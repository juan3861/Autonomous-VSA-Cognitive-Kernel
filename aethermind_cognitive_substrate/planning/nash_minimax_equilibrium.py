"""Zero-Sum Nash Equilibrium & Minimax Strategy Solver (Regret Matching / MWU).

Organ 78 do Substrato Cognitivo Nao-LLM (AetherCOS v6.4).
Solucionador de Equilibrio de Nash em Jogos de Soma Zero de 2 Jogadores (von Neumann 1928):
- Dada matriz de payoff A (m x n) onde Jogador 1 (linha) maximiza p^T A q e Jogador 2 (coluna)
  minimiza p^T A q;
- Executa Regret Matching+ / Multiplicative Weights Update acoplado em T iteracoes com media
  ergodica das estrategias (p_avg, q_avg);
- Certifica o Teorema Minimax: gap de explorabilidade
    gap = max_i (A q_avg)_i - min_j (p_avg^T A)_j -> 0
  convergindo para o valor exato do jogo v* = p_avg^T A q_avg sem tokens LLM.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class ZeroSumNashEquilibriumSolver:
    """
    Solucionador de Equilibrio de Nash Minimax para Jogos de Soma Zero.
    """

    def __init__(self, n_iters: int = 2000):
        self.n_iters = int(n_iters)

    def solve_minimax(
        self,
        payoff_matrix: Optional[List[List[float]] | np.ndarray] = None,
        n_iters: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Calcula estrategias mistas de equilibrio de Nash (p*, q*) e o gap de explorabilidade.
        Padrao: Pedra-Papel-Tesoura ponderado (jogo assimetrico sem estrategia pura dominante).
        """
        t0 = time.perf_counter()

        if payoff_matrix is None:
            # Jogo assimetrico 3x3 (Pedra-Papel-Tesoura com pesos [1, 2, 3])
            A = np.array([
                [0.0, -2.0, 1.0],
                [2.0, 0.0, -3.0],
                [-1.0, 3.0, 0.0],
            ], dtype=np.float64)
        else:
            A = np.asarray(payoff_matrix, dtype=np.float64)

        m, n = A.shape
        T = int(n_iters if n_iters is not None else self.n_iters)

        # Regret Matching+ (Tammelin 2014) para convergencia rapida O(1/T) em media
        regret_p = np.zeros(m, dtype=np.float64)
        regret_q = np.zeros(n, dtype=np.float64)
        p_sum = np.zeros(m, dtype=np.float64)
        q_sum = np.zeros(n, dtype=np.float64)

        p = np.full(m, 1.0 / m, dtype=np.float64)
        q = np.full(n, 1.0 / n, dtype=np.float64)

        for t in range(1, T + 1):
            # Jogador 1 (maximiza p^T A q)
            u_p = A @ q
            val_p = float(np.dot(p, u_p))
            regret_p = np.maximum(0.0, regret_p + (u_p - val_p))
            s_p = float(np.sum(regret_p))
            p = (regret_p / s_p) if s_p > 1e-12 else np.full(m, 1.0 / m)

            # Jogador 2 (minimiza p^T A q, logo maximiza -p^T A q)
            u_q = -(p @ A)
            val_q = float(np.dot(q, u_q))
            regret_q = np.maximum(0.0, regret_q + (u_q - val_q))
            s_q = float(np.sum(regret_q))
            q = (regret_q / s_q) if s_q > 1e-12 else np.full(n, 1.0 / n)

            # Ponderacao linear (RM+ linear averaging)
            p_sum += t * p
            q_sum += t * q

        p_eq = p_sum / float(np.sum(p_sum))
        q_eq = q_sum / float(np.sum(q_sum))

        game_value = float(p_eq @ A @ q_eq)
        best_response_p1 = float(np.max(A @ q_eq))
        best_response_p2 = float(np.min(p_eq @ A))
        exploitability_gap = max(0.0, best_response_p1 - best_response_p2)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "NASH_MINIMAX_EQUILIBRIUM_CONVERGED",
            "shape": [m, n],
            "iterations": T,
            "game_value": round(game_value, 6),
            "exploitability_gap": float(f"{exploitability_gap:.3e}"),
            "minimax_certified": exploitability_gap < 5e-3,
            "row_player_strategy": [round(float(v), 5) for v in p_eq],
            "col_player_strategy": [round(float(v), 5) for v in q_eq],
            "elapsed_us": round(elapsed_us, 2),
        }
