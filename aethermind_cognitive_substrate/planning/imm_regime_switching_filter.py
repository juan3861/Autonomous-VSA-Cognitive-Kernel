"""Interacting Multiple Model (IMM) Hybrid Regime-Switching Bayesian Filter.

Organ 53 do Substrato Cognitivo Não-LLM (AetherCOS v5.2).
Implementa o algoritmo canônico IMM (Blom & Bar-Shalom, IEEE TAC 1988) para rastreamento
ótimo em sistemas híbridos com troca estocástica de regime operacional:
- Mantém M modelos dinâmicos acoplados por matriz de transição Markoviana Pi_{ij}:
  * Modo 0 (NominalSteady): dinâmica suave / baixa incerteza de processo Q_0;
  * Modo 1 (AgileManeuver): dinâmica de aceleração / salto rápido com alta variância Q_1;
- Ciclo IMM completo em 4 estágios por instante t:
  1. Interação / Mixing (probabilidades condicionadas mu_{i|j} e mistura de momentos com
     termo de espalhamento das médias);
  2. Predição & Atualização de Kalman por modo + verossimilhança Gaussiana de inovação;
  3. Atualização Bayesiana das probabilidades de modo mu_t^(j);
  4. Fusão combinada de estado x_hat_t e covariância P_t.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional
import numpy as np


class IMMRegimeSwitchingFilter:
    """
    Filtro Bayesiano Híbrido Interacting Multiple Model (IMM) com troca de regime Markoviana.
    """

    def __init__(
        self,
        dt: float = 0.1,
        transition_matrix: Optional[List[List[float]]] = None,
        obs_noise_std: float = 0.08,
    ):
        self.dt = float(dt)
        self.obs_noise_std = float(obs_noise_std)
        if transition_matrix is None:
            self.Pi = np.array([[0.94, 0.06], [0.10, 0.90]], dtype=np.float64)
        else:
            self.Pi = np.asarray(transition_matrix, dtype=np.float64)
        # Normaliza linhas para matriz estocástica válida
        self.Pi = self.Pi / np.sum(self.Pi, axis=1, keepdims=True)

        dt_val = self.dt
        # Matrizes de transição para estado 2D [posição, velocidade]
        self.F_models = [
            np.array([[1.0, dt_val], [0.0, 0.99]], dtype=np.float64),   # Modo 0: Nominal / Suave
            np.array([[1.0, dt_val], [0.0, 1.00]], dtype=np.float64),   # Modo 1: Manobra / Salto
        ]
        # Covariâncias de ruído de processo: baixa vs alta manobrabilidade
        self.Q_models = [
            np.array([[1e-4, 0.0], [0.0, 1e-4]], dtype=np.float64),
            np.array([[0.02, 0.01], [0.01, 0.35]], dtype=np.float64),
        ]
        self.H = np.array([[1.0, 0.0]], dtype=np.float64)
        self.R = np.array([[self.obs_noise_std ** 2]], dtype=np.float64)

    @staticmethod
    def _gaussian_likelihood(innov: float, S: float) -> float:
        S_safe = max(float(S), 1e-12)
        exponent = -0.5 * (innov * innov) / S_safe
        return max(math.exp(max(exponent, -500.0)) / math.sqrt(2.0 * math.pi * S_safe), 1e-300)

    def track_with_regime_detection(
        self,
        observations: List[float] | np.ndarray,
        maneuver_prob_threshold: float = 0.50,
    ) -> Dict[str, Any]:
        """
        Executa filtragem IMM sobre série escalar y_t, retornando trajetória estimada,
        probabilidades instantâneas de cada regime e instantes de detecção de manobra/salto.
        """
        t0 = time.perf_counter()
        y_arr = np.asarray(observations, dtype=np.float64).reshape(-1)
        num_modes = len(self.F_models)
        if len(y_arr) == 0:
            return {"status": "EMPTY_OBSERVATIONS", "steps": 0}

        mu = np.array([0.85, 0.15], dtype=np.float64)
        x_modes = [np.array([y_arr[0], 0.0], dtype=np.float64) for _ in range(num_modes)]
        P_modes = [np.eye(2, dtype=np.float64) * 0.25 for _ in range(num_modes)]

        fused_positions: List[float] = []
        fused_velocities: List[float] = []
        mode1_probs: List[float] = []
        maneuver_steps: List[int] = []
        nis_values: List[float] = []
        eye2 = np.eye(2, dtype=np.float64)

        for t_idx, z_t in enumerate(y_arr):
            # 1. Interação / Mixing entre modos
            c_bar = self.Pi.T @ mu
            c_bar = np.maximum(c_bar, 1e-12)
            mu_cond = np.zeros((num_modes, num_modes), dtype=np.float64)
            for i in range(num_modes):
                for j in range(num_modes):
                    mu_cond[i, j] = (self.Pi[i, j] * mu[i]) / c_bar[j]

            x0_mix = []
            P0_mix = []
            for j in range(num_modes):
                xj = sum(mu_cond[i, j] * x_modes[i] for i in range(num_modes))
                Pj = np.zeros((2, 2), dtype=np.float64)
                for i in range(num_modes):
                    diff = (x_modes[i] - xj).reshape(2, 1)
                    Pj += mu_cond[i, j] * (P_modes[i] + diff @ diff.T)
                x0_mix.append(xj)
                P0_mix.append(Pj)

            # 2. Predição & Atualização de Kalman em paralelo por modo
            likelihoods = np.zeros(num_modes, dtype=np.float64)
            step_nis = 0.0
            for j in range(num_modes):
                Fj = self.F_models[j]
                Qj = self.Q_models[j]
                x_pred = Fj @ x0_mix[j]
                P_pred = Fj @ P0_mix[j] @ Fj.T + Qj

                y_pred = float((self.H @ x_pred)[0])
                innov = float(z_t) - y_pred
                S = float((self.H @ P_pred @ self.H.T + self.R)[0, 0])
                S_safe = max(S, 1e-12)

                K = (P_pred @ self.H.T) / S_safe
                x_upd = x_pred + K.reshape(-1) * innov
                P_upd = (eye2 - K @ self.H) @ P_pred
                P_upd = 0.5 * (P_upd + P_upd.T)

                x_modes[j] = x_upd
                P_modes[j] = P_upd
                likelihoods[j] = self._gaussian_likelihood(innov, S_safe)
                step_nis += mu[j] * ((innov * innov) / S_safe)

            # 3. Atualização Bayesiana de probabilidades de regime
            unnorm_mu = likelihoods * c_bar
            total_mu = float(np.sum(unnorm_mu))
            if total_mu <= 1e-300:
                mu = np.array([0.5, 0.5], dtype=np.float64)
            else:
                mu = unnorm_mu / total_mu

            # 4. Fusão combinada de momentos
            x_fused = sum(mu[j] * x_modes[j] for j in range(num_modes))
            fused_positions.append(round(float(x_fused[0]), 5))
            fused_velocities.append(round(float(x_fused[1]), 5))
            prob_maneuver = float(mu[1])
            mode1_probs.append(round(prob_maneuver, 5))
            nis_values.append(round(float(step_nis), 4))
            if prob_maneuver >= maneuver_prob_threshold:
                maneuver_steps.append(t_idx)

        rmse_pos = float(np.sqrt(np.mean((np.array(fused_positions) - y_arr) ** 2)))
        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "IMM_HYBRID_REGIME_TRACKED",
            "steps_processed": int(len(y_arr)),
            "final_mode_probabilities": {
                "nominal_drift": round(float(mu[0]), 5),
                "agile_maneuver": round(float(mu[1]), 5),
            },
            "peak_maneuver_probability": round(max(mode1_probs), 5),
            "maneuver_steps_detected": maneuver_steps,
            "tracking_rmse_vs_raw_obs": round(rmse_pos, 5),
            "fused_final_state": [fused_positions[-1], fused_velocities[-1]],
            "mode1_probability_trace": mode1_probs,
            "elapsed_us": round(elapsed_us, 2),
        }
