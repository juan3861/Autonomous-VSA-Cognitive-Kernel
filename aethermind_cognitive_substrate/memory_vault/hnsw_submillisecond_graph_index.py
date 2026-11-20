import time
import math
import heapq
import ctypes
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# ==============================================================================
# AETHERMIND HNSW SUB-MILLISECOND HIERARCHICAL SMALL-WORLD GRAPH INDEX
# Órgão 29 do Substrato Cognitivo Soberano (Inspirado em hnswlib / Qdrant)
# ==============================================================================
# Implementa o grafo navegável de mundo pequeno em múltiplas camadas hierárquicas
# (Malkov & Yashunin, IEEE TPAMI 2018) para busca aproximada/exata de vizinhos
# mais próximos em complexidade logarítmica O(log N).
# Acoplado à Memória Virtual Paginada OS para recuperação associativa semântica
# instantânea sobre milhares de páginas sem varredura linear.
# 100% Determinístico, 0 tokens, matemática vetorial pura.
# ==============================================================================

class HNSWNode:
    """Nó individual no grafo multi-camada HNSW."""
    def __init__(self, node_id: str, vector: np.ndarray, max_layer: int, payload: Any = None):
        self.node_id = node_id
        self.vector = vector
        self.max_layer = max_layer
        self.payload = payload
        # Conexões por camada: layer -> lista de node_ids vizinhos
        self.neighbors: Dict[int, List[str]] = {l: [] for l in range(max_layer + 1)}


class HNSWSubMillisecondGraphIndex:
    """
    Motor de Indexação e Busca Logarítmica HNSW (Hierarchical Navigable Small World).
    """
    def __init__(self, dim: int = 32, M: int = 12, ef_construction: int = 32, ef_search: int = 32):
        self.dim = dim
        self.M = M
        self.M_max0 = M * 3
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.m_L = 1.0 / math.log(max(2, M))

        self.nodes: Dict[str, HNSWNode] = {}
        self.entry_point_id: Optional[str] = None
        self.max_level: int = -1
        self._rng_counter: int = 1
        self.total_queries: int = 0

        # Vinculação opcional com Kernel Rust Bare-Metal AVX2 (aether_cortex_vsa.dll)
        self.is_native_accelerated = False
        self._rust_dist_fn = None
        dll_path = Path("F:/AetherMind_Apotheosis_Final/aether_cortex_vsa/target/release/aether_cortex_vsa.dll")
        if dll_path.exists():
            try:
                dll = ctypes.CDLL(str(dll_path))
                fn = getattr(dll, "hnsw_cosine_distance_f32", None)
                if fn is not None:
                    fn.argtypes = [
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.c_size_t
                    ]
                    fn.restype = ctypes.c_float
                    self._rust_dist_fn = fn
                    self.is_native_accelerated = True
            except Exception:
                self.is_native_accelerated = False

    def _deterministic_level(self) -> int:
        """Sorteia deterministicamente o nível máximo do nó com decaimento exponencial."""
        # Gerador congruencial linear determinístico em [0.001, 0.999]
        self._rng_counter = (self._rng_counter * 1664525 + 1013904223) & 0xFFFFFFFF
        u = max(1e-5, min(0.9999, float(self._rng_counter) / 4294967296.0))
        level = int(-math.log(u) * self.m_L)
        return min(level, 6)  # Limite superior seguro de 6 camadas

    @staticmethod
    def _normalize(v: np.ndarray) -> np.ndarray:
        norm = float(np.linalg.norm(v))
        if norm < 1e-12:
            return np.ascontiguousarray(v, dtype=np.float32)
        return np.ascontiguousarray((v / norm), dtype=np.float32)

    def _distance(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """Distância de cosseno em [0, 2]: d = 1.0 - dot(v1_norm, v2_norm)."""
        if self.is_native_accelerated and self._rust_dist_fn is not None:
            p1 = v1.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            p2 = v2.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            return float(self._rust_dist_fn(p1, p2, self.dim))
        return max(0.0, 1.0 - float(np.dot(v1, v2)))

    def _search_layer(self, q_vec: np.ndarray, ep_id: str, ef: int, layer: int) -> Tuple[List[Tuple[float, str]], int]:
        """
        Executa busca gulosa / feixe na camada `layer` a partir do ponto de entrada `ep_id`.
        Retorna lista ordenada de (distância, node_id) e número de avaliações de distância.
        """
        visited = {ep_id}
        d_ep = self._distance(q_vec, self.nodes[ep_id].vector)
        # candidates: min-heap (dist, id)
        candidates = [(d_ep, ep_id)]
        # results: max-heap (-dist, id) para manter os ef melhores
        results = [(-d_ep, ep_id)]
        dist_evals = 1

        while candidates:
            c_dist, c_id = heapq.heappop(candidates)
            furthest_dist = -results[0][0]

            if c_dist > furthest_dist and len(results) >= ef:
                break

            c_node = self.nodes[c_id]
            for nb_id in c_node.neighbors.get(layer, []):
                if nb_id not in visited and nb_id in self.nodes:
                    visited.add(nb_id)
                    d_nb = self._distance(q_vec, self.nodes[nb_id].vector)
                    dist_evals += 1
                    furthest_dist = -results[0][0]

                    if d_nb < furthest_dist or len(results) < ef:
                        heapq.heappush(candidates, (d_nb, nb_id))
                        heapq.heappush(results, (-d_nb, nb_id))
                        if len(results) > ef:
                            heapq.heappop(results)

        sorted_res = sorted([(-neg_d, nid) for neg_d, nid in results], key=lambda x: x[0])
        return sorted_res, dist_evals

    def insert(self, node_id: str, vector: List[float], payload: Any = None) -> Dict[str, Any]:
        """Insere um novo vetor no grafo multi-camada HNSW."""
        t0 = time.perf_counter()
        arr = np.resize(np.array(vector, dtype=np.float32), self.dim)
        arr = self._normalize(arr)

        level = self._deterministic_level()
        new_node = HNSWNode(node_id, arr, level, payload)
        self.nodes[node_id] = new_node

        if self.entry_point_id is None:
            self.entry_point_id = node_id
            self.max_level = level
            return {
                "status": "HNSW_FIRST_NODE_INSERTED",
                "node_id": node_id,
                "assigned_level": level,
                "elapsed_us": round((time.perf_counter() - t0) * 1e6, 2)
            }

        curr_ep = self.entry_point_id
        # Fase 1: Desce das camadas superiores (max_level até level + 1) com ef=1 (zoom-in guloso)
        for lc in range(self.max_level, level, -1):
            res, _ = self._search_layer(arr, curr_ep, ef=1, layer=lc)
            if res:
                curr_ep = res[0][1]

        # Fase 2: Conecta nas camadas min(max_level, level) até 0
        for lc in range(min(self.max_level, level), -1, -1):
            res, _ = self._search_layer(arr, curr_ep, ef=self.ef_construction, layer=lc)
            m_limit = self.M_max0 if lc == 0 else self.M
            selected = [nid for _, nid in res if nid != node_id][:m_limit]

            new_node.neighbors[lc] = list(selected)
            for nb_id in selected:
                nb_node = self.nodes[nb_id]
                if lc not in nb_node.neighbors:
                    nb_node.neighbors[lc] = []
                if node_id not in nb_node.neighbors[lc]:
                    nb_node.neighbors[lc].append(node_id)
                    # Poda preservando atalhos de longo alcance (Small-World Diversity Heuristic)
                    if len(nb_node.neighbors[lc]) > m_limit * 2:
                        nb_node.neighbors[lc].sort(
                            key=lambda cand_id: self._distance(nb_node.vector, self.nodes[cand_id].vector)
                        )
                        # Mantém os mais próximos + 2 conexões de longo alcance para evitar ilhas
                        nb_node.neighbors[lc] = nb_node.neighbors[lc][:m_limit - 2] + nb_node.neighbors[lc][-2:]

            if res:
                curr_ep = res[0][1]

        if level > self.max_level:
            self.max_level = level
            self.entry_point_id = node_id

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "HNSW_NODE_INSERTED",
            "node_id": node_id,
            "assigned_level": level,
            "max_graph_level": self.max_level,
            "total_nodes": len(self.nodes),
            "elapsed_us": round(elapsed_us, 2)
        }

    def search_knn(self, query_vector: List[float], k: int = 3) -> Dict[str, Any]:
        """
        Busca os Top-K vizinhos mais próximos em tempo logarítmico O(log N).
        """
        t0 = time.perf_counter()
        if not self.nodes or self.entry_point_id is None:
            return {"status": "EMPTY_INDEX", "matches": [], "distance_evaluations": 0}

        q_arr = np.resize(np.array(query_vector, dtype=np.float32), self.dim)
        q_arr = self._normalize(q_arr)

        curr_ep = self.entry_point_id
        total_evals = 0

        # Fase 1: Zoom-in guloso nas camadas superiores (max_level até 1)
        for lc in range(self.max_level, 0, -1):
            res, evals = self._search_layer(q_arr, curr_ep, ef=1, layer=lc)
            total_evals += evals
            if res:
                curr_ep = res[0][1]

        # Fase 2: Busca refinada na camada base 0 com ef = max(ef_search, k)
        res0, evals0 = self._search_layer(q_arr, curr_ep, ef=max(self.ef_search, k), layer=0)
        total_evals += evals0

        top_k = res0[:k]
        matches = []
        for dist, nid in top_k:
            node = self.nodes[nid]
            matches.append({
                "node_id": nid,
                "cosine_similarity": round(1.0 - dist, 6),
                "distance": round(dist, 6),
                "layer": node.max_layer,
                "payload": node.payload
            })

        self.total_queries += 1
        elapsed_us = (time.perf_counter() - t0) * 1e6
        n_total = len(self.nodes)
        speedup_vs_linear = round(float(n_total) / max(1.0, float(total_evals)), 2)

        return {
            "status": "HNSW_SEARCH_COMPLETED",
            "top_k": k,
            "matches": matches,
            "total_nodes_indexed": n_total,
            "distance_evaluations": total_evals,
            "graph_speedup_ratio": speedup_vs_linear,
            "max_hierarchy_level": self.max_level,
            "elapsed_us": round(elapsed_us, 2)
        }
