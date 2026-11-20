"""STRIPS / SAS+ Fast State-Space Planning Engine (AetherMind Cognitive Substrate).

Área 10: Planejamento Deliberativo & Busca em Espaço de Estados (PDDL).
Gera planos sequenciais matematicamente garantidos a partir de um estado inicial,
conjunto de ações com pré-condições/efeitos e uma meta declarativa, usando A*.
"""
from __future__ import annotations

import heapq
import time
from typing import Dict, Any, List, Set, Tuple, Optional, FrozenSet


class Action:
    def __init__(self, name: str, preconditions: Set[str], add_effects: Set[str],
                 del_effects: Set[str], cost: float = 1.0):
        self.name = name
        self.preconditions = frozenset(preconditions)
        self.add_effects = frozenset(add_effects)
        self.del_effects = frozenset(del_effects)
        self.cost = cost

    def is_applicable(self, state: FrozenSet[str]) -> bool:
        return self.preconditions.issubset(state)

    def apply(self, state: FrozenSet[str]) -> FrozenSet[str]:
        return (state - self.del_effects) | self.add_effects


class FastStateSpacePlanner:
    """Planejador de Estados STRIPS baseado em A* com Heurística Admissível."""

    def __init__(self):
        self.actions: List[Action] = []

    def add_action(self, name: str, preconditions: Set[str], add_effects: Set[str],
                   del_effects: Set[str], cost: float = 1.0) -> None:
        self.actions.append(Action(name, preconditions, add_effects, del_effects, cost))

    def _heuristic(self, state: FrozenSet[str], goal: FrozenSet[str]) -> float:
        """Heurística de Contagem de Metas Faltantes (Goal-Count Admissible)."""
        missing = len(goal - state)
        return float(missing)

    def plan(self, initial_state: Set[str], goal_state: Set[str], max_nodes: int = 5000) -> Dict[str, Any]:
        """Calcula o plano ótimo usando A*."""
        start_time = time.perf_counter()
        init_froz = frozenset(initial_state)
        goal_froz = frozenset(goal_state)

        if goal_froz.issubset(init_froz):
            return {
                "status": "ALREADY_SATISFIED",
                "plan": [],
                "plan_cost": 0.0,
                "nodes_expanded": 0,
                "elapsed_ms": round((time.perf_counter() - start_time) * 1000.0, 3)
            }

        # Fila de Prioridade: (f_score, g_score, state_counter, current_state, path_actions)
        frontier = []
        counter = 0
        h_init = self._heuristic(init_froz, goal_froz)
        heapq.heappush(frontier, (h_init, 0.0, counter, init_froz, []))

        g_scores: Dict[FrozenSet[str], float] = {init_froz: 0.0}
        nodes_expanded = 0

        while frontier and nodes_expanded < max_nodes:
            f, g, _, current_state, path = heapq.heappop(frontier)
            nodes_expanded += 1

            if goal_froz.issubset(current_state):
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                return {
                    "status": "PLAN_FOUND",
                    "plan": path,
                    "plan_steps_count": len(path),
                    "plan_cost": g,
                    "nodes_expanded": nodes_expanded,
                    "final_state": list(current_state),
                    "elapsed_ms": round(elapsed_ms, 3)
                }

            for act in self.actions:
                if act.is_applicable(current_state):
                    next_state = act.apply(current_state)
                    new_g = g + act.cost

                    if next_state not in g_scores or new_g < g_scores[next_state]:
                        g_scores[next_state] = new_g
                        h = self._heuristic(next_state, goal_froz)
                        counter += 1
                        heapq.heappush(frontier, (new_g + h, new_g, counter, next_state, path + [act.name]))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return {
            "status": "UNREACHABLE_OR_EXHAUSTED",
            "plan": None,
            "nodes_expanded": nodes_expanded,
            "elapsed_ms": round(elapsed_ms, 3),
            "reason": f"Nenhum caminho válido encontrado até a meta em {nodes_expanded} estados expandidos."
        }
