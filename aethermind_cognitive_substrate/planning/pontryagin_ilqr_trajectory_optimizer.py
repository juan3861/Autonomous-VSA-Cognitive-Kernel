"""Pontryagin Iterative Linear Quadratic Regulator (iLQR) Trajectory Optimizer.

Organ 64 do Substrato Cognitivo Nao-LLM (AetherCOS v5.7).
Otimizador nao-linear de trajetorias em horizonte finito via Programacao Dinamica Diferencial
de primeira ordem (Li & Todorov, ICINCO 2004 / Tassa et al., 2012):
- Lineariza dinamicas nao-lineares f(x_t, u_t) ao longo da trajetoria nominal via Jacobianos (f_x, f_u);
- Executa passo Backward de Riccati com regularizacao de Levenberg-Marquardt (mu) para ganhos
  feedforward k_t e feedback K_t;
- Executa rollout Forward com Armijo backtracking line search garantindo reducao monotona do custo
  J(X, U) = sum l(x_t, u_t) + l_f(x_T) ate convergencia sem tokens LLM.
"""
from __future__ import annotations

import math
import time
from typing import Callable, Dict, Any, List, Optional, Tuple
import numpy as np


class PontryaginILQROptimizer:
    """
    Otimizador de Trajetorias Nao-Lineares via iLQR (Iterative LQR).
    """

    def __init__(self, dt: float = 0.05, max_iters: int = 30):
        self.dt = float(dt)
        self.max_iters = int(max_iters)

    def _default_pendulum_step(self, x: np.ndarray, u: np.ndarray) -> np.ndarray:
        """Dinamica discreta RK2 (midpoint) do pendulo invertido com amortecimento nao-linear."""
        dt = self.dt
        g_l = 9.81
        b = 0.15

        def f_cont(st: np.ndarray, ctrl: np.ndarray) -> np.ndarray:
            theta, omega = st[0], st[1]
            # theta=0 e o equilibrio superior instavel
            dtheta = omega
            domega = g_l * math.sin(theta) - b * omega + float(ctrl[0])
            return np.array([dtheta, domega], dtype=np.float64)

        k1 = f_cont(x, u)
        k2 = f_cont(x + 0.5 * dt * k1, u)
        return x + dt * k2

    @staticmethod
    def _finite_diff_jacobians(
        step_fn: Callable[[np.ndarray, np.ndarray], np.ndarray],
        x: np.ndarray,
        u: np.ndarray,
        eps: float = 1e-5,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Jacobianos f_x (n, n) e f_u (n, m) por diferencas finitas centrais."""
        n = len(x)
        m = len(u)
        fx = np.zeros((n, n), dtype=np.float64)
        fu = np.zeros((n, m), dtype=np.float64)

        for i in range(n):
            dx = np.zeros(n, dtype=np.float64)
            dx[i] = eps
            fx[:, i] = (step_fn(x + dx, u) - step_fn(x - dx, u)) / (2.0 * eps)

        for j in range(m):
            du = np.zeros(m, dtype=np.float64)
            du[j] = eps
            fu[:, j] = (step_fn(x, u + du) - step_fn(x, u - du)) / (2.0 * eps)

        return fx, fu

    def optimize_trajectory(
        self,
        x0: Optional[List[float] | np.ndarray] = None,
        x_goal: Optional[List[float] | np.ndarray] = None,
        horizon: int = 40,
        max_iters: Optional[int] = None,
        step_fn: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None,
    ) -> Dict[str, Any]:
        """
        Resolve o problema de otimizacao de trajetoria nao-linear via iLQR.
        """
        t0 = time.perf_counter()

        f_step = step_fn if step_fn is not None else self._default_pendulum_step
        x_start = np.asarray(x0 if x0 is not None else [0.8, 0.0], dtype=np.float64).reshape(-1)
        x_target = np.asarray(x_goal if x_goal is not None else [0.0, 0.0], dtype=np.float64).reshape(-1)
        n = len(x_start)
        m = 1
        T = int(horizon)
        iters = int(max_iters if max_iters is not None else self.max_iters)

        Q = np.diag([4.0, 0.4]) if n == 2 else 2.0 * np.eye(n)
        Qf = np.diag([40.0, 4.0]) if n == 2 else 20.0 * np.eye(n)
        R = 0.05 * np.eye(m)

        def eval_cost(X: np.ndarray, U: np.ndarray) -> float:
            total = 0.0
            for t in range(T):
                dx = X[t] - x_target
                total += 0.5 * float(dx.T @ Q @ dx + U[t].T @ R @ U[t])
            dx_f = X[T] - x_target
            total += 0.5 * float(dx_f.T @ Qf @ dx_f)
            return total

        # Rollout nominal inicial (controle nulo)
        U = np.zeros((T, m), dtype=np.float64)
        X = np.zeros((T + 1, n), dtype=np.float64)
        X[0] = x_start
        for t in range(T):
            X[t + 1] = f_step(X[t], U[t])

        initial_cost = eval_cost(X, U)
        initial_terminal_err = float(np.linalg.norm(X[T] - x_target))
        curr_cost = initial_cost
        mu = 1e-4

        iterations_run = 0
        for it in range(iters):
            iterations_run = it + 1
            # 1. Backward Riccati pass
            Vx = Qf @ (X[T] - x_target)
            Vxx = Qf.copy()

            k_ff = [np.zeros(m, dtype=np.float64) for _ in range(T)]
            K_fb = [np.zeros((m, n), dtype=np.float64) for _ in range(T)]

            diverged_backward = False
            for t in range(T - 1, -1, -1):
                fx, fu = self._finite_diff_jacobians(f_step, X[t], U[t])
                lx = Q @ (X[t] - x_target)
                lu = R @ U[t]

                Qx = lx + fx.T @ Vx
                Qu = lu + fu.T @ Vx
                Qxx = Q + fx.T @ Vxx @ fx
                Quu = R + fu.T @ Vxx @ fu
                Qux = fu.T @ Vxx @ fx

                Quu_reg = 0.5 * (Quu + Quu.T) + mu * np.eye(m)
                try:
                    eigvals = np.linalg.eigvalsh(Quu_reg)
                    if np.min(eigvals) <= 1e-9:
                        diverged_backward = True
                        break
                    k_t = -np.linalg.solve(Quu_reg, Qu)
                    K_t = -np.linalg.solve(Quu_reg, Qux)
                except np.linalg.LinAlgError:
                    diverged_backward = True
                    break

                k_ff[t] = k_t
                K_fb[t] = K_t

                Vx = Qx + K_t.T @ Quu @ k_t + K_t.T @ Qu + Qux.T @ k_t
                Vxx = Qxx + K_t.T @ Quu @ K_t + K_t.T @ Qux + Qux.T @ K_t
                Vxx = 0.5 * (Vxx + Vxx.T)

            if diverged_backward:
                mu = min(mu * 10.0, 1e4)
                continue

            # 2. Forward Armijo backtracking line search
            accepted = False
            for alpha in (1.0, 0.5, 0.25, 0.1, 0.05):
                X_new = np.zeros_like(X)
                U_new = np.zeros_like(U)
                X_new[0] = x_start
                for t in range(T):
                    du = alpha * k_ff[t] + K_fb[t] @ (X_new[t] - X[t])
                    U_new[t] = U[t] + du
                    X_new[t + 1] = f_step(X_new[t], U_new[t])

                new_cost = eval_cost(X_new, U_new)
                if new_cost < curr_cost:
                    rel_improv = (curr_cost - new_cost) / max(curr_cost, 1e-12)
                    X, U = X_new, U_new
                    curr_cost = new_cost
                    mu = max(mu * 0.5, 1e-6)
                    accepted = True
                    if rel_improv < 1e-6:
                        break
                    break

            if not accepted:
                mu = min(mu * 10.0, 1e4)
                if mu >= 1e4:
                    break
            elif rel_improv < 1e-6:
                break

        final_terminal_err = float(np.linalg.norm(X[T] - x_target))
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "ILQR_NONLINEAR_TRAJECTORY_OPTIMIZED",
            "horizon": T,
            "iterations": iterations_run,
            "initial_cost": round(initial_cost, 5),
            "final_cost": round(curr_cost, 5),
            "cost_reduction_ratio": round(initial_cost / max(curr_cost, 1e-12), 3),
            "initial_terminal_error": round(initial_terminal_err, 5),
            "final_terminal_error": round(final_terminal_err, 5),
            "final_state": [round(float(v), 5) for v in X[T]],
            "elapsed_us": round(elapsed_us, 2),
        }
