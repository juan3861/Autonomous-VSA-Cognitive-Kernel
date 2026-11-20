"""DAG Task Decomposer & Dependency Engine (AetherMind Cognitive Substrate).

Área 10: Planejamento Deliberativo, Síntese de Ações e Decomposição de Metas.
Decompõe objetivos complexos em um Grafo Acíclico Dirigido (DAG), identifica
o caminho crítico, detecta ciclos impossíveis e calcula níveis de execução paralela.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx


class TaskNode:
    def __init__(self, task_id: str, description: str, estimated_duration_ms: float = 10.0,
                 preconditions: Optional[Set[str]] = None, effects: Optional[Set[str]] = None):
        self.task_id = task_id
        self.description = description
        self.estimated_duration_ms = estimated_duration_ms
        self.preconditions = preconditions or set()
        self.effects = effects or set()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "estimated_duration_ms": self.estimated_duration_ms,
            "preconditions": list(self.preconditions),
            "effects": list(self.effects)
        }


class DAGTaskDecomposer:
    """Orquestrador e Decompositor de Tarefas por Grafo de Dependências."""

    def __init__(self):
        self.graph = nx.DiGraph()
        self.tasks: Dict[str, TaskNode] = {}

    def add_task(
        self,
        task_id: str,
        description: str,
        dependencies: Optional[List[str]] = None,
        duration_ms: float = 10.0,
        preconditions: Optional[Set[str]] = None,
        effects: Optional[Set[str]] = None
    ) -> None:
        """Adiciona uma tarefa e suas arestas de dependência ao grafo."""
        node = TaskNode(task_id, description, duration_ms, preconditions, effects)
        self.tasks[task_id] = node
        self.graph.add_node(task_id, data=node)

        if dependencies:
            for dep in dependencies:
                self.graph.add_edge(dep, task_id)

    def validate_and_schedule(self) -> Dict[str, Any]:
        """Valida aciclicidade e calcula a ordem de execução com estágios paralelos."""
        start = time.perf_counter()

        # 1. Checagem de Ciclos
        if not nx.is_directed_acyclic_graph(self.graph):
            cycle = nx.find_cycle(self.graph, orientation="original")
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "is_valid": False,
                "error": "Ciclo de dependência impossível detectado no plano!",
                "cycle": [(u, v) for u, v, _ in cycle],
                "elapsed_ms": round(elapsed_ms, 3)
            }

        # 2. Ordem Topológica Estrita
        topo_order = list(nx.topological_sort(self.graph))

        # 3. Cálculo de Níveis Paralelos (Topological Generations)
        parallel_generations = [list(gen) for gen in nx.topological_generations(self.graph)]

        # 4. Cálculo do Caminho Crítico (Longest Path baseado na duração)
        # Inverte os pesos para calcular o caminho mais longo em DAG
        for u, v in self.graph.edges():
            self.graph[u][v]["weight"] = self.tasks[u].estimated_duration_ms

        # Adiciona nós virtuais source e target para achar o caminho crítico
        source_nodes = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
        sink_nodes = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]

        critical_path = []
        max_duration = 0.0

        for src in source_nodes:
            for snk in sink_nodes:
                try:
                    paths = list(nx.all_simple_paths(self.graph, src, snk))
                    for path in paths:
                        path_dur = sum(self.tasks[node_id].estimated_duration_ms for node_id in path)
                        if path_dur > max_duration:
                            max_duration = path_dur
                            critical_path = path
                except nx.NetworkXNoPath:
                    continue

        # 5. Verificação Causal de Pré-condições / Efeitos
        world_state = set()
        causal_violations = []
        for task_id in topo_order:
            node = self.tasks[task_id]
            missing_preconditions = node.preconditions - world_state
            if missing_preconditions:
                causal_violations.append({
                    "task_id": task_id,
                    "missing_preconditions": list(missing_preconditions)
                })
            world_state.update(node.effects)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "is_valid": len(causal_violations) == 0,
            "tasks_count": len(self.tasks),
            "topological_sequence": topo_order,
            "parallel_stages": parallel_generations,
            "critical_path": critical_path,
            "critical_path_duration_ms": max_duration,
            "causal_violations": causal_violations,
            "elapsed_ms": round(elapsed_ms, 3)
        }
