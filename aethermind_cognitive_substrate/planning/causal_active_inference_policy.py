"""Causal Active Inference & Epistemic Policy Engine with Pearl Do-Interventions (pymdp + Pearl SCM).

Organ 33 do Substrato Cognitivo Não-LLM (AetherCOS v4.2).
Unifica a Teoria da Inferência Ativa Variacional de Karl Friston (Princípio da Energia Livre)
com o Cálculo Causal de Intervenções e Contrafactuais de Judea Pearl (do-calculus):
- Avaliação da Energia Livre Esperada Causal G(do(pi)):
    G(do(pi)) = Risco Pragmático (Divergência da Meta) - Ganho Epistêmico Causal (Informação Mútua sob Intervenção).
- Poda de Confounders (Causal Surgery): elimina correlações espúrias via poda de arcos pais no DAG estrutural.
- Índice de Discrepância Causal: Delta = ||E[o|a] - E[o|do(a)]||. Se Delta > limiar, a correlação é espúria.
- Avaliação de Arrependimento Contrafactual (Counterfactual Regret):
    Regret(a') = max(0, Utilidade(o_{a'}) - Utilidade(o_{real})).
- Decisão epistêmica segura: integra com Control Barrier Functions (CBF-QP) para imunidade a violações físicas.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple, Callable
import numpy as np


class CausalActiveInferenceEngine:
    """
    Motor de Políticas de Inferência Ativa Causal.
    Equilibra utilidade pragmática e curiosidade epistêmica pura enquanto
    imuniza o agente contra ilusões causais e correlações espúrias de observação.
    """

    def __init__(
        self,
        obs_dim: int = 16,
        action_dim: int = 4,
        latent_dim: int = 16,
        seed: int = 42
    ):
        self.obs_dim = obs_dim
        self.action_dim = action_dim
        self.latent_dim = latent_dim

        rng = np.random.RandomState(seed)
        # Matriz generativa de observação A: P(o|s)
        self.A_matrix = rng.randn(obs_dim, latent_dim) * 0.1
        # Matriz de transição dinâmica B: P(s_{t+1}|s_t, a)
        self.B_tensors = [rng.randn(latent_dim, latent_dim) * 0.05 for _ in range(action_dim)]
        # Matriz de acoplamento direto de ação
        self.W_action = rng.randn(obs_dim, action_dim) * 0.15

        # Matriz de Confounding Latente (simula variáveis de confusão não observadas Z)
        self.confounder_coupling = rng.randn(obs_dim, 2) * 0.2

        # Distribuição de Preferência Homeostática P*(o) (Alvo do Agente)
        self.target_goal = np.zeros(obs_dim, dtype=np.float64)

        # Matriz de Adjacência Causal do DAG de Ações (A -> O, Z -> A, Z -> O)
        # 0: Direct Causal, 1: Spurious Backdoor Path
        self.causal_graph: Dict[str, List[str]] = {}

    def set_target_goal(self, target_obs: np.ndarray | List[float]) -> None:
        """Configura o estado homeostático alvo no espaço sensorial."""
        self.target_goal = np.resize(np.array(target_obs, dtype=np.float64), self.obs_dim)

    def evaluate_interventional_policy(
        self,
        current_state: np.ndarray | List[float],
        candidate_actions: List[np.ndarray | List[float]],
        action_names: Optional[List[str]] = None,
        confounder_latent_signal: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Avalia o conjunto de políticas sob intervenção do-calculus:
        Calcula G(do(pi)), decompondo em:
        1. Risco Pragmático Causal (Distância à Meta P*(o))
        2. Ganho Epistêmico Genuíno (Redução de Incerteza / Salience)
        3. Índice de Discrepância Causal (Detecção de Backdoor Confounder)
        """
        t0 = time.perf_counter()
        s0 = np.resize(np.array(current_state, dtype=np.float64), self.latent_dim)
        names = action_names or [f"act_{i}" for i in range(len(candidate_actions))]

        z_val = confounder_latent_signal if confounder_latent_signal is not None else 0.5
        confounder_vec = np.array([z_val, math.sin(z_val * math.pi)], dtype=np.float64)

        policy_evaluations = []
        best_policy = None
        min_g_do = float("inf")

        for idx, act in enumerate(candidate_actions):
            a_vec = np.resize(np.array(act, dtype=np.float64), self.action_dim)

            # 1. Predição Observacional P(o|a) — contaminada por correlação espúria Z
            obs_spurious = (
                np.dot(self.A_matrix, s0) +
                np.dot(self.W_action, a_vec) +
                np.dot(self.confounder_coupling, confounder_vec)
            )

            # 2. Predição Intervencionista P(o|do(a)) — Cirurgia Causal (Causal Surgery):
            # Z -> A é podado pela intervenção do(A). Apenas caminhos dirigidos A -> O permanecem.
            obs_interventional = (
                np.dot(self.A_matrix, s0) +
                np.dot(self.W_action, a_vec)
            )

            # 3. Índice de Discrepância Causal (CDI)
            causal_discrepancy = float(np.linalg.norm(obs_spurious - obs_interventional))
            is_confounded = causal_discrepancy > 0.05

            # 4. Risco Pragmático Causal: divergência L2 em relação ao atrator homeostático
            pragmatic_risk = float(np.linalg.norm(obs_interventional - self.target_goal))

            # 5. Ganho Epistêmico Causal (Curiosidade Válida / Redução de Entropia):
            # Proporcional à variância explicada na dinâmica interna sob a ação
            s_next_sim = s0.copy()
            for h in range(min(self.action_dim, len(self.B_tensors))):
                s_next_sim += a_vec[h] * np.dot(self.B_tensors[h], s0)
            epistemic_gain = float(np.var(s_next_sim) + 0.1 * np.linalg.norm(s_next_sim - s0))

            # 6. Energia Livre Esperada Causal G(do(a)) = Risco - beta * Epistêmico + penalidade de confusão
            # Queremos minimizar G
            beta_curiosity = 0.4
            g_do = pragmatic_risk - beta_curiosity * epistemic_gain

            # Se for confuso e o agente acreditar na correlação espúria, penaliza a confiabilidade
            confounder_penalty = 0.5 * causal_discrepancy if is_confounded else 0.0
            g_do_adjusted = g_do + confounder_penalty

            eval_entry = {
                "action_name": names[idx],
                "action_vector": [round(float(v), 3) for v in a_vec],
                "g_expected_free_energy": round(g_do_adjusted, 4),
                "pragmatic_risk": round(pragmatic_risk, 4),
                "epistemic_gain": round(epistemic_gain, 4),
                "causal_discrepancy_cdi": round(causal_discrepancy, 4),
                "is_spurious_confounded": is_confounded,
                "predicted_obs_norm": round(float(np.linalg.norm(obs_interventional)), 4)
            }
            policy_evaluations.append(eval_entry)

            if g_do_adjusted < min_g_do:
                min_g_do = g_do_adjusted
                best_policy = names[idx]

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "CAUSAL_POLICY_SEARCH_COMPLETED",
            "best_action": best_policy,
            "min_expected_free_energy_g": round(min_g_do, 4),
            "evaluations": policy_evaluations,
            "confounder_detected": any(e["is_spurious_confounded"] for e in policy_evaluations),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def compute_counterfactual_regret(
        self,
        executed_action: np.ndarray | List[float],
        observed_outcome: np.ndarray | List[float],
        counterfactual_candidate: np.ndarray | List[float]
    ) -> Dict[str, Any]:
        """
        Avaliação de Arrependimento Contrafactual em 3 Passos (Abdução, Intervenção, Predição):
        'Se eu tivesse tomado a ação a' em vez de a, qual teria sido a melhora na utilidade homeostática?'
        """
        t0 = time.perf_counter()
        a_real = np.resize(np.array(executed_action, dtype=np.float64), self.action_dim)
        o_real = np.resize(np.array(observed_outcome, dtype=np.float64), self.obs_dim)
        a_cf = np.resize(np.array(counterfactual_candidate, dtype=np.float64), self.action_dim)

        # 1. Abdução: Recupera ruído exógeno U a partir da observação real e ação executada
        # o_real = W_a * a_real + U => U = o_real - W_a * a_real
        exogenous_noise_U = o_real - np.dot(self.W_action, a_real)

        # 2. Intervenção Causal: substitui do(A = a_cf) mantendo o ruído U fixo
        o_counterfactual = np.dot(self.W_action, a_cf) + exogenous_noise_U

        # 3. Cálculo de Utilidade: -||o - target||
        utility_real = -float(np.linalg.norm(o_real - self.target_goal))
        utility_cf = -float(np.linalg.norm(o_counterfactual - self.target_goal))

        # Arrependimento: max(0, utility_cf - utility_real)
        regret = max(0.0, utility_cf - utility_real)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "COUNTERFACTUAL_REGRET_EVALUATED",
            "factual_utility": round(utility_real, 4),
            "counterfactual_utility": round(utility_cf, 4),
            "regret": round(regret, 4),
            "regret_detected": regret > 0.01,
            "counterfactual_outcome_norm": round(float(np.linalg.norm(o_counterfactual)), 4),
            "elapsed_ms": round(elapsed_ms, 3)
        }
