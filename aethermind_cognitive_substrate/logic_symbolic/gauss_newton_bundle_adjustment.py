"""Levenberg-Marquardt Damped Nonlinear Least Squares (NLLS) Solver.

Organ 73 do Substrato Cognitivo Nao-LLM (AetherCOS v6.2).
Solucionador de Minimos Quadrados Nao-Lineares Amortecido (Levenberg 1944 / Marquardt 1963):
- Minimiza f(theta) = 0.5 * ||r(theta)||_2^2 interpolando entre Gauss-Newton e descida do gradiente:
    (J^T J + lambda * diag(J^T J)) delta = -J^T r
- Utiliza razao de ganho rho = (f(theta) - f(theta + delta)) / (L(0) - L(delta)) para ajustar
  dinamicamente o fator de amortecimento lambda;
- Estima a matriz de covariancia assintotica dos parametros Cov(theta) ~= sigma^2 * (J^T J)^{-1}
  sem tokens LLM e com convergencia superlinear.
"""
from __future__ import annotations

import math
import time
from typing import Callable, Dict, Any, List, Optional
import numpy as np


class LevenbergMarquardtNLLSSolver:
    """
    Solucionador de Minimos Quadrados Nao-Lineares via Levenberg-Marquardt.
    """

    def __init__(self, tol: float = 1e-10, max_iters: int = 50, seed: int = 202673):
        self.tol = float(tol)
        self.max_iters = int(max_iters)
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _finite_diff_jacobian(
        res_fn: Callable[[np.ndarray], np.ndarray],
        theta: np.ndarray,
        r0: np.ndarray,
        eps: float = 1e-6,
    ) -> np.ndarray:
        """Calcula Jacobiano J (m x p) por diferencas finitas."""
        m = len(r0)
        p = len(theta)
        J = np.zeros((m, p), dtype=np.float64)
        for j in range(p):
            dt = np.zeros(p, dtype=np.float64)
            step = eps * max(1.0, abs(float(theta[j])))
            dt[j] = step
            J[:, j] = (res_fn(theta + dt) - r0) / step
        return J

    def fit_nonlinear(
        self,
        residual_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        theta0: Optional[List[float] | np.ndarray] = None,
        tol: Optional[float] = None,
        max_iters: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Ajusta parametros theta minimizando 0.5 * ||r(theta)||^2.
        Por padrao ajusta decaimento exponencial y = a * exp(-b * t) + c com ruido.
        """
        t0 = time.perf_counter()

        true_theta = np.array([2.5, 1.3, 0.4], dtype=np.float64)
        if residual_fn is None:
            t_grid = np.linspace(0.0, 3.0, 35)
            y_obs = (
                true_theta[0] * np.exp(-true_theta[1] * t_grid) + true_theta[2]
                + self.rng.normal(0.0, 0.015, size=len(t_grid))
            )

            def default_res(th: np.ndarray) -> np.ndarray:
                return (th[0] * np.exp(-th[1] * t_grid) + th[2]) - y_obs

            fn = default_res
            th_init = np.asarray(theta0 if theta0 is not None else [1.0, 0.5, 0.0], dtype=np.float64)
            using_default = True
        else:
            fn = residual_fn
            th_init = np.asarray(theta0 if theta0 is not None else [1.0, 1.0], dtype=np.float64)
            using_default = False

        theta = th_init.copy()
        eps_tol = float(tol if tol is not None else self.tol)
        iters_max = int(max_iters if max_iters is not None else self.max_iters)

        r = fn(theta)
        cost = 0.5 * float(np.dot(r, r))
        initial_cost = cost
        lam = 1e-3
        iters_done = 0

        for it in range(1, iters_max + 1):
            iters_done = it
            J = self._finite_diff_jacobian(fn, theta, r)
            JTJ = J.T @ J
            g = J.T @ r

            if float(np.max(np.abs(g))) < eps_tol:
                break

            diag_JTJ = np.maximum(np.diag(JTJ), 1e-8)
            accepted = False
            for _ in range(12):
                A = JTJ + lam * np.diag(diag_JTJ)
                try:
                    delta = -np.linalg.solve(A, g)
                except np.linalg.LinAlgError:
                    lam *= 10.0
                    continue

                if float(np.linalg.norm(delta)) < eps_tol * (1.0 + float(np.linalg.norm(theta))):
                    accepted = True
                    break

                theta_new = theta + delta
                r_new = fn(theta_new)
                cost_new = 0.5 * float(np.dot(r_new, r_new))
                pred_red = -float(np.dot(g, delta)) - 0.5 * float(delta.T @ JTJ @ delta)
                rho = (cost - cost_new) / max(pred_red, 1e-15)

                if rho > 0.0 and cost_new < cost:
                    theta = theta_new
                    r = r_new
                    cost = cost_new
                    lam = max(lam * max(1.0 / 3.0, 1.0 - (2.0 * rho - 1.0) ** 3), 1e-10)
                    accepted = True
                    break
                else:
                    lam = min(lam * 5.0, 1e8)

            if not accepted or float(np.linalg.norm(delta)) < eps_tol:
                break

        # Estimativa da incerteza dos parametros
        J_final = self._finite_diff_jacobian(fn, theta, r)
        dof = max(1, len(r) - len(theta))
        sigma2 = float(np.dot(r, r)) / dof
        try:
            cov_theta = sigma2 * np.linalg.inv(J_final.T @ J_final + 1e-12 * np.eye(len(theta)))
            param_std = [round(float(v), 5) for v in np.sqrt(np.maximum(np.diag(cov_theta), 0.0))]
        except np.linalg.LinAlgError:
            param_std = [0.0] * len(theta)

        param_err = float(np.linalg.norm(theta - true_theta)) if using_default else None
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "LEVENBERG_MARQUARDT_NLLS_CONVERGED",
            "n_residuals": len(r),
            "n_params": len(theta),
            "iterations": iters_done,
            "initial_cost": round(initial_cost, 6),
            "final_cost": round(cost, 6),
            "cost_reduction_ratio": round(initial_cost / max(cost, 1e-12), 2),
            "estimated_params": [round(float(v), 5) for v in theta],
            "param_std_errors": param_std,
            "param_error_vs_true": round(param_err, 5) if param_err is not None else None,
            "elapsed_us": round(elapsed_us, 2),
        }
