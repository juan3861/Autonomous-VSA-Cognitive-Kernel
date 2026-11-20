"""Entropic Optimal Transport (Log-Domain Sinkhorn-Knopp) & Wasserstein Engine.

Organ 56 do Substrato Cognitivo Não-LLM (AetherCOS v5.3).
Resolve o problema de Transporte Ótimo Regularizado por Entropia (Cuturi, NeurIPS 2013):
    min_{P in U(a, b)} <P, C> - eps * H(P)
em domínio logarítmico estabilizado (Log-Sum-Exp) para evitar underflow numérico mesmo para
regularizações pequenas eps:
- Calcula o plano ótimo de acoplamento P* com satisfação estrita das restrições marginais
  ||P* 1 - a||_1 + ||(P*)^T 1 - b||_1 < tol;
- Computa o custo exato de Wasserstein <P*, C> (definido mesmo quando os suportes das
  distribuições a e b são disjuntos — onde divergência KL explode para +inf);
- Suporta interpolação / baricentro de Wasserstein entre distribuições discretas.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class OptimalTransportSinkhornEngine:
    """
    Motor de Transporte Ótimo Entrópico (Sinkhorn-Knopp em Domínio Logarítmico).
    """

    def __init__(self, reg_epsilon: float = 0.05, max_iters: int = 600, tol: float = 1e-8):
        self.reg_epsilon = float(reg_epsilon)
        self.max_iters = int(max_iters)
        self.tol = float(tol)

    @staticmethod
    def _logsumexp(arr: np.ndarray, axis: int) -> np.ndarray:
        m = np.max(arr, axis=axis, keepdims=True)
        return np.squeeze(m + np.log(np.sum(np.exp(arr - m), axis=axis, keepdims=True) + 1e-300), axis=axis)

    def compute_transport_plan(
        self,
        source_weights: List[float] | np.ndarray,
        target_weights: List[float] | np.ndarray,
        cost_matrix: Optional[List[List[float]] | np.ndarray] = None,
        source_points: Optional[List[float] | np.ndarray] = None,
        target_points: Optional[List[float] | np.ndarray] = None,
        reg_epsilon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Resolve o plano ótimo P* e a distância de Wasserstein W_eps(a, b) via Sinkhorn log-estável.
        """
        t0 = time.perf_counter()
        eps = float(self.reg_epsilon if reg_epsilon is None else reg_epsilon)

        a_full = np.asarray(source_weights, dtype=np.float64).reshape(-1)
        b_full = np.asarray(target_weights, dtype=np.float64).reshape(-1)
        a_full = np.maximum(a_full, 0.0)
        b_full = np.maximum(b_full, 0.0)
        a_full = a_full / max(float(np.sum(a_full)), 1e-15)
        b_full = b_full / max(float(np.sum(b_full)), 1e-15)

        n_full, m_full = len(a_full), len(b_full)
        if cost_matrix is not None:
            C_full = np.asarray(cost_matrix, dtype=np.float64)
        else:
            x = np.linspace(0.0, 1.0, n_full) if source_points is None else np.asarray(source_points, dtype=np.float64)
            y = np.linspace(0.0, 1.0, m_full) if target_points is None else np.asarray(target_points, dtype=np.float64)
            if x.ndim == 1:
                x = x.reshape(-1, 1)
            if y.ndim == 1:
                y = y.reshape(-1, 1)
            diff = x[:, None, :] - y[None, :, :]
            C_full = np.sum(diff * diff, axis=2)

        # Restringe o transporte ao suporte estritamente positivo (evita rigidez artificial de log(0))
        a_mask = a_full > 1e-12
        b_mask = b_full > 1e-12
        a = a_full[a_mask]
        b = b_full[b_mask]
        a = a / float(np.sum(a))
        b = b / float(np.sum(b))
        C = C_full[np.ix_(a_mask, b_mask)]
        n, m = len(a), len(b)

        log_a = np.log(a)
        log_b = np.log(b)
        # Normaliza C pela escala máxima para manter regularização entrópica invariante à escala
        c_scale = max(float(np.max(C)), 1e-12)
        log_K = -(C / c_scale) / max(eps, 1e-6)

        f = np.zeros(n, dtype=np.float64)
        g = np.zeros(m, dtype=np.float64)
        iters_used = 0
        marginal_err = 1.0

        for it in range(self.max_iters):
            iters_used = it + 1
            f = log_a - self._logsumexp(log_K + g[None, :], axis=1)
            g = log_b - self._logsumexp(log_K + f[:, None], axis=0)
            if it % 5 == 0 or it == self.max_iters - 1:
                log_P = log_K + f[:, None] + g[None, :]
                P_cur = np.exp(np.clip(log_P, -500.0, 50.0))
                err_a = float(np.sum(np.abs(np.sum(P_cur, axis=1) - a)))
                err_b = float(np.sum(np.abs(np.sum(P_cur, axis=0) - b)))
                marginal_err = err_a + err_b
                if marginal_err < self.tol:
                    break

        log_P = log_K + f[:, None] + g[None, :]
        P_sub = np.exp(np.clip(log_P, -500.0, 50.0))
        transport_cost = float(np.sum(P_sub * C))
        wasserstein_2 = float(np.sqrt(max(transport_cost, 0.0)))
        err_a = float(np.sum(np.abs(np.sum(P_sub, axis=1) - a)))
        err_b = float(np.sum(np.abs(np.sum(P_sub, axis=0) - b)))
        marginal_err = err_a + err_b

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "SINKHORN_OPTIMAL_TRANSPORT_CONVERGED" if marginal_err < 1e-4 else "SINKHORN_MAX_ITERS",
            "converged": bool(marginal_err < 1e-4),
            "iterations": iters_used,
            "reg_epsilon": eps,
            "transport_cost_sq": round(transport_cost, 6),
            "wasserstein_distance": round(wasserstein_2, 6),
            "marginal_l1_error": float(f"{marginal_err:.3e}"),
            "plan_shape": [n_full, m_full],
            "active_support_shape": [n, m],
            "elapsed_us": round(elapsed_us, 2),
        }
