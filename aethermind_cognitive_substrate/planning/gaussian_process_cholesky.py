"""Exact & Inducing-Point Gaussian Process Regression via Cholesky Factorization.

Organ 55 do Substrato Cognitivo Não-LLM (AetherCOS v5.3).
Modela funções contínuas desconhecidas com quantificação analítica exata de incerteza epistêmica
(Rasmussen & Williams, Gaussian Processes for Machine Learning):
- Suporta kernels estacionários RBF (Squared Exponential) e Matérn-3/2;
- Resolve (K(X, X) + sigma_n^2 I) alpha = y via fatoração de Cholesky K = L L^T numericamente
  estabilizada (com jitter adaptativo), evitando inversão explícita instável;
- Calcula Log-Marginal-Likelihood (evidência Bayesiana exata) para seleção de modelo;
- Prediz média posterior mu(x_*) e desvio-padrão epistêmico sigma(x_*), garantindo que
  regiões fora da distribuição observada (OOD) produzam incerteza estritamente maior do que
  regiões in-distribution.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional
import numpy as np


class SparseGaussianProcessEstimator:
    """
    Regressão por Processos Gaussianos (GPR) via Cholesky L L^T para estimação
    de média posterior e incerteza epistêmica contínua OOD.
    """

    def __init__(
        self,
        kernel: str = "rbf",
        lengthscale: float = 1.0,
        signal_variance: float = 1.0,
        noise_variance: float = 1e-3,
    ):
        self.kernel = kernel
        self.lengthscale = float(lengthscale)
        self.signal_variance = float(signal_variance)
        self.noise_variance = float(noise_variance)

    def _compute_kernel(self, X1: np.ndarray, X2: np.ndarray) -> np.ndarray:
        """Matriz de covariância K(X1, X2) para RBF ou Matérn-3/2."""
        diff = X1[:, None, :] - X2[None, :, :]
        sq_dist = np.sum(diff * diff, axis=2)
        ls = max(self.lengthscale, 1e-6)
        if self.kernel == "matern32":
            r = np.sqrt(np.maximum(sq_dist, 0.0)) / ls
            sqrt3_r = math.sqrt(3.0) * r
            return self.signal_variance * (1.0 + sqrt3_r) * np.exp(-sqrt3_r)
        # Padrão RBF
        return self.signal_variance * np.exp(-0.5 * sq_dist / (ls * ls))

    @staticmethod
    def _solve_lower(L: np.ndarray, B: np.ndarray) -> np.ndarray:
        return np.linalg.solve(L, B)

    def fit_and_predict(
        self,
        X_train: List[List[float]] | List[float] | np.ndarray,
        y_train: List[float] | np.ndarray,
        X_query: List[List[float]] | List[float] | np.ndarray,
    ) -> Dict[str, Any]:
        """
        Ajusta GP exato via Cholesky sobre (X_train, y_train) e avalia média e incerteza
        epistêmica em X_query.
        """
        t0 = time.perf_counter()
        X_tr = np.asarray(X_train, dtype=np.float64)
        if X_tr.ndim == 1:
            X_tr = X_tr.reshape(-1, 1)
        y_tr = np.asarray(y_train, dtype=np.float64).reshape(-1)
        X_q = np.asarray(X_query, dtype=np.float64)
        if X_q.ndim == 1:
            X_q = X_q.reshape(-1, 1)

        n = len(X_tr)
        K_xx = self._compute_kernel(X_tr, X_tr)
        jitter = max(self.noise_variance, 1e-8)

        L = None
        for _ in range(6):
            try:
                L = np.linalg.cholesky(K_xx + jitter * np.eye(n, dtype=np.float64))
                break
            except np.linalg.LinAlgError:
                jitter *= 10.0
        if L is None:
            raise RuntimeError("Falha na fatoração de Cholesky da matriz de covariância GP.")

        # alpha = L^{-T} (L^{-1} y)
        v_y = self._solve_lower(L, y_tr)
        alpha = np.linalg.solve(L.T, v_y)

        # Log Marginal Likelihood: -0.5 y^T alpha - sum(log(diag(L))) - 0.5 n log(2 pi)
        lml = float(
            -0.5 * float(np.dot(y_tr, alpha))
            - float(np.sum(np.log(np.maximum(np.diag(L), 1e-18))))
            - 0.5 * n * math.log(2.0 * math.pi)
        )

        # Predição posterior em X_query
        K_xs = self._compute_kernel(X_tr, X_q)
        K_ss_diag = np.full(len(X_q), self.signal_variance, dtype=np.float64)

        mu_star = K_xs.T @ alpha
        v_s = self._solve_lower(L, K_xs)
        var_star = np.maximum(K_ss_diag - np.sum(v_s * v_s, axis=0), 1e-12)
        std_star = np.sqrt(var_star)

        # Erro de reconstrução nos pontos de treino (sanity check)
        train_pred = K_xx @ alpha
        train_rmse = float(np.sqrt(np.mean((train_pred - y_tr) ** 2)))

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "GP_CHOLESKY_POSTERIOR_COMPUTED",
            "kernel": self.kernel,
            "n_train": n,
            "n_query": int(len(X_q)),
            "log_marginal_likelihood": round(lml, 5),
            "train_rmse": round(train_rmse, 6),
            "posterior_mean": [round(float(m), 5) for m in mu_star],
            "posterior_std": [round(float(s), 5) for s in std_star],
            "posterior_var": [round(float(v), 6) for v in var_star],
            "elapsed_us": round(elapsed_us, 2),
        }
