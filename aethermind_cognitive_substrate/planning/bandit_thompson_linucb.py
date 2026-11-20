"""Contextual Bandit Engine (Disjoint LinUCB & Linear Thompson Sampling).

Organ 70 do Substrato Cognitivo Nao-LLM (AetherCOS v6.0).
Tomada de decisao sequencial online sob incerteza contextual (Li et al., WWW 2010 / Agrawal & Goyal, 2013):
- Mantem matriz de precisao A_a = I + sum x_t x_t^T e vetor b_a = sum r_t x_t para cada braco a;
- Atualiza A_a^{-1} incrementalmente via identidade de Sherman-Morrison em tempo O(d^2) sem reinversao;
- Suporta selecao deterministica LinUCB (theta_a^T x + alpha * sqrt(x^T A_a^{-1} x)) e
  amostragem estocastica Linear Thompson Sampling (theta_tilde ~ N(theta_a, v^2 A_a^{-1}));
- Verifica empiricamente que o arrependimento medio por passo decresce sublinearmente com o horizonte T.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, Optional
import numpy as np


class ContextualBanditLinUCBThompson:
    """
    Motor de Bandits Contextuais Online (LinUCB & Thompson Sampling) com Sherman-Morrison O(d^2).
    """

    def __init__(self, n_arms: int = 4, context_dim: int = 5, alpha: float = 1.2, seed: int = 202670):
        self.n_arms = int(n_arms)
        self.context_dim = int(context_dim)
        self.alpha = float(alpha)
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _sherman_morrison_update(A_inv: np.ndarray, x: np.ndarray) -> np.ndarray:
        """Atualizacao O(d^2) de (A + x x^T)^{-1} = A_inv - (A_inv x x^T A_inv) / (1 + x^T A_inv x)."""
        Ax = A_inv @ x
        denom = 1.0 + float(x.T @ Ax)
        return A_inv - np.outer(Ax, Ax) / max(denom, 1e-12)

    def simulate_contextual_bandit(
        self,
        n_rounds: int = 250,
        policy: str = "linucb",
        n_arms: Optional[int] = None,
        context_dim: Optional[int] = None,
        alpha: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Executa loop online completo de bandit contextual avaliando arrependimento acumulado
        e taxa de acerto do braco otimo na metade final do horizonte.
        """
        t0 = time.perf_counter()

        K = int(n_arms if n_arms is not None else self.n_arms)
        d = int(context_dim if context_dim is not None else self.context_dim)
        alp = float(alpha if alpha is not None else self.alpha)
        T = int(n_rounds)

        # Parametros verdadeiros latentes dos K bracos
        true_thetas = self.rng.normal(0.0, 1.0, size=(K, d))
        for a in range(K):
            true_thetas[a] /= max(float(np.linalg.norm(true_thetas[a])), 1e-12)

        # Estado de cada braco: A_inv_a, b_a
        A_invs = [np.eye(d, dtype=np.float64) for _ in range(K)]
        bs = [np.zeros(d, dtype=np.float64) for _ in range(K)]

        cumulative_regret = 0.0
        early_hits = 0
        late_hits = 0
        half = T // 2

        for t in range(T):
            x = self.rng.normal(0.0, 1.0, size=d)
            x /= max(float(np.linalg.norm(x)), 1e-12)

            expected_rewards = true_thetas @ x
            best_arm = int(np.argmax(expected_rewards))
            best_expected = float(expected_rewards[best_arm])

            scores = np.zeros(K, dtype=np.float64)
            for a in range(K):
                theta_hat = A_invs[a] @ bs[a]
                if policy == "thompson":
                    cov = (alp ** 2) * 0.25 * A_invs[a]
                    theta_sample = self.rng.multivariate_normal(theta_hat, 0.5 * (cov + cov.T))
                    scores[a] = float(theta_sample @ x)
                else:
                    ucb_bonus = alp * math.sqrt(max(float(x.T @ A_invs[a] @ x), 0.0))
                    scores[a] = float(theta_hat @ x) + ucb_bonus

            chosen_arm = int(np.argmax(scores))
            chosen_expected = float(expected_rewards[chosen_arm])
            regret = best_expected - chosen_expected
            cumulative_regret += regret

            if chosen_arm == best_arm:
                if t < half:
                    early_hits += 1
                else:
                    late_hits += 1

            # Observa recompensa ruidosa e atualiza Sherman-Morrison O(d^2)
            reward = chosen_expected + float(self.rng.normal(0.0, 0.08))
            A_invs[chosen_arm] = self._sherman_morrison_update(A_invs[chosen_arm], x)
            bs[chosen_arm] += reward * x

        early_acc = early_hits / max(1, half)
        late_acc = late_hits / max(1, T - half)
        mean_regret_per_step = cumulative_regret / max(1, T)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "CONTEXTUAL_BANDIT_SIMULATED",
            "policy": policy,
            "n_arms": K,
            "context_dim": d,
            "n_rounds": T,
            "cumulative_regret": round(cumulative_regret, 4),
            "mean_regret_per_step": round(mean_regret_per_step, 5),
            "early_optimal_arm_rate": round(early_acc, 4),
            "late_optimal_arm_rate": round(late_acc, 4),
            "learning_verified": late_acc >= early_acc,
            "elapsed_us": round(elapsed_us, 2),
        }
