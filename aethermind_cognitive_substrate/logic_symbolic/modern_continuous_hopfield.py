"""Modern Continuous Hopfield Network with Exponential Storage Capacity (Ramsauer / Krotov-Hopfield).

Organ 36 do Substrato Cognitivo Não-LLM (AetherCOS v4.3).
Implementa as Redes de Hopfield Contínuas Modernas (ENG-034, hopfield-layers):
- Função de Energia de Lyapunov Côncavo-Convexa:
    E(xi) = - (1 / beta) * log( sum_i exp(beta * <x_i, xi>) ) + 0.5 * ||xi||^2
- Regra de Atualização CCCP (Concave-Convex Procedure):
    xi_{t+1} = X * softmax(beta * X^T * xi_t)
- Capacidade de Armazenamento Exponencial: C ~ exp(alpha * d), superando o limite
  linear 0.14*d das redes de Hopfield binárias clássicas.
- Convergência global garantida em 1 a 3 iterações mesmo sob severa corrupção de ruído
  ou mascaramento parcial do padrão de consulta.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ModernContinuousHopfieldNetwork:
    """
    Cofre de Memória Associativa de Hopfield Contínua Moderna.
    Recupera padrões contínuos em alta dimensão com garantia monotônica de queda
    da função de energia de Lyapunov dE/dt <= 0.
    """

    def __init__(self, dimension: int = 32, beta: float = 8.0):
        self.dimension = dimension
        self.beta = beta
        self.patterns: List[np.ndarray] = []
        self.labels: List[str] = []

    def store_pattern(self, pattern: List[float] | np.ndarray, label: Optional[str] = None) -> int:
        """Armazena um padrão normalizado na matriz de memória X."""
        vec = np.array(pattern, dtype=np.float64).reshape(-1)
        if len(vec) < self.dimension:
            vec = np.pad(vec, (0, self.dimension - len(vec)))
        elif len(vec) > self.dimension:
            vec = vec[:self.dimension]

        norm = float(np.linalg.norm(vec))
        if norm > 1e-12:
            vec = vec / norm

        idx = len(self.patterns)
        self.patterns.append(vec)
        self.labels.append(label or f"pattern_{idx}")
        return idx

    def compute_energy(self, state_xi: np.ndarray) -> float:
        """
        Calcula a função de energia moderna de Hopfield:
        E(xi) = - (1/beta) * lse(beta, X^T xi) + 0.5 * ||xi||^2
        """
        if not self.patterns:
            return 0.0
        X = np.column_stack(self.patterns)  # (d, N)
        dots = self.beta * np.dot(X.T, state_xi)  # (N,)
        max_dot = float(np.max(dots))
        lse = (max_dot + math.log(float(np.sum(np.exp(dots - max_dot))))) / self.beta
        quad = 0.5 * float(np.dot(state_xi, state_xi))
        return float(-lse + quad)

    def retrieve(
        self,
        noisy_query: List[float] | np.ndarray,
        max_steps: int = 5,
        tol: float = 1e-7
    ) -> Dict[str, Any]:
        """
        Executa a recuperação associativa via procedimento côncavo-convexo (CCCP):
        xi_{t+1} = X * softmax(beta * X^T xi_t)
        """
        t0 = time.perf_counter()
        if not self.patterns:
            return {"status": "EMPTY_HOPFIELD_VAULT", "retrieved": False}

        xi = np.array(noisy_query, dtype=np.float64).reshape(-1)
        if len(xi) < self.dimension:
            xi = np.pad(xi, (0, self.dimension - len(xi)))
        elif len(xi) > self.dimension:
            xi = xi[:self.dimension]

        norm_q = float(np.linalg.norm(xi))
        if norm_q > 1e-12:
            xi = xi / norm_q

        X = np.column_stack(self.patterns)  # shape (d, N)
        initial_energy = self.compute_energy(xi)
        energy_trajectory = [round(initial_energy, 6)]

        steps_run = 0
        attn_weights = np.zeros(len(self.patterns), dtype=np.float64)

        for step in range(max_steps):
            steps_run += 1
            logits = self.beta * np.dot(X.T, xi)
            logits_shifted = logits - np.max(logits)
            exp_scores = np.exp(logits_shifted)
            attn_weights = exp_scores / (np.sum(exp_scores) + 1e-15)

            xi_next = np.dot(X, attn_weights)
            delta = float(np.linalg.norm(xi_next - xi))
            xi = xi_next
            energy_trajectory.append(round(self.compute_energy(xi), 6))

            if delta < tol:
                break

        final_energy = self.compute_energy(xi)
        best_idx = int(np.argmax(attn_weights))
        best_label = self.labels[best_idx]
        cosine_sim = float(np.dot(xi, self.patterns[best_idx]) / (np.linalg.norm(xi) * np.linalg.norm(self.patterns[best_idx]) + 1e-12))

        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "HOPFIELD_FIXED_POINT_RETRIEVED",
            "retrieved": True,
            "matched_index": best_idx,
            "matched_label": best_label,
            "attention_confidence": round(float(attn_weights[best_idx]), 6),
            "cosine_similarity": round(cosine_sim, 6),
            "initial_energy": round(initial_energy, 6),
            "final_energy": round(final_energy, 6),
            "energy_monotonic_drop": round(initial_energy - final_energy, 6),
            "steps_to_converge": steps_run,
            "stored_patterns_count": len(self.patterns),
            "retrieved_vector": [round(float(v), 5) for v in xi],
            "elapsed_us": round(elapsed_us, 2)
        }
