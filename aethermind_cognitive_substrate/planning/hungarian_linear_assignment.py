"""Hungarian (Kuhn-Munkres) Exact Bipartite Optimal Task Assignment Engine.

Organ 72 do Substrato Cognitivo Nao-LLM (AetherCOS v6.1).
Algoritmo Hungaro exato O(n^3) com potenciais duais (u_i, v_j) para atribuicao otima
multi-agente 1-para-1 (Kuhn 1955 / Jonker-Volgenant):
- Dada matriz de custos C (N agentes x M tarefas), encontra a bijecao pi* que minimiza
  sum_i C[i, pi(i)];
- Mantem potenciais duais (u, v) satisfazendo viabilidade dual u_i + v_j <= C_{ij} e
  folga complementar u_i + v_{pi(i)} = C_{i, pi(i)}, certificando otimalidade global exata;
- Zero tokens LLM, tempo polinomial O(N^3) deterministico.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class HungarianOptimalAssignmentEngine:
    """
    Motor de Atribuicao Bipartida Otima via Algoritmo Hungaro (Kuhn-Munkres O(n^3)).
    """

    def __init__(self, seed: int = 202672):
        self.rng = np.random.default_rng(seed)

    def solve_assignment(
        self,
        cost_matrix: Optional[List[List[float]] | np.ndarray] = None,
        n_agents: int = 6,
    ) -> Dict[str, Any]:
        """
        Resolve o problema de atribuicao linear de custo minimo com prova de otimalidade dual.
        """
        t0 = time.perf_counter()

        if cost_matrix is None:
            N = int(n_agents)
            C = self.rng.uniform(1.0, 20.0, size=(N, N))
            # Cria preferencia diagonal clara + perturbacoes para testar desvio de guloso
            for i in range(N):
                C[i, i] *= 0.4
            C = np.round(C, 3)
        else:
            C = np.asarray(cost_matrix, dtype=np.float64)

        n_rows, n_cols = C.shape
        transposed = False
        if n_rows > n_cols:
            C_work = C.T
            transposed = True
        else:
            C_work = C

        nr, nc = C_work.shape
        # Implementacao canonica O(nr^2 * nc) com potenciais duais u (nr+1) e v (nc+1)
        u = np.zeros(nr + 1, dtype=np.float64)
        v = np.zeros(nc + 1, dtype=np.float64)
        p = np.zeros(nc + 1, dtype=np.int64)
        way = np.zeros(nc + 1, dtype=np.int64)

        for i in range(1, nr + 1):
            p[0] = i
            j0 = 0
            minv = np.full(nc + 1, float("inf"), dtype=np.float64)
            used = np.zeros(nc + 1, dtype=bool)

            while True:
                used[j0] = True
                i0 = p[j0]
                delta = float("inf")
                j1 = 0
                for j in range(1, nc + 1):
                    if not used[j]:
                        cur = C_work[i0 - 1, j - 1] - u[i0] - v[j]
                        if cur < minv[j]:
                            minv[j] = cur
                            way[j] = j0
                        if minv[j] < delta:
                            delta = minv[j]
                            j1 = j

                for j in range(nc + 1):
                    if used[j]:
                        u[p[j]] += delta
                        v[j] -= delta
                    else:
                        minv[j] -= delta

                j0 = j1
                if p[j0] == 0:
                    break

            while True:
                j1 = way[j0]
                p[j0] = p[j1]
                j0 = j1
                if j0 == 0:
                    break

        # Extrai atribuicao
        row_to_col = [-1] * nr
        for j in range(1, nc + 1):
            if p[j] != 0:
                row_to_col[p[j] - 1] = j - 1

        if transposed:
            # Converte para pares (original_row, original_col)
            assignments = [(col, row) for row, col in enumerate(row_to_col) if col >= 0]
            assignments.sort(key=lambda pair: pair[0])
        else:
            assignments = [(row, col) for row, col in enumerate(row_to_col) if col >= 0]

        total_cost = float(sum(C[r, c] for r, c in assignments))

        # Verificacao de otimalidade dual: u[i+1] + v[j+1] <= C_work[i, j]
        # e folga complementar nas arestas escolhidas
        u_vec = u[1:nr + 1][:, None]
        v_vec = v[1:nc + 1][None, :]
        dual_violation = float(np.max(u_vec + v_vec - C_work))
        dual_sum = float(np.sum(u[1:nr + 1]) + np.sum(v[1:nc + 1]))
        # Em problemas retangulares (nr < nc), a soma dos potenciais duais das colunas livres e 0
        duality_gap = abs(total_cost - (-dual_sum if False else sum(u[1:nr + 1]) + sum(v[1:nc + 1])))
        # Nota: na formulacao padrao min, sum(u) + sum(v) == total_cost quando nr == nc ou v_free == 0
        # Checagem exata de folga complementar em cada par atribuido
        slack_err = max(
            abs((u[r + 1] + v[c + 1]) - C_work[r, c])
            for r, c in enumerate(row_to_col) if c >= 0
        )

        # Custo de um guloso ingenuo para comparacao
        greedy_cost = 0.0
        used_c = set()
        for r in range(n_rows):
            avail = [(C[r, c], c) for c in range(n_cols) if c not in used_c]
            if avail:
                best_val, best_c = min(avail)
                greedy_cost += best_val
                used_c.add(best_c)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "HUNGARIAN_OPTIMAL_ASSIGNMENT_FOUND",
            "shape": [n_rows, n_cols],
            "assignments": assignments,
            "optimal_total_cost": round(total_cost, 6),
            "greedy_baseline_cost": round(float(greedy_cost), 6),
            "dual_feasibility_violation": float(f"{max(0.0, dual_violation):.3e}"),
            "complementary_slackness_error": float(f"{slack_err:.3e}"),
            "duality_gap": float(f"{duality_gap:.3e}"),
            "dual_optimality_certified": (dual_violation <= 1e-9) and (slack_err <= 1e-9),
            "elapsed_us": round(elapsed_us, 2),
        }
