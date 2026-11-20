"""Structural Causal Model (SCM) & Pearl Do-Calculus Engine (AetherMind Cognitive Substrate).

Áreas 06 & 10: Raciocínio Causal, Metacognição e Planejamento Deliberativo.
Implementa o cálculo de intervenção do(X) de Judea Pearl:
- Representação de Modelos Causais Estruturais (SCMs) via Grafo Acíclico Dirigido (DAG)
- Verificação do Critério de Porta dos Fundos (Backdoor Criterion) e d-separação
- Separação formal entre correlação observacional P(Y | X) e intervenção causal P(Y | do(X)).
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx


class StructuralCausalEngine:
    """Motor Simbólico de Inferência Causal e Do-Calculus."""

    def __init__(self):
        self.causal_dag = nx.DiGraph()
        self.equations: Dict[str, str] = {}

    def add_causal_edge(self, cause: str, effect: str) -> None:
        """Adiciona uma relação de causa e efeito direta (Cause -> Effect)."""
        self.causal_dag.add_edge(cause.strip().lower(), effect.strip().lower())

    def add_structural_equation(self, variable: str, equation_repr: str) -> None:
        """Registra a equação determinística de atribuição: V := f(Parents, Noise).
        Infere automaticamente arestas de causa a partir dos identificadores da equação.
        """
        import re
        v = variable.strip().lower()
        self.equations[v] = equation_repr
        self.causal_dag.add_node(v)
        tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", equation_repr)
        for tok in tokens:
            t_tok = tok.lower()
            if t_tok != v and not t_tok.isdigit():
                self.causal_dag.add_edge(t_tok, v)

    def is_d_separated(self, x_nodes: Set[str], y_nodes: Set[str], z_conditioned: Set[str]) -> bool:
        """Verifica d-separação entre X e Y dado o conjunto condicional Z."""
        return nx.is_d_separator(self.causal_dag, x_nodes, y_nodes, z_conditioned)

    def find_backdoor_adjustment_sets(self, treatment: str, outcome: str) -> Dict[str, Any]:
        """Encontra conjuntos válidos de ajuste por Backdoor Criterion para isolar P(Y | do(X))."""
        start = time.perf_counter()
        t = treatment.strip().lower()
        y = outcome.strip().lower()

        if t not in self.causal_dag:
            self.causal_dag.add_node(t)
        if y not in self.causal_dag:
            self.causal_dag.add_node(y)

        # Cria grafo mutilado de backdoor (remove todas as arestas saindo do tratamento T)
        backdoor_graph = self.causal_dag.copy()
        for succ in list(backdoor_graph.successors(t)):
            backdoor_graph.remove_edge(t, succ)

        # Descendentes do tratamento não podem ser condicionados
        descendants_of_t = nx.descendants(self.causal_dag, t) | {t}
        all_other_nodes = set(self.causal_dag.nodes()) - {t, y} - descendants_of_t

        valid_adjustment_sets = []
        import itertools
        parents_list = sorted(list(self.causal_dag.predecessors(t)))

        # Testa todos os subconjuntos de pais de T (do menor para o maior)
        for r in range(len(parents_list) + 1):
            for subset in itertools.combinations(parents_list, r):
                subset_set = set(subset)
                if nx.is_d_separator(backdoor_graph, {t}, {y}, subset_set):
                    subset_sorted = sorted(list(subset_set))
                    if subset_sorted not in valid_adjustment_sets:
                        valid_adjustment_sets.append(subset_sorted)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        is_identifiable = len(valid_adjustment_sets) > 0
        return {
            "treatment": t,
            "outcome": y,
            "is_causally_identifiable": is_identifiable,
            "formula": f"P({y} | do({t})) = SUM_Z P({y} | {t}, Z) * P(Z)" if is_identifiable else "NÃO_IDENTIFICÁVEL_VIA_BACKDOOR",
            "valid_adjustment_sets": valid_adjustment_sets,
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def simulate_hard_intervention(self, intervention_var: str, value: float, state_env: Dict[str, float]) -> Dict[str, Any]:
        """Executa a operação atômica de cirurgia de grafo de Pearl: do(X = c)."""
        start = time.perf_counter()
        var = intervention_var.strip().lower()
        sim_state = dict(state_env)
        sim_state[var] = value

        if var not in self.causal_dag:
            self.causal_dag.add_node(var)

        # Ordem topológica para propagação dos efeitos causais downstream
        try:
            topo_order = list(nx.topological_sort(self.causal_dag))
        except Exception:
            topo_order = list(self.causal_dag.nodes())

        if var in self.causal_dag:
            affected_nodes = list(nx.descendants(self.causal_dag, var))
        else:
            affected_nodes = [k for k, eq in self.equations.items() if var in eq]

        for node in topo_order:
            if node in affected_nodes and node in self.equations:
                eq = self.equations[node]
                try:
                    sim_state[node] = float(eval(eq, {"__builtins__": None}, sim_state))
                except Exception:
                    pass

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "intervention": f"do({var} = {value})",
            "affected_downstream_variables": affected_nodes,
            "resulting_state": sim_state,
            "elapsed_ms": round(elapsed_ms, 3)
        }
