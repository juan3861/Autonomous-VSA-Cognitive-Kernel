"""Topological Data Analysis (TDA) & Persistent Homology (H0/H1) Barcode Engine.

Organ 58 do Substrato Cognitivo Não-LLM (AetherCOS v5.4).
Analisa a estrutura topológica invariante e a conectividade multiescalar de espaços latentes
e nuvens de pontos através da filtração de Vietoris-Rips:
- Mantém estruturas Disjoint-Set (Union-Find) com timestamps de nascimento para rastrear
  a evolução de componentes conexas em H_0 ao longo da escala de filtração epsilon;
- Gera diagramas de persistência exatos e códigos de barra (barcodes) [birth, death);
- Identifica transições de fase topológicas e separação de clusters via salto de tempo de vida max(death - birth);
- Calcula a Entropia de Persistência Topológica (Atienza et al., 2020) E_pers = -sum p_i log2(p_i)
  como assinatura compacta de complexidade estrutural invariante a deformações contínuas;
- Detecta geradores de ciclos topológicos H_1 em 1-esqueleto grafal em tempo O(E log V).
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class _DisjointSetForest:
    """Estrutura Union-Find com rank e tracking de tempo de nascimento."""

    def __init__(self, n: int):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.birth = [0.0] * n
        self.birth_id = list(range(n))

    def find(self, i: int) -> int:
        root = i
        while root != self.parent[root]:
            root = self.parent[root]
        curr = i
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
        return root

    def union(self, i: int, j: int, epsilon: float) -> Optional[Dict[str, Any]]:
        root_i = self.find(i)
        root_j = self.find(j)
        if root_i == root_j:
            return None  # Cria um 1-ciclo topológico (H_1)

        # Critério de persistência: componente que nasceu primeiro sobrevive
        # Em empate, componente de menor ID sobrevive
        if (self.birth[root_i], self.birth_id[root_i]) <= (self.birth[root_j], self.birth_id[root_j]):
            survivor, dead = root_i, root_j
        else:
            survivor, dead = root_j, root_i

        death_event = {
            "component_id": self.birth_id[dead],
            "birth": round(self.birth[dead], 6),
            "death": round(epsilon, 6),
            "lifetime": round(epsilon - self.birth[dead], 6),
            "merged_into": self.birth_id[survivor],
        }

        # União por rank
        if self.rank[survivor] < self.rank[dead]:
            self.parent[survivor] = dead
            # Mas preserva nascimento do survivor
            self.birth[dead] = self.birth[survivor]
            self.birth_id[dead] = self.birth_id[survivor]
        else:
            self.parent[dead] = survivor
            if self.rank[survivor] == self.rank[dead]:
                self.rank[survivor] += 1

        return death_event


class TopologicalPersistenceHomologyEngine:
    """
    Motor de Homologia Persistente e Análise Topológica de Dados (TDA) Vietoris-Rips.
    """

    def __init__(self):
        pass

    @staticmethod
    def _pairwise_distances(points: np.ndarray) -> np.ndarray:
        diff = points[:, None, :] - points[None, :, :]
        return np.sqrt(np.maximum(np.sum(diff * diff, axis=2), 0.0))

    def compute_persistence_diagram(
        self,
        point_cloud: Optional[List[List[float]] | np.ndarray] = None,
        distance_matrix: Optional[List[List[float]] | np.ndarray] = None,
        max_epsilon: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calcula a filtração de Vietoris-Rips para H_0 e candidatos a 1-ciclos H_1.
        Retorna barcodes, entropia de persistência e intervalos persistentes dominantes.
        """
        t0 = time.perf_counter()

        if distance_matrix is not None:
            D = np.asarray(distance_matrix, dtype=np.float64)
            n = D.shape[0]
            assert D.shape == (n, n), "Matriz de distâncias deve ser quadrada"
        elif point_cloud is not None:
            pts = np.asarray(point_cloud, dtype=np.float64)
            if pts.ndim == 1:
                pts = pts.reshape(-1, 1)
            n = len(pts)
            D = self._pairwise_distances(pts)
        else:
            raise ValueError("Deve ser fornecido point_cloud ou distance_matrix")

        if n < 2:
            return {
                "status": "TOPOLOGICAL_DEGENERATE_SINGLE_POINT",
                "n_points": n,
                "intervals_h0": [[0.0, None]],
                "persistence_entropy": 0.0,
                "elapsed_us": round((time.perf_counter() - t0) * 1e6, 2),
            }

        # 1. Coleta e ordena todas as arestas
        edges: List[Tuple[float, int, int]] = []
        for i in range(n):
            for j in range(i + 1, n):
                edges.append((float(D[i, j]), i, j))
        edges.sort(key=lambda e: e[0])

        d_max = float(edges[-1][0]) if edges else 1.0
        limit_eps = float(max_epsilon) if max_epsilon is not None else (d_max * 1.5)

        # 2. Executa filtração de Vietoris-Rips com Union-Find
        dsu = _DisjointSetForest(n)
        h0_intervals: List[Dict[str, Any]] = []
        h1_cycle_births: List[float] = []

        for dist, u, v in edges:
            if dist > limit_eps:
                break
            event = dsu.union(u, v, dist)
            if event is not None:
                h0_intervals.append(event)
            else:
                h1_cycle_births.append(round(dist, 6))

        # A última componente viva persiste indefinidamente (lifetime infinito)
        root_inf = dsu.find(0)
        h0_intervals.append({
            "component_id": dsu.birth_id[root_inf],
            "birth": round(dsu.birth[root_inf], 6),
            "death": None,
            "lifetime": float("inf"),
            "merged_into": None,
        })

        # 3. Métricas Topológicas: Entropia de Persistência e Salto Máximo
        finite_lifetimes = [it["lifetime"] for it in h0_intervals if it["death"] is not None]
        total_life = sum(finite_lifetimes)
        entropy = 0.0
        if total_life > 1e-12:
            for l in finite_lifetimes:
                if l > 1e-12:
                    p = l / total_life
                    entropy -= p * math.log2(p)

        max_persistence = max(finite_lifetimes) if finite_lifetimes else 0.0
        h0_intervals_sorted = sorted(
            [it for it in h0_intervals if it["death"] is not None],
            key=lambda it: it["lifetime"],
            reverse=True,
        )

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "PERSISTENCE_HOMOLOGY_COMPUTED",
            "n_points": n,
            "n_edges_filtered": len(edges),
            "h0_components_born": n,
            "h0_deaths_recorded": len(finite_lifetimes),
            "h1_cycle_births_count": len(h1_cycle_births),
            "max_h0_persistence_lifetime": round(max_persistence, 6),
            "persistence_entropy": round(entropy, 5),
            "dominant_persistent_features": h0_intervals_sorted[:5],
            "elapsed_us": round(elapsed_us, 2),
        }
