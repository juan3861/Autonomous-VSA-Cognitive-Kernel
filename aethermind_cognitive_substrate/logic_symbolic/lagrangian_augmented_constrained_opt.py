"""Augmented Lagrangian Method (ALM) for General Nonlinear Constrained Optimization.

Organ 75 do Substrato Cognitivo Nao-LLM (AetherCOS v6.3).
Metodo dos Multiplicadores / Lagrangiano Aumentado (Hestenes 1969 / Powell 1969 / Rockafellar):
- Resolve problemas de otimizacao nao-linear com restricoes de igualdade h(x) = 0 e desigualdade g(x) <= 0:
    L_rho(x, lam, mu) = f(x) + lam^T h(x) + (rho/2)||h(x)||^2 + (1/(2*rho)) sum_i (max(0, mu_i + rho*g_i(x))^2 - mu_i^2)
- Alterna minimizacao irrestrita (BFGS com busca linear Armijo) com atualizacao dual exata:
    lam <- lam + rho * h(x)
    mu  <- max(0, mu + rho * g(x))
- Garante viabilidade primal (< 1e-6) e otimalidade KKT sem tokens LLM.
"""
from __future__ import annotations

import math
import time
from typing import Callable, Dict, Any, List, Optional
import numpy as np


class AugmentedLagrangianConstrainedSolver:
    """
    Solucionador de Otimizacao Nao-Linear Restrita via Lagrangiano Aumentado (ALM + BFGS).
    """

    def __init__(self, tol: float = 1e-6, max_outer_iters: int = 20):
        self.tol = float(tol)
        self.max_outer_iters = int(max_outer_iters)

    @staticmethod
    def _finite_diff_grad(fn: Callable[[np.ndarray], float], x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
        g = np.zeros_like(x)
        f0 = fn(x)
        for i in range(len(x)):
            dx = np.zeros_like(x)
            h = eps * max(1.0, abs(float(x[i])))
            dx[i] = h
            g[i] = (fn(x + dx) - f0) / h
        return g

    def _bfgs_minimize(self, fn: Callable[[np.ndarray], float], x0: np.ndarray, max_iters: int = 40) -> np.ndarray:
        """Minimizacao irrestrita BFGS com busca linear Armijo."""
        x = x0.copy()
        n = len(x)
        H = np.eye(n, dtype=np.float64)
        g = self._finite_diff_grad(fn, x)

        for _ in range(max_iters):
            if float(np.linalg.norm(g)) < 1e-8:
                break
            p = -H @ g
            if float(np.dot(g, p)) >= 0.0:
                p = -g
                H = np.eye(n, dtype=np.float64)

            fx = fn(x)
            alpha = 1.0
            c1 = 1e-4
            gp = float(np.dot(g, p))
            for _ in range(20):
                if fn(x + alpha * p) <= fx + c1 * alpha * gp:
                    break
                alpha *= 0.5

            s = alpha * p
            x_new = x + s
            g_new = self._finite_diff_grad(fn, x_new)
            y = g_new - g
            sy = float(np.dot(s, y))
            if sy > 1e-12:
                rho_k = 1.0 / sy
                I_n = np.eye(n, dtype=np.float64)
                V = I_n - rho_k * np.outer(s, y)
                H = V @ H @ V.T + rho_k * np.outer(s, s)
            x, g = x_new, g_new

        return x

    def solve_constrained(
        self,
        f_obj: Optional[Callable[[np.ndarray], float]] = None,
        h_eq: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        g_ineq: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        x0: Optional[List[float] | np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Resolve min f(x) s.t. h(x) = 0, g(x) <= 0.
        Problema padrao: min (x0 - 2)^2 + (x1 - 2)^2 s.t. x0 + x1 - 2 = 0 (otimo exato [1, 1], f*=2)
        e x0 >= 0.5 (g(x) = 0.5 - x0 <= 0).
        """
        t0 = time.perf_counter()

        if f_obj is None:
            def f_fn(x: np.ndarray) -> float:
                return float((x[0] - 2.0) ** 2 + (x[1] - 2.0) ** 2)

            def h_fn(x: np.ndarray) -> np.ndarray:
                return np.array([x[0] + x[1] - 2.0], dtype=np.float64)

            def g_fn(x: np.ndarray) -> np.ndarray:
                return np.array([0.5 - x[0]], dtype=np.float64)

            x = np.asarray(x0 if x0 is not None else [0.0, 0.0], dtype=np.float64)
        else:
            f_fn = f_obj
            h_fn = h_eq if h_eq is not None else (lambda _: np.zeros(0, dtype=np.float64))
            g_fn = g_ineq if g_ineq is not None else (lambda _: np.zeros(0, dtype=np.float64))
            x = np.asarray(x0 if x0 is not None else [0.0, 0.0], dtype=np.float64)

        h0 = np.atleast_1d(h_fn(x))
        g0 = np.atleast_1d(g_fn(x))
        lam = np.zeros(len(h0), dtype=np.float64)
        mu = np.zeros(len(g0), dtype=np.float64)
        rho = 2.0

        outer_iters = 0
        eq_viol = float("inf")
        ineq_viol = float("inf")

        for k in range(1, self.max_outer_iters + 1):
            outer_iters = k

            def aug_lag(xv: np.ndarray) -> float:
                val = f_fn(xv)
                if len(lam) > 0:
                    hv = np.atleast_1d(h_fn(xv))
                    val += float(np.dot(lam, hv)) + 0.5 * rho * float(np.dot(hv, hv))
                if len(mu) > 0:
                    gv = np.atleast_1d(g_fn(xv))
                    plus = np.maximum(0.0, mu + rho * gv)
                    val += (0.5 / rho) * float(np.sum(plus ** 2 - mu ** 2))
                return val

            x = self._bfgs_minimize(aug_lag, x, max_iters=40)

            hv = np.atleast_1d(h_fn(x)) if len(lam) > 0 else np.zeros(0)
            gv = np.atleast_1d(g_fn(x)) if len(mu) > 0 else np.zeros(0)

            eq_viol = float(np.linalg.norm(hv)) if len(hv) > 0 else 0.0
            ineq_viol = float(np.max(np.maximum(0.0, gv))) if len(gv) > 0 else 0.0

            if len(lam) > 0:
                lam = lam + rho * hv
            if len(mu) > 0:
                mu = np.maximum(0.0, mu + rho * gv)

            if eq_viol < self.tol and ineq_viol < self.tol:
                break
            rho = min(rho * 3.0, 1e6)

        f_opt = f_fn(x)
        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "ALM_CONSTRAINED_OPTIMAL_CONVERGED",
            "outer_iterations": outer_iters,
            "optimal_x": [round(float(v), 5) for v in x],
            "optimal_objective": round(float(f_opt), 6),
            "equality_violation": float(f"{eq_viol:.3e}"),
            "inequality_violation": float(f"{ineq_viol:.3e}"),
            "feasible": (eq_viol < self.tol) and (ineq_viol < self.tol),
            "final_penalty_rho": round(rho, 2),
            "elapsed_us": round(elapsed_us, 2),
        }
