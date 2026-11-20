"""Sequential Monte Carlo (Bootstrap Particle Filter) Non-Gaussian & Multimodal Estimator.

Organ 51 do Substrato Cognitivo Não-LLM (AetherCOS v5.1).
Supera filtros Kalman (EKF/UKF) em regimes fortemente não-lineares ou multimodais (ex.: múltiplos
alvos plausíveis ou observações ambíguas y = x^2 + ruído com ambiguidade de sinal ±x):
- Mantém uma nuvem ponderada de N partículas {(x_i, w_i)} em R^d;
- Propaga partículas por dinâmica não-linear com ruído estocástico (process noise);
- Atualiza pesos via log-verossimilhança estabilizada (Log-Sum-Exp) para evitar underflow numérico;
- Monitora o Tamanho Efetivo de Amostra N_eff = 1 / sum(w_i^2) e dispara reamostragem
  sistemática de baixa variância (Low-Variance Systematic Resampling) apenas quando N_eff < threshold * N;
- Extrai média, covariância/variância posterior e detecção de modos dominantes via histograma/clusters.
"""
from __future__ import annotations

import ctypes
import math
import time
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional, Tuple
import numpy as np


class ParticleFilterSMCEngine:
    """
    Motor de Filtragem Bayesiana Sequencial de Monte Carlo (Particle Filter SMC)
    com reamostragem sistemática adaptativa baseada em N_eff, rastreamento multimodal
    e aceleração bare-metal opcional em Rust C-ABI (`smc_quadratic_track_f64`).
    """

    def __init__(
        self,
        num_particles: int = 512,
        state_dim: int = 1,
        resample_ratio: float = 0.5,
        seed: int = 202618,
    ):
        if num_particles < 16:
            raise ValueError("num_particles deve ser >= 16 para estabilidade estatística.")
        self.num_particles = int(num_particles)
        self.state_dim = int(state_dim)
        self.resample_ratio = float(resample_ratio)
        self.seed = int(seed)
        self.rng = np.random.default_rng(seed)
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
            if lib is not None and hasattr(lib, "smc_quadratic_track_f64"):
                self._native_fn = lib.smc_quadratic_track_f64
        except Exception:
            self._native_fn = None
        return self._native_fn

    @staticmethod
    def effective_sample_size(weights: np.ndarray) -> float:
        """Calcula N_eff = 1 / sum(w_i^2) para pesos normalizados."""
        denom = float(np.sum(weights * weights))
        return float(1.0 / max(denom, 1e-18))

    def systematic_resample(self, weights: np.ndarray) -> np.ndarray:
        """
        Reamostragem sistemática O(N) de variância mínima (Kitagawa / Thrun):
        Gera uma única semente u0 ~ Uniform(0, 1/N) e amostra pontos u0 + k/N.
        """
        n = len(weights)
        cdf = np.cumsum(weights)
        cdf[-1] = 1.0  # garante soma exata contra erro de ponto flutuante
        u0 = float(self.rng.uniform(0.0, 1.0 / n))
        positions = u0 + np.arange(n, dtype=np.float64) / n
        indices = np.searchsorted(cdf, positions, side="right")
        return np.clip(indices, 0, n - 1)

    @staticmethod
    def _normalize_log_weights(log_w: np.ndarray) -> np.ndarray:
        """Estabilização Log-Sum-Exp para evitar underflow em verossimilhanças extremas."""
        max_lw = float(np.max(log_w))
        if not math.isfinite(max_lw):
            return np.full(len(log_w), 1.0 / len(log_w), dtype=np.float64)
        shifted = np.exp(np.clip(log_w - max_lw, -500.0, 50.0))
        total = float(np.sum(shifted))
        if total <= 1e-18 or not math.isfinite(total):
            return np.full(len(log_w), 1.0 / len(log_w), dtype=np.float64)
        return shifted / total

    @staticmethod
    def extract_modes(particles: np.ndarray, weights: np.ndarray, dim: int = 0, bins: int = 24) -> List[Dict[str, float]]:
        """Identifica os modos dominantes na dimensão `dim` da densidade posterior."""
        vals = particles[:, dim]
        hist, edges = np.histogram(vals, bins=bins, weights=weights)
        centers = 0.5 * (edges[:-1] + edges[1:])
        modes: List[Dict[str, float]] = []
        for idx in range(len(hist)):
            left = hist[idx - 1] if idx > 0 else -1.0
            right = hist[idx + 1] if idx + 1 < len(hist) else -1.0
            if hist[idx] >= left and hist[idx] >= right and hist[idx] > 0.05:
                modes.append({"center": round(float(centers[idx]), 4), "mass": round(float(hist[idx]), 4)})
        modes.sort(key=lambda m: m["mass"], reverse=True)
        return modes[:4]

    def track_sequence(
        self,
        observations: List[List[float]] | List[float] | np.ndarray,
        scenario: str = "quadratic_bimodal",
        process_noise_std: float = 0.18,
        obs_noise_std: float = 0.35,
        init_low: float = -4.0,
        init_high: float = 4.0,
        transition_fn: Optional[Callable[[np.ndarray, int], np.ndarray]] = None,
        log_likelihood_fn: Optional[Callable[[np.ndarray, np.ndarray], np.ndarray]] = None,
        prefer_native: bool = True,
    ) -> Dict[str, Any]:
        """
        Executa filtragem SMC ao longo da sequência de observações.
        Cenário padrão `quadratic_bimodal`: y_t = x_t^2 + eps (observação simétrica gera
        posterior naturalmente bimodal em +sqrt(y_t) e -sqrt(y_t), onde EKF/UKF colapsam na média ~ 0).
        """
        t0 = time.perf_counter()
        obs_arr = np.asarray(observations, dtype=np.float64)
        if obs_arr.ndim == 1:
            obs_arr = obs_arr.reshape(-1, 1)

        n = self.num_particles
        d = self.state_dim

        if prefer_native and scenario == "quadratic_bimodal" and d == 1 and transition_fn is None and log_likelihood_fn is None:
            native_fn = self._get_native_fn()
            if native_fn is not None and len(obs_arr) > 0:
                obs_flat = np.ascontiguousarray(obs_arr[:, 0], dtype=np.float64)
                metrics = np.zeros(9, dtype=np.float64)
                rc = int(
                    native_fn(
                        obs_flat.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                        len(obs_flat),
                        n,
                        process_noise_std,
                        obs_noise_std,
                        init_low,
                        init_high,
                        self.resample_ratio,
                        self.seed,
                        metrics.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    )
                )
                if rc == 0:
                    modes_native: List[Dict[str, float]] = []
                    if metrics[5] > 0.05:
                        modes_native.append({"center": round(float(metrics[7]), 4), "mass": round(float(metrics[5]), 4)})
                    if metrics[6] > 0.05:
                        modes_native.append({"center": round(float(metrics[8]), 4), "mass": round(float(metrics[6]), 4)})
                    modes_native.sort(key=lambda m: m["mass"], reverse=True)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    return {
                        "status": "SMC_PARTICLE_FILTER_COMPLETED",
                        "backend": "aether_cortex_vsa.dll (Rust LTO C-ABI)",
                        "scenario": scenario,
                        "num_particles": n,
                        "state_dim": d,
                        "steps_processed": int(len(obs_flat)),
                        "resample_count": int(round(metrics[4])),
                        "resample_steps": [],
                        "min_neff": round(float(metrics[2]), 2),
                        "final_neff": round(float(metrics[3]), 2),
                        "final_posterior_mean": [round(float(metrics[0]), 5)],
                        "final_posterior_var": [round(float(metrics[1]), 5)],
                        "final_dominant_modes_dim0": modes_native,
                        "multimodal_detected": len(modes_native) >= 2,
                        "elapsed_ms": round(elapsed_ms, 3),
                    }

        particles = self.rng.uniform(init_low, init_high, size=(n, d))
        weights = np.full(n, 1.0 / n, dtype=np.float64)

        neff_history: List[float] = []
        resample_steps: List[int] = []
        posterior_means: List[List[float]] = []
        posterior_vars: List[List[float]] = []
        modes_final: List[Dict[str, float]] = []

        inv_two_var = 1.0 / (2.0 * (obs_noise_std ** 2) + 1e-12)

        for step_idx, y_t in enumerate(obs_arr):
            # 1. Propagação (Predição)
            if transition_fn is not None:
                particles = transition_fn(particles, step_idx)
            elif scenario == "quadratic_bimodal":
                # Passeio suave com pequena deriva senoidal determinística
                particles = 0.98 * particles + self.rng.normal(0.0, process_noise_std, size=(n, d))
            else:
                particles = particles + self.rng.normal(0.0, process_noise_std, size=(n, d))

            # 2. Ponderação Bayesiana em espaço logarítmico
            if log_likelihood_fn is not None:
                log_lik = log_likelihood_fn(particles, y_t)
            elif scenario == "quadratic_bimodal":
                pred_y = particles[:, 0] ** 2
                err = pred_y - y_t[0]
                log_lik = -(err * err) * inv_two_var
            else:
                diff = particles - y_t[:d]
                log_lik = -np.sum(diff * diff, axis=1) * inv_two_var

            log_w = np.log(np.maximum(weights, 1e-300)) + log_lik
            weights = self._normalize_log_weights(log_w)

            # 3. Monitoramento de degenerescência & reamostragem sistemática adaptativa
            neff = self.effective_sample_size(weights)
            neff_history.append(round(neff, 2))
            if neff < (self.resample_ratio * n):
                idx = self.systematic_resample(weights)
                particles = particles[idx]
                # Jitter regularizado (Liu-West leve) para evitar empobrecimento de partículas
                particles = particles + self.rng.normal(0.0, process_noise_std * 0.15, size=(n, d))
                weights = np.full(n, 1.0 / n, dtype=np.float64)
                resample_steps.append(step_idx)

            mean_t = np.sum(particles * weights[:, None], axis=0)
            var_t = np.sum(((particles - mean_t) ** 2) * weights[:, None], axis=0)
            posterior_means.append([round(float(v), 5) for v in mean_t])
            posterior_vars.append([round(float(v), 5) for v in var_t])

        modes_final = self.extract_modes(particles, weights, dim=0)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "SMC_PARTICLE_FILTER_COMPLETED",
            "scenario": scenario,
            "num_particles": n,
            "state_dim": d,
            "steps_processed": int(len(obs_arr)),
            "resample_count": len(resample_steps),
            "resample_steps": resample_steps,
            "min_neff": round(min(neff_history), 2) if neff_history else float(n),
            "final_neff": neff_history[-1] if neff_history else float(n),
            "final_posterior_mean": posterior_means[-1] if posterior_means else [0.0] * d,
            "final_posterior_var": posterior_vars[-1] if posterior_vars else [0.0] * d,
            "final_dominant_modes_dim0": modes_final,
            "multimodal_detected": len(modes_final) >= 2,
            "elapsed_ms": round(elapsed_ms, 3),
        }
