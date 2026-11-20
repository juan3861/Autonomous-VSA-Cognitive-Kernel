"""Active Inference & Friston Variational Free Energy Engine (Predictive Coding / NGC).

Área 06 & 10: Raciocínio Termodinâmico, Cobertor de Markov e Aprendizado Local sem Backprop.
Implementa o Princípio da Energia Livre de Karl Friston (FEP) e Neural Generative Coding:
- Previsões descendentes (top-down): s_hat_l = W_l * s_{l+1}.
- Erros de predição locais ascendentes (bottom-up): e_l = s_l - s_hat_l.
- Minimização da Energia Livre Variacional F:
    F = sum_l (1/2) * (e_l^T * e_l) + D_KL[q(s) || p(s)].
- Plasticidade sináptica local Hebbiana (STDP modulado por erro):
    Delta W_l = eta * e_l * (s_{l+1})^T (sem propagação global de erro).
- Energia Livre Esperada G(pi) para seleção de ações:
    G(pi) = - Valor Epistêmico (Curiosidade / Ganho de Informação) - Valor Pragmático (Utilidade).
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ActiveInferenceFristonEngine:
    """Motor de Inferência Ativa e Codificação Preditiva com Energia Livre de Friston."""

    def __init__(
        self,
        obs_dim: int = 16,
        hidden_dim: int = 32,
        prior_dim: int = 16,
        learning_rate: float = 0.05
    ):
        self.obs_dim = obs_dim
        self.hidden_dim = hidden_dim
        self.prior_dim = prior_dim
        self.learning_rate = learning_rate

        rng = np.random.RandomState(42)
        # Pesos generativos top-down: Camada 2 -> Camada 1 -> Observação
        self.W_prior_to_hidden = rng.randn(hidden_dim, prior_dim) * 0.1
        self.W_hidden_to_obs = rng.randn(obs_dim, hidden_dim) * 0.1

        # Estados latentes atuais (representações internas)
        self.s_hidden = np.zeros(hidden_dim, dtype=np.float64)
        self.s_prior = np.zeros(prior_dim, dtype=np.float64)

        # Preferências pragmáticas do agente (alvo de sobrevivência / meta)
        self.target_observation = np.zeros(obs_dim, dtype=np.float64)

    def set_target_goal(self, target_obs: np.ndarray) -> None:
        """Define o atrator homeostático / meta do agente no espaço de observação."""
        self.target_observation = np.resize(target_obs.astype(np.float64), self.obs_dim)

    def compute_variational_free_energy(self, observation: np.ndarray) -> Tuple[float, np.ndarray, np.ndarray]:
        """Calcula a Energia Livre Variacional F e os erros de predição locais."""
        obs = np.resize(observation.astype(np.float64), self.obs_dim)

        # 1. Previsões top-down
        pred_hidden = np.dot(self.W_prior_to_hidden, self.s_prior)
        pred_obs = np.dot(self.W_hidden_to_obs, self.s_hidden)

        # 2. Erros de predição locais
        e_obs = obs - pred_obs
        e_hidden = self.s_hidden - pred_hidden

        # 3. Energia Livre F = 0.5 * ||e_obs||^2 + 0.5 * ||e_hidden||^2
        free_energy = float(0.5 * np.sum(e_obs ** 2) + 0.5 * np.sum(e_hidden ** 2))
        return free_energy, e_obs, e_hidden

    def infer_and_adapt(
        self,
        observation: np.ndarray,
        inference_steps: int = 25
    ) -> Dict[str, Any]:
        """Inferência perceptual rápida (atualiza s) seguida de plasticidade local (atualiza W)."""
        start = time.perf_counter()
        obs = np.resize(observation.astype(np.float64), self.obs_dim)

        initial_fe, _, _ = self.compute_variational_free_energy(obs)
        fe_trajectory = [round(initial_fe, 4)]

        # 1. Inferência Perceptual: Minimiza F em relação aos estados internos s_hidden
        dt_state = 0.1
        for _ in range(inference_steps):
            _, e_obs, e_hidden = self.compute_variational_free_energy(obs)
            # Gradiente descendente direto em F: ds/dt = W^T * e_obs - e_hidden
            grad_hidden = np.dot(self.W_hidden_to_obs.T, e_obs) - e_hidden
            self.s_hidden += dt_state * grad_hidden
            # Dinâmica lenta do prior
            self.s_prior += dt_state * 0.2 * np.dot(self.W_prior_to_hidden.T, e_hidden)

        final_fe, final_e_obs, final_e_hidden = self.compute_variational_free_energy(obs)
        fe_trajectory.append(round(final_fe, 4))

        # 2. Plasticidade Sináptica Local Hebbiana (Zero Backprop): Delta W = eta * e * s^T
        delta_w_obs = self.learning_rate * np.outer(final_e_obs, self.s_hidden)
        delta_w_hidden = self.learning_rate * np.outer(final_e_hidden, self.s_prior)

        self.W_hidden_to_obs += delta_w_obs
        self.W_prior_to_hidden += delta_w_hidden

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "FREE_ENERGY_MINIMIZED",
            "initial_free_energy": round(initial_fe, 4),
            "final_free_energy": round(final_fe, 4),
            "free_energy_reduction_pct": round(max(0.0, (initial_fe - final_fe) / (initial_fe + 1e-9) * 100.0), 2),
            "mean_prediction_error_obs": round(float(np.mean(np.abs(final_e_obs))), 5),
            "synaptic_update_norm": round(float(np.linalg.norm(delta_w_obs)), 5),
            "fe_trajectory": fe_trajectory,
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def evaluate_expected_free_energy_policy(
        self,
        candidate_actions: List[np.ndarray],
        action_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Calcula G(pi) para seleção de ação: equilibra Curiosidade Epistêmica e Valor Pragmático."""
        start = time.perf_counter()
        names = action_names or [f"action_{i}" for i in range(len(candidate_actions))]

        evaluated_policies = []
        best_policy = None
        min_g = float("inf")

        for idx, act in enumerate(candidate_actions):
            act_vec = np.resize(act.astype(np.float64), self.obs_dim)

            # Simula a observação predita sob esta ação
            simulated_obs = np.dot(self.W_hidden_to_obs, self.s_hidden) + 0.5 * act_vec

            # 1. Valor Pragmático: proximidade da observação simulada ao objetivo homeostático
            pragmatic_distance = float(np.linalg.norm(simulated_obs - self.target_observation))

            # 2. Valor Epistêmico (Curiosidade): divergência em relação à expectativa atual (ganho de informação)
            epistemic_novelty = float(np.var(simulated_obs))

            # G(pi) = Pragmatic_Loss - Epistemic_Bonus (queremos minimizar G)
            expected_free_energy = pragmatic_distance - 0.3 * epistemic_novelty

            evaluated_policies.append({
                "action_name": names[idx],
                "expected_free_energy_G": round(expected_free_energy, 4),
                "pragmatic_distance": round(pragmatic_distance, 4),
                "epistemic_novelty": round(epistemic_novelty, 4)
            })

            if expected_free_energy < min_g:
                min_g = expected_free_energy
                best_policy = names[idx]

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "OPTIMAL_ACTION_SELECTED",
            "best_action": best_policy,
            "min_expected_free_energy": round(min_g, 4),
            "evaluated_policies": evaluated_policies,
            "elapsed_ms": round(elapsed_ms, 3)
        }
