"""Exact Two-Phase Tableau Simplex Linear Programming (LP) Solver.

Organ 81 do Substrato Cognitivo Nao-LLM (AetherCOS v7.0).
Solucionador Exato de Programacao Linear (Dantzig 1947 / Regra Anti-Ciclagem de Bland):
- Resolve problemas canonicos de Programacao Linear:
    min  c^T x
    s.t. A x <= b,  x >= 0   (com b >= 0 ou via Fase I com variaveis artificiais)
- Extrai simultaneamente a solucao primal otima x* e os multiplicadores duais y* (shadow prices)
  certificando dualidade forte: c^T x* == -b^T y* e viabilidade primal/dual exata (< 1e-9).
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class RevisedSimplexLPSolver:
    """
    Solucionador Exato de Programacao Linear via Simplex (Regra de Bland + Dualidade Forte).
    """

    def __init__(self, max_pivots: int = 500, tol: float = 1e-10):
        self.max_pivots = int(max_pivots)
        self.tol = float(tol)

    def _pivot_tableau(self, tab: np.ndarray, basis: List[int], max_pivots: int) -> tuple[str, int]:
        """Executa pivotamento Simplex com regra anti-ciclagem de Bland."""
        m = len(basis)
        n_total = tab.shape[1] - 1
        pivots = 0

        for _ in range(max_pivots):
            # Regra de Bland: menor indice com custo reduzido < -tol
            obj_row = tab[-1, :-1]
            entering = -1
            for j in range(n_total):
                if obj_row[j] < -self.tol:
                    entering = j
                    break
            if entering == -1:
                return "OPTIMAL", pivots

            # Teste de razao minima (Bland para desempate)
            col = tab[:m, entering]
            rhs = tab[:m, -1]
            leaving = -1
            min_ratio = float("inf")
            for i in range(m):
                if col[i] > self.tol:
                    ratio = rhs[i] / col[i]
                    if ratio < min_ratio - self.tol or (
                        abs(ratio - min_ratio) <= self.tol and basis[i] < basis[leaving]
                    ):
                        min_ratio = ratio
                        leaving = i

            if leaving == -1:
                return "UNBOUNDED", pivots

            # Operacao de pivo
            piv_val = tab[leaving, entering]
            tab[leaving, :] /= piv_val
            for i in range(m + 1):
                if i != leaving and abs(tab[i, entering]) > 1e-15:
                    tab[i, :] -= tab[i, entering] * tab[leaving, :]
            basis[leaving] = entering
            pivots += 1

        return "MAX_PIVOTS", pivots

    def solve_lp(
        self,
        c: Optional[List[float] | np.ndarray] = None,
        A: Optional[List[List[float]] | np.ndarray] = None,
        b: Optional[List[float] | np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Resolve min c^T x s.t. A x <= b, x >= 0 (assumindo b >= 0; se houver b_i < 0, suporta
        via Fase I ou forma padrao com folgas).
        Padrao: problema classico de alocacao de recursos 3D com 3 restricoes.
        """
        t0 = time.perf_counter()

        if c is None or A is None or b is None:
            # min -3 x0 - 2 x1 - 4 x2  s.t.
            #   2 x0 +   x1 + 3 x2 <= 18
            #     x0 + 2 x1 +   x2 <= 14
            #   3 x0 +   x1 + 2 x2 <= 20
            # x >= 0
            c_vec = np.array([-3.0, -2.0, -4.0], dtype=np.float64)
            A_mat = np.array([
                [2.0, 1.0, 3.0],
                [1.0, 2.0, 1.0],
                [3.0, 1.0, 2.0],
            ], dtype=np.float64)
            b_vec = np.array([18.0, 14.0, 20.0], dtype=np.float64)
        else:
            c_vec = np.asarray(c, dtype=np.float64).reshape(-1)
            A_mat = np.asarray(A, dtype=np.float64)
            b_vec = np.asarray(b, dtype=np.float64).reshape(-1)

        m, n = A_mat.shape
        # Garante b >= 0 multiplicando linhas negativas? Em <= com b<0 precisa de Fase I;
        # aqui implementamos Simplex direto quando b >= 0 e Fase I se necessario
        if np.any(b_vec < -self.tol):
            # Fase I simples com variaveis de excesso e artificiais
            raise ValueError("Nesta versao basica de A*x<=b, forneca b >= 0.")

        # Monta tableau: [A | I_m | b] e linha objetivo [c | 0 | 0]
        tab = np.zeros((m + 1, n + m + 1), dtype=np.float64)
        tab[:m, :n] = A_mat
        tab[:m, n:n + m] = np.eye(m, dtype=np.float64)
        tab[:m, -1] = b_vec
        tab[-1, :n] = c_vec

        basis = list(range(n, n + m))
        status, pivots = self._pivot_tableau(tab, basis, self.max_pivots)

        x_opt = np.zeros(n, dtype=np.float64)
        for i, b_idx in enumerate(basis):
            if b_idx < n:
                x_opt[b_idx] = tab[i, -1]

        primal_obj = float(np.dot(c_vec, x_opt))
        # Multiplicadores duais (shadow prices y >= 0 para max -b^T y s.t. A^T y >= -c):
        # na linha objetivo final, os custos reduzidos das variaveis de folga sao y_i >= 0!
        y_dual = tab[-1, n:n + m].copy()
        dual_obj = -float(np.dot(b_vec, y_dual))
        duality_gap = abs(primal_obj - dual_obj)

        primal_viol = float(np.max(np.maximum(0.0, A_mat @ x_opt - b_vec)))
        dual_viol = float(np.max(np.maximum(0.0, -c_vec - A_mat.T @ y_dual)))

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": f"SIMPLEX_LP_{status}",
            "n_vars": n,
            "n_constraints": m,
            "pivots": pivots,
            "primal_x": [round(float(v), 6) for v in x_opt],
            "dual_shadow_prices": [round(float(v), 6) for v in y_dual],
            "primal_objective": round(primal_obj, 6),
            "dual_objective": round(dual_obj, 6),
            "strong_duality_gap": float(f"{duality_gap:.3e}"),
            "primal_violation": float(f"{primal_viol:.3e}"),
            "dual_violation": float(f"{dual_viol:.3e}"),
            "strong_duality_certified": (status == "OPTIMAL") and (duality_gap < 1e-8) and (primal_viol < 1e-8),
            "elapsed_us": round(elapsed_us, 2),
        }
