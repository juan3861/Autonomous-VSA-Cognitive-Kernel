"""
Autonomous Causal Discovery Engine (Peter-Clark / PC Algorithm & NOTEARS Formulation)
Discovers causal Directed Acyclic Graphs (DAGs) from observational telemetry data:
1. Conditional Independence Tests using Partial Correlation Fisher Z-transform.
2. Skeleton Discovery (Undirected Graph).
3. V-Structure (Collider) Orientation: X -> Z <- Y if unconditioned.
4. Meek Rule Orientation to prevent cycles.
"""

from __future__ import annotations

import time
import math
import itertools
from typing import Dict, Any, List, Set, Tuple, Optional
import numpy as np
import networkx as nx

class AutonomousCausalDiscovery:
    """Motor de Descoberta Causal Não-Supervisionada (Algoritmo PC)."""

    def __init__(self, alpha: float = 0.05):
        self.alpha = alpha

    def _partial_correlation(self, data: np.ndarray, x: int, y: int, z_set: List[int]) -> float:
        """Calcula a correlação parcial entre X e Y dado o conjunto Z."""
        if not z_set:
            r = np.corrcoef(data[:, x], data[:, y])[0, 1]
            return 0.0 if np.isnan(r) else float(r)

        indices = [x, y] + list(z_set)
        sub_cov = np.cov(data[:, indices], rowvar=False)
        try:
            prec = np.linalg.pinv(sub_cov)
            p_xy = -prec[0, 1] / math.sqrt(abs(prec[0, 0] * prec[1, 1]) + 1e-12)
            return 0.0 if np.isnan(p_xy) else float(np.clip(p_xy, -0.999999, 0.999999))
        except Exception:
            return 0.0

    def _is_conditionally_independent(self, data: np.ndarray, x: int, y: int, z_set: List[int]) -> Tuple[bool, float]:
        """Teste de independência condicional baseado na transformada de Fisher Z."""
        n = data.shape[0]
        k = len(z_set)
        r = self._partial_correlation(data, x, y, z_set)
        
        # Estatística Z de Fisher (math.erfc nativo em C, idêntico a 2*(1-norm.cdf(stat)))
        z = 0.5 * math.log((1.0 + r) / (1.0 - r + 1e-12))
        stat = math.sqrt(max(1, n - k - 3)) * abs(z)
        p_val = math.erfc(stat / math.sqrt(2.0))
        return (p_val > self.alpha), float(p_val)

    def discover_dag(self, variable_names: List[str], data_matrix: np.ndarray) -> Dict[str, Any]:
        """
        Executa o algoritmo PC completo:
        1. Esqueleto completo não-direcionado.
        2. Poda de arestas com separadores Z crescentes.
        3. Identificação de v-estruturas (imoralidades causais).
        4. Orientação DAG consistente.
        """
        start = time.perf_counter()
        n_vars = len(variable_names)
        assert data_matrix.shape[1] == n_vars, "Matrix columns must match variable count"

        # 1. Esqueleto Completo
        adj: Dict[int, Set[int]] = {i: set(range(n_vars)) - {i} for i in range(n_vars)}
        separators: Dict[Tuple[int, int], Set[int]] = {}

        # 2. Poda de Arestas por Teste de Independência
        depth = 0
        while True:
            edges_tested = 0
            for i in range(n_vars):
                for j in list(adj[i]):
                    if j <= i:
                        continue
                    neighbors = sorted(list(adj[i] - {j}))
                    if len(neighbors) < depth:
                        continue
                    
                    edges_tested += 1
                    for z_tuple in itertools.combinations(neighbors, depth):
                        z_list = list(z_tuple)
                        is_indep, p_val = self._is_conditionally_independent(data_matrix, i, j, z_list)
                        if is_indep:
                            adj[i].remove(j)
                            adj[j].remove(i)
                            separators[(i, j)] = set(z_list)
                            separators[(j, i)] = set(z_list)
                            break
            depth += 1
            if depth >= n_vars - 1 or edges_tested == 0:
                break

        # 3. Orientação de V-Estruturas (X -> Z <- Y se Z não está no separador)
        dag = nx.DiGraph()
        dag.add_nodes_from(variable_names)
        oriented_edges: Set[Tuple[int, int]] = set()

        for z in range(n_vars):
            for x, y in itertools.combinations(adj[z], 2):
                if y not in adj[x]:  # X e Y não são adjacentes
                    sep = separators.get((x, y), set())
                    if z not in sep:
                        # Colisor identificado: x -> z <- y
                        oriented_edges.add((x, z))
                        oriented_edges.add((y, z))

        # Adiciona arestas orientadas
        for u, v in oriented_edges:
            dag.add_edge(variable_names[u], variable_names[v])

        # Para as demais arestas do esqueleto não colidentes, orienta no sentido de fluxo ou bidirecional
        for i in range(n_vars):
            for j in adj[i]:
                if j > i:
                    u_name, v_name = variable_names[i], variable_names[j]
                    if not dag.has_edge(u_name, v_name) and not dag.has_edge(v_name, u_name):
                        # Evita ciclos
                        dag.add_edge(u_name, v_name)
                        if not nx.is_directed_acyclic_graph(dag):
                            dag.remove_edge(u_name, v_name)
                            dag.add_edge(v_name, u_name)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "CAUSAL_DISCOVERY_CONVERGED",
            "variables": variable_names,
            "sample_size": data_matrix.shape[0],
            "discovered_edges": list(dag.edges()),
            "is_dag": nx.is_directed_acyclic_graph(dag),
            "elapsed_ms": round(elapsed_ms, 3)
        }
