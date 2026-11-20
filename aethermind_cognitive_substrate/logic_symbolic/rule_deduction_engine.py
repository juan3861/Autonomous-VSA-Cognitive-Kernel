"""Horn Clause & Datalog Rule Deduction Engine (AetherMind Cognitive Substrate).

Área 01 & 03: Raciocínio Relacional, Dedução Lógica e Fecho Transitivo.
Permite inferir fatos, verificar regras de segurança e derivar intenções
sem redes neurais por meio de resolução de cláusulas de Horn e unificação.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Set, Tuple, Optional


class Fact:
    def __init__(self, predicate: str, *args: str):
        self.predicate = predicate
        self.args = tuple(args)

    def __eq__(self, other):
        return isinstance(other, Fact) and self.predicate == other.predicate and self.args == other.args

    def __hash__(self):
        return hash((self.predicate, self.args))

    def __repr__(self):
        return f"{self.predicate}({', '.join(self.args)})"


class Rule:
    def __init__(self, head: Fact, body: List[Fact]):
        self.head = head
        self.body = body

    def __repr__(self):
        return f"{self.head} :- {', '.join(str(b) for b in self.body)}"


class RuleDeductionEngine:
    """Motor de Dedução por Encademaneto para Frente e para Trás (Forward/Backward Chaining)."""

    def __init__(self):
        self.facts: Set[Fact] = set()
        self.rules: List[Rule] = []

    def add_fact(self, predicate: str, *args: str) -> None:
        self.facts.add(Fact(predicate, *args))

    def add_rule(self, head: Tuple[str, Tuple[str, ...]], body: List[Tuple[str, Tuple[str, ...]]]) -> None:
        rule_head = Fact(head[0], *head[1])
        rule_body = [Fact(b[0], *b[1]) for b in body]
        self.rules.append(Rule(rule_head, rule_body))

    def forward_chain(self, max_iterations: int = 100) -> Dict[str, Any]:
        """Calcula o fecho dedutivo completo a partir dos fatos e regras conhecidos."""
        start = time.perf_counter()
        known_facts = set(self.facts)
        derived_steps = []

        for iteration in range(max_iterations):
            new_facts_in_round = set()
            for rule in self.rules:
                # Checa se todos os fatos do corpo da regra estão satisfeitos
                # Suporte a regras proposicionais/instanciadas
                if all(b in known_facts for b in rule.body):
                    if rule.head not in known_facts:
                        new_facts_in_round.add(rule.head)
                        derived_steps.append({
                            "derived": str(rule.head),
                            "by_rule": str(rule),
                            "iteration": iteration + 1
                        })

            if not new_facts_in_round:
                break
            known_facts.update(new_facts_in_round)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {
            "status": "COMPLETED",
            "initial_facts_count": len(self.facts),
            "total_facts_count": len(known_facts),
            "new_facts_derived": len(known_facts) - len(self.facts),
            "deduced_facts": [str(f) for f in known_facts],
            "derivation_log": derived_steps,
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def prove_goal(self, predicate: str, *args: str) -> Dict[str, Any]:
        """Verifica se um objetivo pode ser provado logicamente (Backward Chaining)."""
        start = time.perf_counter()
        goal = Fact(predicate, *args)
        visited = set()
        proof_tree = []

        def _backward(current_goal: Fact, path: List[Fact]) -> bool:
            if current_goal in self.facts:
                proof_tree.append(f"Axioma/Fato Base: {current_goal}")
                return True
            if current_goal in path:
                return False  # Evita ciclos infinitos

            for rule in self.rules:
                if rule.head == current_goal:
                    all_subgoals_proven = True
                    for sub in rule.body:
                        if not _backward(sub, path + [current_goal]):
                            all_subgoals_proven = False
                            break
                    if all_subgoals_proven:
                        proof_tree.append(f"Regra Aplicada: {rule}")
                        return True
            return False

        is_proven = _backward(goal, [])
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "goal": str(goal),
            "is_proven": is_proven,
            "proof_trace": proof_tree,
            "elapsed_ms": round(elapsed_ms, 3)
        }
