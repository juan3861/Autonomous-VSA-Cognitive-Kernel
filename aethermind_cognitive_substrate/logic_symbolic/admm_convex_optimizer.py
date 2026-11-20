"""Bare-Metal ADMM Quadratic Program Convex Optimizer (OSQP / CVXPY Inspiration).

Organ 44 do Substrato Cognitivo Não-LLM (AetherCOS v4.6).
Resolve Programas Quadráticos Convexos sob restrições lineares em forma padrão OSQP:
    minimize_x   0.5 * x^T P x + q^T x
    subject to   l <= A x <= u
usando Alternating Direction Method of Multipliers (ADMM) com:
- Fatoração única (1-Shot) por decomposição de Cholesky da matriz KKT reduzida:
    M = P + sigma * I + rho * (A^T A)
- Sobrerrelaxação controlada (alpha in (1.0, 1.8)) para convergência acelerada.
- Projeção exata em caixa [l, u] e atualização dual por gradiente ascendido.
- Certificado de resíduos primal/dual ||Ax - z||_inf e ||rho A^T (z^{k+1} - z^k)||_inf.
Zero dependências externas pesadas e latência sub-milissegundo em hardware local.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class ADMMConvexQPOptimizer:
    """
    Otimizador Convexo ADMM Bare-Metal para Alocação de Recursos e Síntese de Controle.
    Implementa o núcleo algorítmico de separação de operadores estilo OSQP.
    """

    def __init__(
        self,
        rho: float = 0.5,
        sigma: float = 1e-6,
        alpha_relax: float = 1.6,
        max_iter: int = 400,
        eps_abs: float = 1e-5,
        eps_rel: float = 1e-4
    ):
        self.rho = rho
        self.sigma = sigma
        self.alpha_relax = alpha_relax
        self.max_iter = max_iter
        self.eps_abs = eps_abs
        self.eps_rel = eps_rel

    def solve_qp(
        self,
        P: List[List[float]] | np.ndarray,
        q: List[float] | np.ndarray,
        A: List[List[float]] | np.ndarray,
        l: List[float] | np.ndarray,
        u: List[float] | np.ndarray,
        max_iter: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Resolve o QP convexo: min 0.5 x^T P x + q^T x  s.t.  l <= Ax <= u.
        Suporta limites infinitos (-1e12 / +1e12) e restrições de igualdade (l_i == u_i).
        """
        t0 = time.perf_counter()

        P_mat = np.array(P, dtype=np.float64)
        P_mat = 0.5 * (P_mat + P_mat.T)
        q_vec = np.array(q, dtype=np.float64).reshape(-1)
        A_mat = np.array(A, dtype=np.float64)
        if A_mat.ndim == 1:
            A_mat = A_mat.reshape(1, -1)
        l_vec = np.array(l, dtype=np.float64).reshape(-1)
        u_vec = np.array(u, dtype=np.float64).reshape(-1)

        n = len(q_vec)
        m = A_mat.shape[0]
        iters_limit = max_iter if max_iter is not None else self.max_iter

        # Fatoração única de Cholesky da matriz de sistema M = P + sigma*I + rho*A^T*A
        # Invertendo L uma única vez (L^{-1}), obtemos M^{-1} = L^{-T} L^{-1} simétrica positiva-definida,
        # reduzindo cada passo ADMM no laço a um único produto matriz-vetor BLAS O(n^2)!
        M = P_mat + self.sigma * np.eye(n, dtype=np.float64) + self.rho * (A_mat.T @ A_mat)
        L = np.linalg.cholesky(M)
        L_inv = np.linalg.solve(L, np.eye(n, dtype=np.float64))
        M_inv = L_inv.T @ L_inv

        x = np.zeros(n, dtype=np.float64)
        z = np.clip(np.zeros(m, dtype=np.float64), l_vec, u_vec)
        y = np.zeros(m, dtype=np.float64)

        converged = False
        primal_res = float("inf")
        dual_res = float("inf")
        iters_run = 0

        for it in range(1, iters_limit + 1):
            iters_run = it

            # 1. Passo x em O(n^2) BLAS direto via M_inv pré-fatorada por Cholesky
            rhs = self.sigma * x - q_vec + A_mat.T @ (self.rho * z - y)
            x_tilde = M_inv @ rhs

            z_tilde = A_mat @ x_tilde

            # 2. Sobrerrelaxação e Projeção em caixa [l, u]
            x = self.alpha_relax * x_tilde + (1.0 - self.alpha_relax) * x
            z_prev = z
            z_relaxed = self.alpha_relax * z_tilde + (1.0 - self.alpha_relax) * z_prev
            z = np.clip(z_relaxed + y / self.rho, l_vec, u_vec)

            # 3. Atualização do multiplicador dual y
            y = y + self.rho * (z_relaxed - z)

            # 4. Critério de parada primal/dual a cada 5 passos (ou no último)
            if it % 5 == 0 or it == iters_limit:
                Ax = A_mat @ x
                primal_res = float(np.linalg.norm(Ax - z, ord=np.inf))
                dual_res = float(np.linalg.norm(self.rho * (A_mat.T @ (z - z_prev)), ord=np.inf))

                scale_p = max(
                    float(np.linalg.norm(Ax, ord=np.inf)),
                    float(np.linalg.norm(z, ord=np.inf)),
                    1e-9
                )
                scale_d = max(
                    float(np.linalg.norm(P_mat @ x, ord=np.inf)),
                    float(np.linalg.norm(A_mat.T @ y, ord=np.inf)),
                    float(np.linalg.norm(q_vec, ord=np.inf)),
                    1e-9
                )
                tol_p = self.eps_abs + self.eps_rel * scale_p
                tol_d = self.eps_abs + self.eps_rel * scale_d

                if primal_res <= tol_p and dual_res <= tol_d:
                    converged = True
                    break

        obj_val = float(0.5 * (x @ P_mat @ x) + (q_vec @ x))
        Ax_final = A_mat @ x
        max_bound_violation = float(
            max(
                0.0,
                float(np.max(l_vec - Ax_final)) if m > 0 else 0.0,
                float(np.max(Ax_final - u_vec)) if m > 0 else 0.0
            )
        )
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "ADMM_QP_OPTIMAL" if converged else "ADMM_QP_MAX_ITER",
            "converged": converged,
            "iterations": iters_run,
            "optimal_x": [round(float(v), 6) for v in x],
            "objective_value": round(obj_val, 6),
            "primal_residual": float(f"{primal_res:.3e}"),
            "dual_residual": float(f"{dual_res:.3e}"),
            "max_constraint_violation": float(f"{max_bound_violation:.3e}"),
            "constraints_satisfied": bool(max_bound_violation <= 1e-3),
            "elapsed_us": round(elapsed_us, 2)
        }
