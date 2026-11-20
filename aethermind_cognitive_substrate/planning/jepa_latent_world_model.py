"""Joint Embedding Predictive Architecture (JEPA) Latent World Model.

Área 05: Modelos Mundiais Contínuos, Não-Generativos e Simulação Mental Deliberativa.
Inspirado na arquitetura JEPA de Yann LeCun (Meta AI / Courant Institute) e nos avanços
do I-JEPA / V-JEPA (Assran et al., CVPR 2023).

Princípio Fundamental:
Modelos generativos (LLMs autorregressivos ou diffusion) gastam 99% da computação
tentando prever cada pixel irrelevante ou token de texto, levando a alucinações e lentidão.
O JEPA NÃO gera pixels ou texto: ele prevê diretamente no ESPAÇO LATENTE ABSTRATO:
    s_hat_{t+1} = Predictor(s_t, a_t)

Prevenção de Colapso Representacional:
Usa um Target Encoder atualizado via Exponential Moving Average (EMA):
    theta_bar <- tau * theta_bar + (1 - tau) * theta
eliminando a necessidade de contrastes negativos e garantindo que o espaço latente
permaneça estruturado e matematicamente diferenciável.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class JEPAPredictiveWorldModel:
    """Modelo Mundial Latente JEPA com Simulação Mental em Microssegundos."""

    def __init__(
        self,
        obs_dim: int = 16,
        action_dim: int = 8,
        latent_dim: int = 32,
        ema_tau: float = 0.98,
        learning_rate: float = 0.01,
        seed: int = 42
    ):
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.latent_dim = latent_dim
        self.ema_tau = ema_tau
        self.lr = learning_rate

        rng = np.random.RandomState(seed)

        # Context Encoder E_theta: obs_dim -> latent_dim
        self.W_enc = rng.randn(latent_dim, obs_dim) * math.sqrt(2.0 / obs_dim)
        self.b_enc = np.zeros(latent_dim, dtype=np.float64)

        # Target Encoder E_theta_bar (EMA): inicializado igual ao Context Encoder
        self.W_enc_target = np.copy(self.W_enc)
        self.b_enc_target = np.copy(self.b_enc)

        # Latent Predictor P_phi: (latent_dim + action_dim) -> latent_dim
        pred_in = latent_dim + action_dim
        self.W_pred1 = rng.randn(latent_dim, pred_in) * math.sqrt(2.0 / pred_in)
        self.b_pred1 = np.zeros(latent_dim, dtype=np.float64)
        self.W_pred2 = rng.randn(latent_dim, latent_dim) * math.sqrt(2.0 / latent_dim)
        self.b_pred2 = np.zeros(latent_dim, dtype=np.float64)

        # Telemetria
        self.train_steps = 0
        self.recent_losses: List[float] = []

    def _activate(self, x: np.ndarray) -> np.ndarray:
        """Ativação suave GELU."""
        return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * np.power(x, 3))))

    def _layer_norm(self, x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
        """Normalização de camada para estabilidade no espaço de embedding."""
        mean = np.mean(x)
        var = np.var(x)
        return (x - mean) / math.sqrt(var + eps)

    def encode_context(self, obs: np.ndarray) -> np.ndarray:
        """Codifica observação atual no espaço latente s_t."""
        x = np.resize(obs.astype(np.float64), self.obs_dim)
        linear = np.dot(self.W_enc, x) + self.b_enc
        latent = self._layer_norm(self._activate(linear))
        return latent

    def encode_target(self, obs: np.ndarray) -> np.ndarray:
        """Codifica observação alvo s_{t+1} usando o Target Encoder (EMA)."""
        x = np.resize(obs.astype(np.float64), self.obs_dim)
        linear = np.dot(self.W_enc_target, x) + self.b_enc_target
        latent = self._layer_norm(self._activate(linear))
        return latent

    def predict_next_latent(self, latent_s: np.ndarray, action: np.ndarray) -> np.ndarray:
        """Prediz próximo estado latente s_hat_{t+1} a partir de (s_t, a_t)."""
        a = np.resize(action.astype(np.float64), self.action_dim)
        inp = np.concatenate([latent_s, a])
        h1 = self._layer_norm(self._activate(np.dot(self.W_pred1, inp) + self.b_pred1))
        # Conexão residual no preditor: s_hat = s_t + F(s_t, a_t)
        res = np.dot(self.W_pred2, h1) + self.b_pred2
        s_hat = self._layer_norm(latent_s + res)
        return s_hat

    def step_train(
        self,
        obs_t: np.ndarray,
        action_t: np.ndarray,
        obs_t1: np.ndarray
    ) -> float:
        """Executa 1 passo de otimização auto-supervisionada JEPA."""
        s_t = self.encode_context(obs_t)
        s_target = self.encode_target(obs_t1)
        s_hat = self.predict_next_latent(s_t, action_t)

        # Distância suave L2 e cosseno
        norm_hat = np.linalg.norm(s_hat) + 1e-8
        norm_tar = np.linalg.norm(s_target) + 1e-8
        cosine_sim = float(np.dot(s_hat, s_target) / (norm_hat * norm_tar))
        l2_dist = float(np.linalg.norm(s_hat - s_target))

        loss = (1.0 - cosine_sim) + 0.1 * l2_dist

        # Gradiente analítico aproximado com respeito ao preditor
        err = (s_hat - s_target)
        a = np.resize(action_t.astype(np.float64), self.action_dim)
        inp = np.concatenate([s_t, a])

        # Atualização dos pesos do preditor (gradiente estocástico)
        grad_W2 = np.outer(err, self._layer_norm(self._activate(np.dot(self.W_pred1, inp) + self.b_pred1)))
        self.W_pred2 -= self.lr * np.clip(grad_W2, -1.0, 1.0)
        self.b_pred2 -= self.lr * np.clip(err, -1.0, 1.0)

        # Atualização do Context Encoder
        grad_W_enc = np.outer(np.dot(self.W_pred2.T, err)[:self.latent_dim], obs_t)
        self.W_enc -= self.lr * 0.5 * np.clip(grad_W_enc, -1.0, 1.0)

        # Atualização do Target Encoder via EMA (sem gradiente direto)
        self.W_enc_target = self.ema_tau * self.W_enc_target + (1.0 - self.ema_tau) * self.W_enc
        self.b_enc_target = self.ema_tau * self.b_enc_target + (1.0 - self.ema_tau) * self.b_enc

        self.train_steps += 1
        self.recent_losses.append(loss)
        if len(self.recent_losses) > 100:
            self.recent_losses.pop(0)

        return loss

    def mental_rollout(
        self,
        current_obs: np.ndarray,
        action_sequence: List[np.ndarray],
        goal_obs: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """Simula mentalmente trajetórias no espaço latente em microssegundos."""
        t0 = time.perf_counter()
        s_current = self.encode_context(current_obs)

        goal_latent = None
        if goal_obs is not None:
            goal_latent = self.encode_target(goal_obs)

        latent_trajectory = [s_current]
        step_alignments = []
        cumulative_value = 0.0
        gamma = 0.95

        for step_idx, action in enumerate(action_sequence):
            s_next = self.predict_next_latent(s_current, action)
            latent_trajectory.append(s_next)

            if goal_latent is not None:
                norm_next = np.linalg.norm(s_next) + 1e-8
                norm_goal = np.linalg.norm(goal_latent) + 1e-8
                cos_sim = float(np.dot(s_next, goal_latent) / (norm_next * norm_goal))
                step_alignments.append(cos_sim)
                cumulative_value += (gamma ** step_idx) * cos_sim

            s_current = s_next

        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "ROLLOUT_COMPLETE",
            "horizon_steps": len(action_sequence),
            "elapsed_microseconds": round(elapsed_us, 2),
            "final_latent_norm": round(float(np.linalg.norm(s_current)), 4),
            "goal_cumulative_value": round(cumulative_value, 4) if goal_obs is not None else None,
            "mean_goal_alignment": round(float(np.mean(step_alignments)), 4) if step_alignments else None,
            "trajectory_depth": len(latent_trajectory)
        }

    def select_best_action_plan(
        self,
        current_obs: np.ndarray,
        candidate_plans: List[List[np.ndarray]],
        goal_obs: np.ndarray
    ) -> Tuple[int, Dict[str, Any]]:
        """Usa Model Predictive Control (MPC) latente para escolher o plano com menor energia livre."""
        best_idx = 0
        best_val = -float("inf")
        best_telemetry = {}

        for idx, plan in enumerate(candidate_plans):
            sim = self.mental_rollout(current_obs, plan, goal_obs)
            val = sim["goal_cumulative_value"] or 0.0
            if val > best_val:
                best_val = val
                best_idx = idx
                best_telemetry = sim

        return best_idx, best_telemetry
