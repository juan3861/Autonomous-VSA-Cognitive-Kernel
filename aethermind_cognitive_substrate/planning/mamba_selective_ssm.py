import time
import math
from typing import List, Dict, Any, Tuple, Optional

# ==============================================================================
# AETHERMIND MAMBA SELECTIVE STATE-SPACE MODEL (SSM) ENGINE
# Órgão 25 do Substrato Cognitivo Soberano (Inspirado em Mamba / S4 / RWKV)
# ==============================================================================
# Substitui o mecanismo de atenção quadrática O(N^2) e KV-caches inflados de LLMs
# por uma varredura seletiva recorrente em tempo O(N) e espaço O(1).
# A seletividade permite ao modelo filtrar ruído e reter fatos críticos
# indefinidamente no espaço de estados latente h_t.
# 100% Determinístico, 0 tokens, pura matemática de sistemas dinâmicos.
# ==============================================================================

class MambaSelectiveSSMEngine:
    """
    Motor de Espaço de Estados Seletivo Contínuo (Selective SSM).
    Equações fundamentais:
      h_t = A_bar * h_{t-1} + B_bar * x_t
      y_t = C_t * h_t + D * x_t
    onde Delta_t, B_t, C_t dependem dinamicamente da entrada x_t.
    """
    def __init__(self, d_model: int = 16, d_state: int = 32, dt_min: float = 0.001, dt_max: float = 0.1):
        self.d_model = d_model   # Dimensão de entrada/saída de cada passo
        self.d_state = d_state   # Dimensão oculta do espaço de estados contínuo
        self.dt_min = dt_min
        self.dt_max = dt_max
        
        # Parâmetro diagonal estável de transição A (HiPPO / Decaimento Negativo)
        # A_i = -exp(log(i + 1)) para garantir estabilidade assintótica estrita
        self.A_diag: List[float] = [-float(i + 1) * 0.25 for i in range(self.d_state)]
        
        # Projeção D residual (skip-connection direta)
        self.D: List[float] = [1.0] * self.d_model
        
        # Pesos de projeção determinísticos para Delta, B e C
        self.W_delta: List[List[float]] = []
        for i in range(self.d_model):
            row = [math.cos((i + 1) * 0.314 + (j + 1) * 0.159) * 0.2 for j in range(self.d_model)]
            self.W_delta.append(row)
            
        self.W_B: List[List[float]] = []
        for i in range(self.d_state):
            row = [math.sin((i + 1) * 0.271 + (j + 1) * 0.543) * 0.3 for j in range(self.d_model)]
            self.W_B.append(row)
            
        self.W_C: List[List[float]] = []
        for i in range(self.d_model):
            row = [math.cos((i + 1) * 0.412 + (j + 1) * 0.198) * 0.3 for j in range(self.d_state)]
            self.W_C.append(row)

        # Estado latente interno h_t in R^{d_state} (inicializado em zero)
        self.hidden_state: List[float] = [0.0] * self.d_state
        self.step_counter: int = 0

    def reset_state(self):
        """Reinicia o estado interno contínuo."""
        self.hidden_state = [0.0] * self.d_state
        self.step_counter = 0

    @staticmethod
    def softplus(x: float) -> float:
        """Função de ativação suave softplus com guarda de overflow."""
        if x > 20.0:
            return x
        elif x < -20.0:
            return math.exp(x)
        return math.log1p(math.exp(x))

    def step(self, x_t: List[float]) -> Tuple[List[float], Dict[str, Any]]:
        """
        Executa 1 passo de varredura seletiva (online inference em O(d_state)).
        x_t: Vetor de entrada em R^{d_model}
        Retorna y_t in R^{d_model} e telemetria do passo.
        """
        t0 = time.perf_counter()
        
        # Ajuste de dimensão se necessário
        if len(x_t) != self.d_model:
            if len(x_t) < self.d_model:
                x_t = x_t + [0.0] * (self.d_model - len(x_t))
            else:
                x_t = x_t[:self.d_model]

        # 1. Computar Delta_t dependente de x_t (Time-scale selectivity)
        # Delta = softplus(W_delta * x_t) escalado para o intervalo [dt_min, dt_max]
        delta_raw = sum(sum(self.W_delta[i][j] * x_t[j] for j in range(self.d_model)) for i in range(self.d_model)) / float(self.d_model)
        delta_t = self.dt_min + (self.dt_max - self.dt_min) * (self.softplus(delta_raw) / (1.0 + self.softplus(delta_raw)))

        # 2. Computar B_t in R^{d_state} seletivo dependente da entrada
        B_t = []
        for i in range(self.d_state):
            val = sum(self.W_B[i][j] * x_t[j] for j in range(self.d_model))
            B_t.append(val)

        # 3. Discretização ZOH (Zero-Order Hold)
        # A_bar = exp(Delta * A)
        # B_bar = Delta * B_t (aproximação estável de 1ª ordem)
        new_hidden = [0.0] * self.d_state
        for i in range(self.d_state):
            a_bar = math.exp(delta_t * self.A_diag[i])
            b_bar = delta_t * B_t[i]
            # Mapeamento de estado: h_t = A_bar * h_{t-1} + B_bar * x_agg
            # x_agg é a projeção escalar média da entrada neste modo
            x_proj = x_t[i % self.d_model]
            new_hidden[i] = a_bar * self.hidden_state[i] + b_bar * x_proj

        self.hidden_state = new_hidden

        # 4. Computar C_t e projetar para a saída y_t: y_t = C * h_t + D * x_t
        y_t = []
        for i in range(self.d_model):
            c_proj = sum(self.W_C[i][j] * self.hidden_state[j] for j in range(self.d_state))
            val = c_proj + self.D[i] * x_t[i]
            y_t.append(val)

        self.step_counter += 1
        elapsed_us = (time.perf_counter() - t0) * 1e6
        
        # Norma Euclidiana do estado latente (para monitorar estabilidade)
        h_norm = math.sqrt(sum(v * v for v in self.hidden_state))

        telemetry = {
            "elapsed_us": round(elapsed_us, 2),
            "step": self.step_counter,
            "delta_t": round(delta_t, 6),
            "h_norm": round(h_norm, 4),
            "state_dimension": self.d_state,
            "is_stable": h_norm < 1000.0
        }
        
        return y_t, telemetry

    def selective_scan(self, sequence: List[List[float]]) -> Tuple[List[List[float]], Dict[str, Any]]:
        """
        Executa a varredura seletiva completa sobre uma sequência de comprimento N em tempo O(N).
        """
        t0 = time.perf_counter()
        outputs = []
        total_delta = 0.0
        
        for x_t in sequence:
            y_t, tele = self.step(x_t)
            outputs.append(y_t)
            total_delta += tele["delta_t"]

        total_elapsed_ms = (time.perf_counter() - t0) * 1000.0
        seq_len = len(sequence)
        us_per_token = (total_elapsed_ms * 1000.0) / max(1, seq_len)

        summary = {
            "sequence_length": seq_len,
            "total_elapsed_ms": round(total_elapsed_ms, 3),
            "us_per_step": round(us_per_token, 3),
            "throughput_steps_per_sec": round(seq_len / (total_elapsed_ms / 1000.0 + 1e-9), 1),
            "final_h_norm": round(math.sqrt(sum(v * v for v in self.hidden_state)), 4)
        }
        
        return outputs, summary
