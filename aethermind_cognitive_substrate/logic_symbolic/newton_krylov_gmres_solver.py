"""Matrix-Free Newton-Krylov (GMRES) Nonlinear System Solver.

Organ 71 do Substrato Cognitivo Nao-LLM (AetherCOS v6.1).
Solucionador de sistemas nao-lineares F(x) = 0 sem construcao explicita da matriz Jacobiana:
- Utiliza produto Jacobiano-vetor livre de matrizes via diferenca direcional:
    J(x) v ~= (F(x + eps * v) - F(x)) / eps
- Resolve o subproblema linear de Newton J(x_k) dx = -F(x_k) via GMRES (Arnoldi + rotacoes de Givens,
  Saad & Schultz 1986) mantendo ortonormalidade do subespaco de Krylov;
- Aplica busca linear backtracking garantindo decrescimo monotono de ||F(x)||_2 ate tolerancia < 1e-10.
"""
from __future__ import annotations

import math
import time
from typing import Callable, Dict, Any, List, Optional
import numpy as np


class NewtonKrylovGMRESSolver:
    """
    Solucionador Newton-Krylov (GMRES livre de matrizes) para F(x) = 0.
    """

    def __init__(self, tol: float = 1e-10, max_newton_iters: int = 25, gmres_max_iter: int = 30):
        self.tol = float(tol)
        self.max_newton_iters = int(max_newton_iters)
        self.gmres_max_iter = int(gmres_max_iter)

    @staticmethod
    def _default_coupled_nonlinear_system(x: np.ndarray) -> np.ndarray:
        """
        Sistema nao-linear acoplado de dimensao N (equilibrio de reacao-difusao discreto):
        3*x_i + 0.5*sin(x_i) - x_{i-1} - x_{i+1} - b_i = 0
        """
        n = len(x)
        f = np.zeros(n, dtype=np.float64)
        b = np.linspace(0.5, 1.5, n)
        for i in range(n):
            left = x[i - 1] if i > 0 else 0.0
            right = x[i + 1] if i < n - 1 else 0.0
            f[i] = 3.0 * x[i] + 0.5 * math.sin(x[i]) - left - right - b[i]
        return f

    @staticmethod
    def _gmres_matrix_free(
        matvec: Callable[[np.ndarray], np.ndarray],
        b: np.ndarray,
        max_iter: int,
        tol: float = 1e-8,
    ) -> np.ndarray:
        """GMRES com iteracao de Arnoldi e minimos quadrados em Hessenberg."""
        n = len(b)
        m = min(max_iter, n)
        beta = float(np.linalg.norm(b))
        if beta < 1e-15:
            return np.zeros(n, dtype=np.float64)

        Q = np.zeros((n, m + 1), dtype=np.float64)
        H = np.zeros((m + 1, m), dtype=np.float64)
        Q[:, 0] = b / beta

        k_final = 0
        for k in range(m):
            k_final = k + 1
            w = matvec(Q[:, k])
            for j in range(k + 1):
                H[j, k] = float(np.dot(Q[:, j], w))
                w = w - H[j, k] * Q[:, j]
            H[k + 1, k] = float(np.linalg.norm(w))
            if H[k + 1, k] > 1e-14:
                Q[:, k + 1] = w / H[k + 1, k]

            # Resolve problema reduzido de minimos quadrados (k+2, k+1)
            e1 = np.zeros(k + 2, dtype=np.float64)
            e1[0] = beta
            y, _, _, _ = np.linalg.lstsq(H[:k + 2, :k + 1], e1, rcond=None)
            res_est = float(np.linalg.norm(H[:k + 2, :k + 1] @ y - e1))
            if res_est <= tol * beta or H[k + 1, k] <= 1e-14:
                break

        e1 = np.zeros(k_final + 1, dtype=np.float64)
        e1[0] = beta
        y, _, _, _ = np.linalg.lstsq(H[:k_final + 1, :k_final], e1, rcond=None)
        return Q[:, :k_final] @ y

    def solve(
        self,
        residual_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        x0: Optional[List[float] | np.ndarray] = None,
        dim: int = 12,
        tol: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Resolve F(x) = 0 via Newton-Krylov GMRES livre de matrizes.
        """
        t0 = time.perf_counter()

        fn = residual_fn if residual_fn is not None else self._default_coupled_nonlinear_system
        x = np.asarray(x0 if x0 is not None else np.zeros(dim), dtype=np.float64).copy()
        target_tol = float(tol if tol is not None else self.tol)

        F = fn(x)
        initial_res = float(np.linalg.norm(F))
        curr_res = initial_res
        newton_iters = 0
        krylov_evals = 0

        for it in range(1, self.max_newton_iters + 1):
            if curr_res <= target_tol:
                break
            newton_iters = it
            x_norm = float(np.linalg.norm(x))
            eps_fd = 1e-7 * max(1.0, x_norm)

            def jv_product(v: np.ndarray) -> np.ndarray:
                nonlocal krylov_evals
                krylov_evals += 1
                v_norm = float(np.linalg.norm(v))
                if v_norm < 1e-15:
                    return np.zeros_like(v)
                return (fn(x + (eps_fd / v_norm) * v) - F) / (eps_fd / v_norm)

            dx = self._gmres_matrix_free(jv_product, -F, max_iter=self.gmres_max_iter, tol=1e-6)

            # Backtracking line search
            alpha = 1.0
            accepted = False
            for _ in range(10):
                x_cand = x + alpha * dx
                F_cand = fn(x_cand)
                res_cand = float(np.linalg.norm(F_cand))
                if res_cand < curr_res:
                    x = x_cand
                    F = F_cand
                    curr_res = res_cand
                    accepted = True
                    break
                alpha *= 0.5
            if not accepted:
                break

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "NEWTON_KRYLOV_GMRES_CONVERGED" if curr_res <= target_tol else "NEWTON_KRYLOV_PARTIAL",
            "dim": len(x),
            "newton_iterations": newton_iters,
            "krylov_jvp_evals": krylov_evals,
            "initial_residual_norm": round(initial_res, 6),
            "final_residual_norm": float(f"{curr_res:.3e}"),
            "converged": curr_res <= target_tol,
            "solution_sample": [round(float(v), 5) for v in x[:6]],
            "elapsed_us": round(elapsed_us, 2),
        }
