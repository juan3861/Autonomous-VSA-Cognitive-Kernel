"""Discrete Lyapunov Stability & Optimal LQR Riccati (DARE) Formal Certifier.

Organ 54 do Substrato Cognitivo Não-LLM (AetherCOS v5.2).
Sintetiza certificados matemáticos exatos de estabilidade assintótica para sistemas dinâmicos
em tempo discreto x_{t+1} = A x_t + B u_t sem dependências pesadas:
1. Solução da Equação Discreta de Lyapunov (Equação de Stein) A^T P A - P = -Q via Algoritmo
   de Duplicação Quadrática de Smith (O(n^3 log k) — convergência quadrática superexponencial!),
   com validação de resíduo numérico e autovalores lambda_min(P) > 0 garantindo que a função
   energética V(x) = x^T P x decresce estritamente: Delta V(x) = -x^T Q x < 0.
2. Síntese de Controlador LQR Estabilizante Ótimo por resolução iterativa da Equação Algébrica
   Discreta de Riccati (DARE): A^T P A - P - A^T P B (R + B^T P B)^{-1} B^T P A + Q = 0,
   gerando o ganho ótimo u_t = -K x_t mesmo para plantas originalmente instáveis (rho(A) >= 1)
   e certificando Lyapunov no sistema em malha fechada A_cl = A - B K.
"""
from __future__ import annotations

import ctypes
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np


class LyapunovSDPStabilityCertifier:
    """
    Certificador Analítico de Estabilidade de Lyapunov (Stein / Smith Doubling,
    com aceleração bare-metal opcional em Rust LTO C-ABI) e Síntese LQR via DARE.
    """

    def __init__(self, max_doubling_iters: int = 24, dare_max_iters: int = 250, tol: float = 1e-11):
        self.max_doubling_iters = int(max_doubling_iters)
        self.dare_max_iters = int(dare_max_iters)
        self.tol = float(tol)
        self._native_fn = None
        self._native_checked = False

    def _get_native_fn(self):
        if self._native_checked:
            return self._native_fn
        self._native_checked = True
        try:
            from aethermind_cognitive_substrate.physical_bridge.native_cortex_dll_singleton import (
                get_native_cortex_dll,
            )
            lib = get_native_cortex_dll()
            if lib is not None and hasattr(lib, "lyapunov_smith_doubling_f64"):
                self._native_fn = lib.lyapunov_smith_doubling_f64
        except Exception:
            self._native_fn = None
        return self._native_fn

    def certify_discrete_lyapunov(
        self,
        A: List[List[float]] | np.ndarray,
        Q: Optional[List[List[float]] | np.ndarray] = None,
        prefer_native: bool = True,
    ) -> Dict[str, Any]:
        """
        Resolve A^T P A - P = -Q por duplicação quadrática de Smith e certifica rho(A) < 1 e P > 0.
        """
        t0 = time.perf_counter()
        A_mat = np.asarray(A, dtype=np.float64)
        n, m = A_mat.shape
        if n != m:
            raise ValueError(f"Matriz A deve ser quadrada, recebido {A_mat.shape}")

        Q_mat = np.eye(n, dtype=np.float64) if Q is None else np.asarray(Q, dtype=np.float64)
        Q_mat = 0.5 * (Q_mat + Q_mat.T)

        eigvals = np.linalg.eigvals(A_mat)
        spectral_radius = float(np.max(np.abs(eigvals)))

        if spectral_radius >= 1.0 - 1e-9:
            return {
                "status": "LYAPUNOV_UNSTABLE_SYSTEM",
                "asymptotically_stable": False,
                "positive_definite_P": False,
                "spectral_radius_rho": round(spectral_radius, 6),
                "min_eigenvalue_P": None,
                "stein_residual_fro": None,
                "elapsed_us": round((time.perf_counter() - t0) * 1e6, 2),
            }

        native_fn = self._get_native_fn() if (prefer_native and n <= 64) else None
        if native_fn is not None:
            a_c = np.ascontiguousarray(A_mat, dtype=np.float64)
            q_c = np.ascontiguousarray(Q_mat, dtype=np.float64)
            p_out = np.zeros((n, n), dtype=np.float64)
            iters_c = ctypes.c_size_t(0)
            res_val = float(
                native_fn(
                    a_c.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    q_c.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    n,
                    self.max_doubling_iters,
                    self.tol,
                    p_out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    ctypes.byref(iters_c),
                )
            )
            if res_val >= 0.0:
                Pk = p_out
                residual = res_val
                iters_used = int(iters_c.value)
                backend = "aether_cortex_vsa.dll (Rust LTO C-ABI)"
            else:
                native_fn = None

        if native_fn is None:
            # Algoritmo de duplicação de Smith em NumPy: P = sum_{k=0}^{inf} (A^k)^T Q A^k
            Ak = A_mat.copy()
            Pk = Q_mat.copy()
            iters_used = 0
            for it in range(self.max_doubling_iters):
                iters_used = it + 1
                delta = Ak.T @ Pk @ Ak
                Pk_next = Pk + delta
                Pk_next = 0.5 * (Pk_next + Pk_next.T)
                Ak_next = Ak @ Ak
                if float(np.linalg.norm(delta, ord="fro")) < self.tol:
                    Pk = Pk_next
                    break
                Pk = Pk_next
                Ak = Ak_next

            residual = float(np.linalg.norm(A_mat.T @ Pk @ A_mat - Pk + Q_mat, ord="fro"))
            backend = "numpy_python"

        p_eigs = np.linalg.eigvalsh(Pk)
        min_eig_p = float(np.min(p_eigs))
        max_eig_p = float(np.max(p_eigs))
        is_pd = bool(min_eig_p > 0.0)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "LYAPUNOV_STABILITY_CERTIFIED" if is_pd else "LYAPUNOV_CERTIFICATION_FAILED",
            "backend": backend,
            "asymptotically_stable": bool(is_pd and spectral_radius < 1.0 and residual < 1e-6),
            "positive_definite_P": is_pd,
            "spectral_radius_rho": round(spectral_radius, 6),
            "min_eigenvalue_P": round(min_eig_p, 6),
            "max_eigenvalue_P": round(max_eig_p, 6),
            "condition_number_P": round(max_eig_p / max(min_eig_p, 1e-12), 4),
            "stein_residual_fro": float(f"{residual:.3e}"),
            "smith_doubling_iters": iters_used,
            "lyapunov_matrix_P": [[round(float(v), 5) for v in row] for row in Pk],
            "elapsed_us": round(elapsed_us, 2),
        }

    def synthesize_stabilizing_lqr(
        self,
        A: List[List[float]] | np.ndarray,
        B: List[List[float]] | np.ndarray,
        Q: Optional[List[List[float]] | np.ndarray] = None,
        R: Optional[List[List[float]] | np.ndarray] = None,
    ) -> Dict[str, Any]:
        """
        Resolve a Equação Algébrica Discreta de Riccati (DARE) para encontrar o ganho ótimo K
        que estabiliza a planta A_cl = A - B K e certifica Lyapunov no sistema em malha fechada.
        """
        t0 = time.perf_counter()
        A_mat = np.asarray(A, dtype=np.float64)
        B_mat = np.asarray(B, dtype=np.float64)
        n = A_mat.shape[0]
        m = B_mat.shape[1]

        Q_mat = np.eye(n, dtype=np.float64) if Q is None else np.asarray(Q, dtype=np.float64)
        R_mat = np.eye(m, dtype=np.float64) if R is None else np.asarray(R, dtype=np.float64)

        open_loop_rho = float(np.max(np.abs(np.linalg.eigvals(A_mat))))

        # Iteração de valor Riccati estabilizada
        P = Q_mat.copy()
        iters = 0
        converged = False
        K = np.zeros((m, n), dtype=np.float64)
        for it in range(self.dare_max_iters):
            iters = it + 1
            BtP = B_mat.T @ P
            G = R_mat + BtP @ B_mat
            K = np.linalg.solve(G, BtP @ A_mat)
            P_next = A_mat.T @ P @ A_mat - A_mat.T @ P @ B_mat @ K + Q_mat
            P_next = 0.5 * (P_next + P_next.T)
            if float(np.linalg.norm(P_next - P, ord="fro")) < self.tol:
                P = P_next
                converged = True
                break
            P = P_next

        A_cl = A_mat - B_mat @ K
        cl_cert = self.certify_discrete_lyapunov(A_cl, Q_mat + K.T @ R_mat @ K)
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "LQR_DARE_STABILIZED_AND_CERTIFIED" if cl_cert["asymptotically_stable"] else "LQR_STABILIZATION_FAILED",
            "dare_converged": converged,
            "dare_iters": iters,
            "open_loop_spectral_radius": round(open_loop_rho, 6),
            "closed_loop_spectral_radius": cl_cert["spectral_radius_rho"],
            "closed_loop_lyapunov_certified": cl_cert["asymptotically_stable"],
            "closed_loop_stein_residual": cl_cert["stein_residual_fro"],
            "optimal_gain_K": [[round(float(v), 5) for v in row] for row in K],
            "elapsed_us": round(elapsed_us, 2),
        }
