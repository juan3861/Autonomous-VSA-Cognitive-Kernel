"""Bayesian Optimization Engine with Analytical Expected Improvement (EI) Acquisition.

Organ 57 do Substrato Cognitivo Não-LLM (AetherCOS v5.4).
Otimizador global livre de gradientes sobre funções caixa-preta contínuas caras f(x):
- Utiliza `SparseGaussianProcessEstimator` (Órgão 55) como modelo substituto (surrogate) Bayesiano;
- Avalia aquisição exata por Melhoria Esperada (Expected Improvement — Jones et al., 1998):
    EI(x) = (mu(x) - f_max - xi) * Phi(Z) + sigma(x) * phi(Z),   onde Z = (mu(x) - f_max - xi) / sigma(x)
- Também suporta Upper Confidence Bound (UCB): UCB(x) = mu(x) + kappa * sigma(x);
- Seleciona o próximo ponto ótimo x_next equilibrando exploração (regiões de alta incerteza sigma)
  e aproveitamento (regiões de alta média prevista mu) com garantia determinística e zero tokens LLM.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from aethermind_cognitive_substrate.planning.gaussian_process_cholesky import (
    SparseGaussianProcessEstimator,
)


class BayesianOptimizationEIEngine:
    """
    Motor de Otimização Bayesiana com Aquisição Analítica por Expected Improvement (EI) e UCB.
    """

    def __init__(
        self,
        kernel: str = "rbf",
        lengthscale: float = 0.8,
        signal_variance: float = 1.0,
        noise_variance: float = 1e-4,
        seed: int = 202657,
    ):
        self.kernel = kernel
        self.lengthscale = float(lengthscale)
        self.signal_variance = float(signal_variance)
        self.noise_variance = float(noise_variance)
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _normal_cdf(z: np.ndarray) -> np.ndarray:
        """Função de distribuição acumulada (CDF) normal padrão via math.erf vetorizado."""
        return 0.5 * (1.0 + np.vectorize(math.erf)(z / math.sqrt(2.0)))

    @staticmethod
    def _normal_pdf(z: np.ndarray) -> np.ndarray:
        """Função de densidade de probabilidade (PDF) normal padrão."""
        return np.exp(-0.5 * (z * z)) / math.sqrt(2.0 * math.pi)

    def compute_expected_improvement(
        self,
        mu: np.ndarray,
        std: np.ndarray,
        f_best: float,
        xi: float = 0.01,
        maximize: bool = True,
    ) -> np.ndarray:
        """Calcula Expected Improvement analítico sobre os candidatos."""
        mu_eval = mu if maximize else -mu
        f_target = f_best if maximize else -f_best
        diff = mu_eval - f_target - xi

        safe_std = np.maximum(std, 1e-12)
        Z = diff / safe_std
        phi_z = self._normal_pdf(Z)
        Phi_z = self._normal_cdf(Z)

        ei = diff * Phi_z + safe_std * phi_z
        # Zera onde a incerteza é desprezível
        ei[std < 1e-8] = 0.0
        return np.maximum(ei, 0.0)

    def compute_ucb(
        self,
        mu: np.ndarray,
        std: np.ndarray,
        kappa: float = 2.0,
        maximize: bool = True,
    ) -> np.ndarray:
        """Calcula Upper Confidence Bound (UCB)."""
        return (mu + kappa * std) if maximize else -(mu - kappa * std)

    def suggest_next_query(
        self,
        X_observed: List[List[float]] | List[float] | np.ndarray,
        y_observed: List[float] | np.ndarray,
        bounds: List[Tuple[float, float]],
        acquisition: str = "ei",
        xi: float = 0.01,
        kappa: float = 2.0,
        maximize: bool = True,
        n_candidates: int = 256,
        num_candidates: Optional[int] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Ajusta o GP aos dados observados e sugere o próximo ponto de avaliação x_next
        que maximiza a função de aquisição sobre a região delimitada por `bounds`.
        """
        if num_candidates is not None:
            n_candidates = num_candidates
        t0 = time.perf_counter()
        X_obs = np.asarray(X_observed, dtype=np.float64)
        if X_obs.ndim == 1:
            X_obs = X_obs.reshape(-1, 1)
        y_obs = np.asarray(y_observed, dtype=np.float64).reshape(-1)

        dim = len(bounds)
        assert X_obs.shape[1] == dim, f"Dimensão dos dados ({X_obs.shape[1]}) diverge dos limites ({dim})"
        assert len(X_obs) == len(y_obs), "X_observed e y_observed devem ter o mesmo número de amostras"

        best_idx = int(np.argmax(y_obs) if maximize else np.argmin(y_obs))
        f_best = float(y_obs[best_idx])
        x_best = [round(float(v), 5) for v in X_obs[best_idx]]

        # Amostragem quase-aleatória de candidatos
        lows = np.array([b[0] for b in bounds], dtype=np.float64)
        highs = np.array([b[1] for b in bounds], dtype=np.float64)
        span = highs - lows

        candidates = lows + span * self.rng.uniform(0.0, 1.0, size=(n_candidates, dim))

        gp = SparseGaussianProcessEstimator(
            kernel=self.kernel,
            lengthscale=self.lengthscale,
            signal_variance=self.signal_variance,
            noise_variance=self.noise_variance,
        )
        gp_res = gp.fit_and_predict(X_obs, y_obs, candidates)
        mu_cand = np.array(gp_res["posterior_mean"], dtype=np.float64)
        std_cand = np.array(gp_res["posterior_std"], dtype=np.float64)

        if acquisition == "ucb":
            acq_values = self.compute_ucb(mu_cand, std_cand, kappa=kappa, maximize=maximize)
        else:
            acq_values = self.compute_expected_improvement(mu_cand, std_cand, f_best=f_best, xi=xi, maximize=maximize)

        next_idx = int(np.argmax(acq_values))
        x_next = candidates[next_idx]
        best_acq = float(acq_values[next_idx])

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "BAYESIAN_OPTIMIZATION_ACQUISITION_OPTIMIZED",
            "acquisition": acquisition,
            "maximize": maximize,
            "n_observed": len(X_obs),
            "n_candidates": n_candidates,
            "current_best_x": x_best,
            "current_best_y": round(f_best, 5),
            "best_observed_y": round(f_best, 5),
            "suggested_next_x": [round(float(v), 5) for v in x_next],
            "x_next": [round(float(v), 5) for v in x_next],
            "predicted_mu_at_next": round(float(mu_cand[next_idx]), 5),
            "predicted_mean": round(float(mu_cand[next_idx]), 5),
            "predicted_std_at_next": round(float(std_cand[next_idx]), 5),
            "predicted_std": round(float(std_cand[next_idx]), 5),
            "acquisition_score_at_next": round(best_acq, 6),
            "acquisition_score": round(best_acq, 6),
            "gp_train_rmse": gp_res["train_rmse"],
            "elapsed_us": round(elapsed_us, 2),
        }

    optimize_step = suggest_next_query
