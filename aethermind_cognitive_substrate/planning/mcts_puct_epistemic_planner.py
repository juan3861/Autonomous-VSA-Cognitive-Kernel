"""AlphaZero PUCT Epistemic Monte Carlo Tree Search Planner (Silver et al. / MuZero Inspiration).

Organ 40 do Substrato Cognitivo Não-LLM (AetherCOS v4.4).
Implementa Busca em Árvore de Monte Carlo guiada pela fórmula Predictor + Upper Confidence
Bound applied to Trees (PUCT) operando sobre o espaço latente contínuo:
- Regra de Seleção PUCT:
    a* = argmax_a [ Q(s, a) + c_puct * P(s, a) * sqrt( sum_b N(s, b) ) / (1 + N(s, a)) ]
- Expansão e Avaliação de Valor Latente:
    Utiliza dinâmica preditiva rápida para simular transições s' = f(s, a) e avaliar
    V(s') = -||s' - s_goal||_2 + beta * Ganho_Epistêmico.
- Backpropagation de Árvore (Não-Gradiente):
    Atualiza incrementalmente N(s, a) <- N(s, a) + 1 e W(s, a) <- W(s, a) + V,
    Q(s, a) = W(s, a) / N(s, a).
- Distribuição de Política Temperada:
    pi(a|s_0) proporcional a N(s_0, a)^(1/tau).
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class _MCTSNode:
    __slots__ = ("state", "prior_p", "visit_count", "value_sum", "children")

    def __init__(self, state: np.ndarray, prior_p: float = 1.0):
        self.state = state
        self.prior_p = prior_p
        self.visit_count: int = 0
        self.value_sum: float = 0.0
        self.children: Dict[int, "_MCTSNode"] = {}

    @property
    def q_value(self) -> float:
        return self.value_sum / self.visit_count if self.visit_count > 0 else 0.0


class MCTSPUCTEpistemicPlanner:
    """
    Planejador Tático de Longo Horizonte via Árvore de Busca de Monte Carlo (PUCT)
    no espaço latente contínuo, sem uso de LLMs.
    """

    def __init__(
        self,
        state_dim: int = 16,
        action_dim: int = 4,
        c_puct: float = 1.414,
        max_depth: int = 4
    ):
        self.state_dim = state_dim
        self.action_dim = action_dim
        self.c_puct = c_puct
        self.max_depth = max_depth

        # Catálogo discreto canônico de macro-ações vetoriais em R^4
        self.action_catalog = [
            np.array([0.25, 0.0, 0.0, 0.0]),
            np.array([0.0, 0.25, 0.0, 0.0]),
            np.array([0.0, 0.0, 0.25, 0.0]),
            np.array([0.0, 0.0, 0.0, 0.25]),
            np.array([0.20, 0.20, 0.20, 0.20]),
            np.array([-0.15, -0.15, -0.15, -0.15]),
        ]

    def _transition_and_value(
        self,
        state: np.ndarray,
        action: np.ndarray,
        goal: np.ndarray
    ) -> Tuple[np.ndarray, float]:
        """Simula um passo latente determinístico e avalia a utilidade + bônus epistêmico."""
        next_state = state.copy()
        k = len(action)
        for i in range(self.state_dim):
            next_state[i] = 0.92 * state[i] + action[i % k]

        dist = float(np.linalg.norm(next_state - goal))
        epistemic_bonus = 0.05 * float(np.std(next_state - state))
        # Valor normalizado em [-1, 1]
        value = math.tanh(-dist + epistemic_bonus)
        return next_state, value

    def search(
        self,
        root_state: List[float] | np.ndarray,
        goal_state: List[float] | np.ndarray,
        num_simulations: int = 64,
        candidate_actions: Optional[List[List[float] | np.ndarray]] = None
    ) -> Dict[str, Any]:
        """
        Executa `num_simulations` simulações PUCT completas (Select -> Expand -> Evaluate -> Backup)
        e retorna a ação ótima que maximiza as visitas da raiz N(s_0, a).
        """
        t0 = time.perf_counter()
        s0 = np.resize(np.array(root_state, dtype=np.float64), self.state_dim)
        g = np.resize(np.array(goal_state, dtype=np.float64), self.state_dim)

        actions = (
            [np.resize(np.array(a, dtype=np.float64), self.action_dim) for a in candidate_actions]
            if candidate_actions
            else self.action_catalog
        )
        n_actions = len(actions)

        root = _MCTSNode(s0, prior_p=1.0)
        total_nodes_expanded = 1

        # Calcula prior inicial P(s, a) via alinhamento direcional com (goal - state)
        def _compute_priors(st: np.ndarray) -> np.ndarray:
            diff = g - st
            scores = np.zeros(n_actions, dtype=np.float64)
            for idx_a, act in enumerate(actions):
                tiled_act = np.resize(act, self.state_dim)
                scores[idx_a] = float(np.dot(diff, tiled_act))
            scores_shifted = scores - np.max(scores)
            exps = np.exp(scores_shifted)
            return exps / (np.sum(exps) + 1e-12)

        for _ in range(num_simulations):
            node = root
            search_path = [node]
            depth = 0

            # 1. SELECT: Desce pela árvore maximizando o escore PUCT
            while node.children and depth < self.max_depth:
                total_n = sum(ch.visit_count for ch in node.children.values())
                sqrt_total = math.sqrt(max(1, total_n))

                best_act_idx = -1
                best_puct = -1e18
                for act_idx, child in node.children.items():
                    u_score = self.c_puct * child.prior_p * (sqrt_total / (1.0 + child.visit_count))
                    puct_score = child.q_value + u_score
                    if puct_score > best_puct:
                        best_puct = puct_score
                        best_act_idx = act_idx

                node = node.children[best_act_idx]
                search_path.append(node)
                depth += 1

            # 2. EXPAND & EVALUATE
            if depth < self.max_depth and not node.children:
                priors = _compute_priors(node.state)
                best_leaf_val = -1e18
                for act_idx, act in enumerate(actions):
                    next_st, val = self._transition_and_value(node.state, act, g)
                    node.children[act_idx] = _MCTSNode(next_st, prior_p=float(priors[act_idx]))
                    total_nodes_expanded += 1
                    if val > best_leaf_val:
                        best_leaf_val = val
                leaf_value = best_leaf_val
            else:
                _, leaf_value = self._transition_and_value(node.state, np.zeros(self.action_dim), g)

            # 3. BACKUP: Propaga o valor de volta até a raiz
            for path_node in reversed(search_path):
                path_node.visit_count += 1
                path_node.value_sum += leaf_value

        # Seleciona a ação na raiz com maior contagem de visitas N(s_0, a)
        visit_counts = [root.children[i].visit_count if i in root.children else 0 for i in range(n_actions)]
        q_values = [round(root.children[i].q_value, 5) if i in root.children else 0.0 for i in range(n_actions)]
        best_idx = int(np.argmax(visit_counts))
        best_action_vec = actions[best_idx]

        total_visits = max(1, sum(visit_counts))
        policy_probs = [round(v / total_visits, 4) for v in visit_counts]
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "MCTS_PUCT_OPTIMAL_ACTION_FOUND",
            "best_action_index": best_idx,
            "best_action_vector": [round(float(v), 4) for v in best_action_vec],
            "root_best_q_value": q_values[best_idx],
            "root_visit_counts": visit_counts,
            "policy_distribution": policy_probs,
            "simulations_executed": num_simulations,
            "tree_nodes_expanded": total_nodes_expanded,
            "elapsed_ms": round(elapsed_ms, 3)
        }
