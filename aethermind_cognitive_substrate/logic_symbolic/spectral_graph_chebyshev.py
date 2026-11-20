"""Spectral Graph Chebyshev Filter & Heat Diffusion Engine.

Organ 63 do Substrato Cognitivo Nao-LLM (AetherCOS v5.7).
Processamento Espectral de Sinais em Grafos via Polinomios de Chebyshev (Hammond et al., 2011 / Defferrard, 2016):
- Constroi o Laplaciano Simetrico Normalizado L_sym = I - D^{-1/2} A D^{-1/2} com espectro em [0, 2];
- Reescala L_tilde = (2 / lambda_max) L_sym - I para [-1, 1] e aplica recorrencia de 3 termos
  T_0(x) = x, T_1(x) = L_tilde x, T_k(x) = 2 L_tilde T_{k-1}(x) - T_{k-2}(x) em tempo O(K |E|);
- Implementa difusao termica espectral exp(-t L_sym) sem autodecomposicao completa, preservando
  a suavizacao da variacao total de Dirichlet (x^T L_sym x) e conservando massa espectral.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional
import numpy as np


class SpectralGraphChebyshevEngine:
    """
    Motor de Filtragem Espectral em Grafos com Polinomios de Chebyshev e Difusao Termica.
    """

    def __init__(self, cheb_order: int = 8, diffusion_time: float = 1.5):
        self.cheb_order = int(cheb_order)
        self.diffusion_time = float(diffusion_time)

    @staticmethod
    def normalized_laplacian(adjacency: np.ndarray) -> np.ndarray:
        """Computa L_sym = I - D^{-1/2} A D^{-1/2}."""
        A = np.asarray(adjacency, dtype=np.float64)
        A = 0.5 * (A + A.T)
        np.fill_diagonal(A, 0.0)
        deg = np.sum(A, axis=1)
        inv_sqrt_deg = np.where(deg > 1e-12, 1.0 / np.sqrt(np.maximum(deg, 1e-12)), 0.0)
        D_inv_sqrt = np.diag(inv_sqrt_deg)
        n = A.shape[0]
        return np.eye(n, dtype=np.float64) - D_inv_sqrt @ A @ D_inv_sqrt

    @staticmethod
    def _cheb_heat_coefficients(t: float, order: int) -> np.ndarray:
        """
        Coeficientes de Chebyshev c_k para h(lambda) = exp(-t * lambda) em lambda in [0, lambda_max=2]
        via quadratura de Gauss-Chebyshev em N_quad pontos.
        """
        n_quad = max(64, 4 * (order + 1))
        j = np.arange(n_quad, dtype=np.float64)
        theta = math.pi * (j + 0.5) / n_quad
        # u = cos(theta) in [-1, 1] corresponde a lambda = (u + 1) in [0, 2]
        lam = np.cos(theta) + 1.0
        h_vals = np.exp(-t * lam)

        coeffs = np.zeros(order + 1, dtype=np.float64)
        for k in range(order + 1):
            c_k = (2.0 / n_quad) * np.sum(h_vals * np.cos(k * theta))
            if k == 0:
                c_k *= 0.5
            coeffs[k] = c_k
        return coeffs

    def apply_chebyshev_filter(
        self,
        adjacency: Optional[List[List[float]] | np.ndarray] = None,
        signal: Optional[List[float] | np.ndarray] = None,
        order: Optional[int] = None,
        diffusion_time: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Aplica filtro passa-baixa de difusao termica espectral exp(-t L_sym) via
        expansao em polinomios de Chebyshev de ordem K.
        """
        t0 = time.perf_counter()

        if adjacency is None:
            # Grafo em anel + pontes (10 nos) com sinal ruidoso de alta frequencia
            n = 10
            A = np.zeros((n, n), dtype=np.float64)
            for i in range(n):
                A[i, (i + 1) % n] = 1.0
                A[(i + 1) % n, i] = 1.0
            A[0, 5] = A[5, 0] = 1.0
            A[2, 7] = A[7, 2] = 1.0
        else:
            A = np.asarray(adjacency, dtype=np.float64)
            n = A.shape[0]

        if signal is None:
            x = np.array([((-1.0) ** i) * 2.0 + 1.0 for i in range(n)], dtype=np.float64)
        else:
            x = np.asarray(signal, dtype=np.float64).reshape(-1)
            assert len(x) == n, f"Dimensao do sinal ({len(x)}) diverge do grafo ({n})"

        K = int(order if order is not None else self.cheb_order)
        tau = float(diffusion_time if diffusion_time is not None else self.diffusion_time)

        L_sym = self.normalized_laplacian(A)
        # Espectro de L_sym sempre limitado em [0, 2]; logo lambda_max <= 2.0
        lambda_max = 2.0
        L_tilde = (2.0 / lambda_max) * L_sym - np.eye(n, dtype=np.float64)

        coeffs = self._cheb_heat_coefficients(tau, K)

        # Recorrencia de 3 termos de Chebyshev: O(K * |E|)
        T_prev = x.copy()
        y = coeffs[0] * T_prev
        if K >= 1:
            T_curr = L_tilde @ x
            y = y + coeffs[1] * T_curr
            for k in range(2, K + 1):
                T_next = 2.0 * (L_tilde @ T_curr) - T_prev
                y = y + coeffs[k] * T_next
                T_prev, T_curr = T_curr, T_next

        # Energia de Dirichlet (Variacao Total no Grafo): x^T L_sym x
        dirichlet_in = float(x.T @ L_sym @ x)
        dirichlet_out = float(y.T @ L_sym @ y)
        smoothness_ratio = dirichlet_out / max(dirichlet_in, 1e-12)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "SPECTRAL_CHEBYSHEV_FILTER_APPLIED",
            "n_nodes": n,
            "cheb_order": K,
            "diffusion_time": tau,
            "dirichlet_energy_in": round(dirichlet_in, 6),
            "dirichlet_energy_out": round(dirichlet_out, 6),
            "smoothness_ratio": round(smoothness_ratio, 6),
            "smoothing_verified": dirichlet_out < dirichlet_in,
            "filtered_signal": [round(float(v), 5) for v in y],
            "elapsed_us": round(elapsed_us, 2),
        }
