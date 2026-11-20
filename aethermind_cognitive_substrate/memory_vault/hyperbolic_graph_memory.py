"""Hyperbolic Poincaré Ball Graph Memory (AetherMind Cognitive Substrate).

Área 05: Memória Perene, Grafos Hierárquicos e Variedades Riemannianas.
Implementa a geometria hiperbólica do Disco de Poincaré (Poincaré Ball Model).
Em espaços hiperbólicos, a área e o volume crescem exponencialmente em relação ao raio,
permitindo acomodar árvores genealógicas e ontologias taxonômicas complexas
em dimensões reduzidas (d=2 ou d=8) com distorção de distância quase nula.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Tuple, Optional
import numpy as np


class PoincaréHyperbolicMemory:
    """Modelo de Memória Hiperbólica no Disco de Poincaré."""

    def __init__(self, dimension: int = 2, max_norm: float = 0.999):
        self.dimension = dimension
        self.max_norm = max_norm
        self.entity_embeddings: Dict[str, np.ndarray] = {}

    def _project_to_ball(self, vec: np.ndarray) -> np.ndarray:
        """Projeta qualquer vetor para dentro do disco aberto de Poincaré (norma < 1.0)."""
        norm = float(np.linalg.norm(vec))
        if norm >= self.max_norm:
            return vec * (self.max_norm / (norm + 1e-9))
        return vec

    def set_entity_embedding(self, entity_name: str, coordinates: List[float]) -> None:
        """Registra a coordenada hiperbólica de um conceito."""
        arr = np.array(coordinates, dtype=np.float64)
        if len(arr) != self.dimension:
            arr = np.resize(arr, self.dimension)
        self.entity_embeddings[entity_name.strip().lower()] = self._project_to_ball(arr)

    def hyperbolic_distance(self, vec_u: np.ndarray, vec_v: np.ndarray) -> float:
        """Calcula a métrica geodésica exata de Poincaré: d(u, v) = arcosh(1 + 2 * ||u-v||^2 / ((1-||u||^2)(1-||v||^2)))."""
        u = self._project_to_ball(vec_u)
        v = self._project_to_ball(vec_v)

        sq_dist = float(np.sum((u - v) ** 2))
        u_norm_sq = float(np.sum(u ** 2))
        v_norm_sq = float(np.sum(v ** 2))

        denom = max((1.0 - u_norm_sq) * (1.0 - v_norm_sq), 1e-12)
        arg = 1.0 + 2.0 * (sq_dist / denom)

        # arcosh(x) para x >= 1
        return float(math.acosh(max(arg, 1.0)))

    def query_nearest_hyperbolic(self, query_entity: str, top_k: int = 5) -> Dict[str, Any]:
        """Localiza os conceitos semanticamente mais próximos na variedade hiperbólica."""
        start = time.perf_counter()
        q = query_entity.strip().lower()

        if q not in self.entity_embeddings:
            return {
                "status": "ENTITY_NOT_FOUND",
                "query": query_entity,
                "results": [],
                "elapsed_ms": round((time.perf_counter() - start) * 1000.0, 3)
            }

        q_vec = self.entity_embeddings[q]
        distances = []

        for name, vec in self.entity_embeddings.items():
            if name != q:
                d = self.hyperbolic_distance(q_vec, vec)
                distances.append((name, round(d, 4)))

        distances.sort(key=lambda item: item[1])
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "query_entity": q,
            "dimension": self.dimension,
            "total_entities": len(self.entity_embeddings),
            "nearest_neighbors": [{"entity": name, "hyperbolic_distance": dist} for name, dist in distances[:top_k]],
            "elapsed_ms": round(elapsed_ms, 3)
        }
