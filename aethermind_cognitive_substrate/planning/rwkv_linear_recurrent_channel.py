"""RWKV Multi-Head Linear Attention & Time-Decayed Recurrent Channel (RWKV-LM Inspiration).

Organ 32 do Substrato Cognitivo Não-LLM (AetherCOS v4.2).
Implementa o mecanismo de Atenção Linear Recorrente do RWKV (Receptance Weighted Key Value):
- Complexidade temporal O(N) e espacial O(1) por passo recorrente.
- Interpolação temporal (Time-Mixing): x'_t = mu * x_t + (1 - mu) * x_{t-1}.
- Portões Receptance r = sigmoid(W_r x'_t) como válvulas de leitura atencional.
- Matriz/Vetor de Estado Decaído: S_t = exp(-w) * S_{t-1} + k_t^T v_t.
- Normalização de decaimento estável numericamente (evita overflow/underflow em fluxos infinitos).
- Fusão temporal multicanal complementar ao Mamba SSM para telemetria e fluxos sensoriais.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class RWKVLinearRecurrentChannel:
    """
    Canal de Atenção Linear Recorrente RWKV com Decaimento Temporal Exponencial.
    Opera como órgão de fusão temporal contínua com estado de memória O(1).
    """

    def __init__(
        self,
        d_model: int = 16,
        num_heads: int = 4,
        head_dim: int = 8,
        seed: int = 42
    ):
        self.d_model = d_model
        self.num_heads = num_heads
        self.head_dim = head_dim
        self.total_key_dim = num_heads * head_dim

        rng = np.random.RandomState(seed)

        # Projeções de Receptance, Key, Value e Output
        self.W_r = rng.randn(self.total_key_dim, d_model) * 0.1
        self.W_k = rng.randn(self.total_key_dim, d_model) * 0.1
        self.W_v = rng.randn(self.total_key_dim, d_model) * 0.1
        self.W_out = rng.randn(d_model, self.total_key_dim) * 0.1

        # Parâmetros de Time-Mixing (interpolação entre token atual e anterior)
        self.time_mix_r = rng.uniform(0.1, 0.9, size=d_model)
        self.time_mix_k = rng.uniform(0.1, 0.9, size=d_model)
        self.time_mix_v = rng.uniform(0.1, 0.9, size=d_model)

        # Vetor de Decaimento Exponencial w > 0 por cabeça (garante estabilidade assintótica)
        # taxa de decaimento exp(-w) em (0, 1)
        self.time_decay_w = rng.uniform(0.05, 0.5, size=(num_heads, head_dim))
        # Bônus imediato u
        self.time_first_u = rng.uniform(0.01, 0.2, size=(num_heads, head_dim))

        # Estado Recorrente O(1): S[h] de dimensão (head_dim, head_dim) por cabeça
        self.state_S = np.zeros((num_heads, head_dim, head_dim), dtype=np.float64)
        self.prev_x = np.zeros(d_model, dtype=np.float64)
        self.step_count = 0

    def reset_state(self) -> None:
        """Reinicia o estado interno de memória para zeros."""
        self.state_S.fill(0.0)
        self.prev_x.fill(0.0)
        self.step_count = 0

    def step(self, x_t: List[float] | np.ndarray) -> Tuple[List[float], Dict[str, Any]]:
        """
        Executa um passo recorrente RWKV O(1):
        1. Time-Mixing: interpola x_t com x_{t-1}
        2. Projeta r, k, v
        3. Atualiza estado multi-cabeça S com decaimento exponencial exp(-w)
        4. Calcula wkv = S * k e aplica receptance gating r
        5. Projeta para saída
        """
        t0 = time.perf_counter()
        x = np.array(x_t, dtype=np.float64).reshape(-1)
        if len(x) < self.d_model:
            x = np.pad(x, (0, self.d_model - len(x)))
        elif len(x) > self.d_model:
            x = x[:self.d_model]

        # 1. Time-Mixing
        xr = self.time_mix_r * x + (1.0 - self.time_mix_r) * self.prev_x
        xk = self.time_mix_k * x + (1.0 - self.time_mix_k) * self.prev_x
        xv = self.time_mix_v * x + (1.0 - self.time_mix_v) * self.prev_x
        self.prev_x = x.copy()

        # 2. Projeções Lineares
        r_raw = np.dot(self.W_r, xr)
        k_raw = np.dot(self.W_k, xk)
        v_raw = np.dot(self.W_v, xv)

        # Receptance gate (sigmóide)
        r_gate = 1.0 / (1.0 + np.exp(-np.clip(r_raw, -15.0, 15.0)))

        # Reshape para multi-cabeça: (num_heads, head_dim)
        r_heads = r_gate.reshape(self.num_heads, self.head_dim)
        k_heads = k_raw.reshape(self.num_heads, self.head_dim)
        v_heads = v_raw.reshape(self.num_heads, self.head_dim)

        out_heads = np.zeros((self.num_heads, self.head_dim), dtype=np.float64)

        # 3. Atualização e Leitura Recorrente por Cabeça
        for h in range(self.num_heads):
            decay = np.exp(-self.time_decay_w[h])  # shape (head_dim,)
            u = self.time_first_u[h]               # shape (head_dim,)

            k_h = k_heads[h]  # (head_dim,)
            v_h = v_heads[h]  # (head_dim,)
            r_h = r_heads[h]  # (head_dim,)

            # Leitura com bônus de primeiro passo: wkv = (S_{t-1} + exp(u) * k^T v) * k ...
            # Atenção linear vetor-matriz: out = (S * k_h)
            # Incorpora contribuição do token atual com bônus u:
            # kv outer product
            kv_outer = np.outer(k_h, v_h)
            
            # Saída da cabeça ponderada pelo estado existente + bônus imediato
            wkv = np.dot(k_h, self.state_S[h]) + u * v_h
            
            # Gating de Receptância
            out_heads[h] = r_h * wkv

            # Atualização do Estado com Decaimento Exponencial:
            # S_t = diag(decay) * S_{t-1} + k_h^T v_h
            # Decaimento aplicado ao longo do eixo das chaves
            decay_matrix = decay[:, np.newaxis]
            self.state_S[h] = decay_matrix * self.state_S[h] + kv_outer

        # 4. Projeção de Saída
        flat_heads = out_heads.reshape(-1)
        y = np.dot(self.W_out, flat_heads)

        self.step_count += 1
        elapsed_us = (time.perf_counter() - t0) * 1e6

        state_frobenius_norm = float(np.linalg.norm(self.state_S))
        out_norm = float(np.linalg.norm(y))

        telemetry = {
            "step": self.step_count,
            "d_model": self.d_model,
            "num_heads": self.num_heads,
            "state_frobenius_norm": round(state_frobenius_norm, 4),
            "output_norm": round(out_norm, 4),
            "mean_receptance": round(float(np.mean(r_gate)), 4),
            "elapsed_us": round(elapsed_us, 2)
        }

        return y.tolist(), telemetry

    def sequence_scan(self, sequence: List[List[float]] | np.ndarray) -> Tuple[List[List[float]], Dict[str, Any]]:
        """
        Executa a varredura linear de uma sequência temporal inteira em O(N) tempo e O(1) memória.
        """
        t0 = time.perf_counter()
        seq = np.array(sequence, dtype=np.float64)
        if seq.ndim == 1:
            seq = seq.reshape(1, -1)

        outputs = []
        for x_t in seq:
            out_t, _ = self.step(x_t)
            outputs.append(out_t)

        total_ms = (time.perf_counter() - t0) * 1000.0
        n_steps = len(seq)
        us_per_step = (total_ms * 1000.0) / max(1, n_steps)

        summary = {
            "total_steps": n_steps,
            "total_elapsed_ms": round(total_ms, 3),
            "latency_us_per_step": round(us_per_step, 2),
            "throughput_steps_per_sec": round(n_steps / (total_ms / 1000.0 + 1e-9), 1),
            "final_state_norm": round(float(np.linalg.norm(self.state_S)), 4)
        }

        return outputs, summary
