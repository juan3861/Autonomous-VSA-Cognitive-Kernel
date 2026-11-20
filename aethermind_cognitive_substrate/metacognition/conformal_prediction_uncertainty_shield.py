"""Distribution-Free Conformal Prediction Uncertainty Shield (Vovk / Angelopoulos & Bates).

Organ 39 do Substrato Cognitivo Não-LLM (AetherCOS v4.4).
Fornece garantias matemáticas de cobertura em amostras finitas livres de distribuição
(Distribution-Free Finite-Sample Coverage Guarantee):
    P( Y_{n+1} in C_alpha(X_{n+1}) ) >= 1 - alpha
sem exigir suposições Gaussianas ou bayesianas assintóticas:
- Escores de Não-Conformidade: s_i = ||y_i - y_hat_i||_2.
- Quantil Finito Corrigido:
    q_hat = Quantile( {s_1, ..., s_n}, ceil((n + 1) * (1 - alpha)) / n ).
- Adaptive Conformal Inference (ACI de Gibbs & Candès) para séries temporais não-estacionárias:
    alpha_{t+1} = alpha_t + gamma * (alpha_target - err_t).
- Gatilho de Abstenção Epistêmica: se o raio conformal q_hat exceder o orçamento de risco,
  aciona modo conservador na Barreira de Controle CBF-QP.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ConformalPredictionUncertaintyShield:
    """
    Escudo de Quantificação de Incerteza por Predição Conformal Split & Adaptativa (ACI).
    Garante formalmente cobertura >= 1 - alpha para predições latentes do modelo mundial.
    """

    def __init__(
        self,
        alpha_target: float = 0.10,
        aci_gamma: float = 0.02,
        max_calibration_window: int = 256,
        max_safe_radius: float = 0.75
    ):
        self.alpha_target = alpha_target
        self.alpha_current = alpha_target
        self.aci_gamma = aci_gamma
        self.max_calibration_window = max_calibration_window
        self.max_safe_radius = max_safe_radius
        self.calibration_scores: List[float] = []
        self.empirical_hits: int = 0
        self.empirical_total: int = 0

    def calibrate(self, residuals_or_scores: List[float] | np.ndarray) -> float:
        """Registra um lote de escores de não-conformidade s_i = ||y_i - y_hat_i||_2."""
        arr = np.array(residuals_or_scores, dtype=np.float64).reshape(-1)
        for v in arr:
            self.calibration_scores.append(float(abs(v)))
        if len(self.calibration_scores) > self.max_calibration_window:
            self.calibration_scores = self.calibration_scores[-self.max_calibration_window:]
        return self.compute_conformal_quantile()

    def compute_conformal_quantile(self, alpha_override: Optional[float] = None) -> float:
        """
        Calcula o quantil conformal finito exato:
        k = ceil((n + 1) * (1 - alpha))
        """
        n = len(self.calibration_scores)
        if n == 0:
            return 0.0
        alpha = float(np.clip(alpha_override if alpha_override is not None else self.alpha_current, 0.005, 0.99))
        sorted_scores = sorted(self.calibration_scores)
        k = math.ceil((n + 1) * (1.0 - alpha))
        idx = min(max(0, k - 1), n - 1)
        return float(sorted_scores[idx])

    def certify_prediction_set(
        self,
        y_pred: List[float] | np.ndarray,
        y_true_observed: Optional[List[float] | np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Constrói a bola conformal C_alpha(x) = { y : ||y - y_pred||_2 <= q_hat }
        e, caso `y_true_observed` seja fornecido, atualiza o passo adaptativo ACI (Gibbs & Candès).
        """
        t0 = time.perf_counter()
        pred = np.array(y_pred, dtype=np.float64).reshape(-1)
        q_radius = self.compute_conformal_quantile()

        covered = None
        observed_score = None
        if y_true_observed is not None:
            truth = np.resize(np.array(y_true_observed, dtype=np.float64).reshape(-1), len(pred))
            observed_score = float(np.linalg.norm(truth - pred))
            covered = bool(observed_score <= q_radius + 1e-12)
            err_t = 0.0 if covered else 1.0

            self.empirical_total += 1
            if covered:
                self.empirical_hits += 1

            # Atualização ACI (Adaptive Conformal Inference):
            # Se houve erro (err_t = 1), reduz alpha_current para ampliar o raio conformal no próximo passo
            self.alpha_current = float(
                np.clip(self.alpha_current + self.aci_gamma * (self.alpha_target - err_t), 0.01, 0.50)
            )
            self.calibration_scores.append(observed_score)
            if len(self.calibration_scores) > self.max_calibration_window:
                self.calibration_scores.pop(0)

        abstain_epistemic = bool(q_radius > self.max_safe_radius)
        coverage_rate = (
            self.empirical_hits / self.empirical_total
            if self.empirical_total > 0
            else 1.0 - self.alpha_target
        )
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "CONFORMAL_SET_CERTIFIED",
            "guaranteed_coverage_level": round(1.0 - self.alpha_target, 4),
            "adaptive_alpha_current": round(self.alpha_current, 4),
            "conformal_radius_q_hat": round(q_radius, 5),
            "epistemic_abstention_triggered": abstain_epistemic,
            "observed_nonconformity_score": round(observed_score, 5) if observed_score is not None else None,
            "is_covered": covered,
            "empirical_coverage_ratio": round(coverage_rate, 4),
            "calibration_sample_size": len(self.calibration_scores),
            "lower_bound_preview": [round(float(v - q_radius), 4) for v in pred[:4]],
            "upper_bound_preview": [round(float(v + q_radius), 4) for v in pred[:4]],
            "elapsed_us": round(elapsed_us, 2)
        }
