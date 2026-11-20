"""Hyperdimensional Computing (HDC) & Vector Symbolic Architecture (AetherMind Cognitive Substrate).

Áreas 05 & 12: Memória Holográfica, Compressão Semântica e Álgebra Vetorial Simbólica.
Opera sobre vetores bipolares de 2048 dimensões em {-1, +1}.
Permite binding (associação chave-valor), bundling (superposição de conceitos)
e desempacotamento associativo exato com zero consumo de GPU.
"""
from __future__ import annotations

import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class HDCVectorCompactor:
    """Motor de Computação Hiperdimensional (HDC / VSA) de 2048 Dimensões."""

    def __init__(self, dimension: int = 2048):
        self.dimension = dimension
        self.item_memory: Dict[str, np.ndarray] = {}

    def get_or_create_basis_vector(self, atom_name: str) -> np.ndarray:
        """Gera um vetor base pseudo-ortogonal determinístico a partir do hash do símbolo."""
        if atom_name in self.item_memory:
            return self.item_memory[atom_name]

        # Semente determinística usando SHA-256 do nome do símbolo
        seed = int(hashlib.sha256(atom_name.encode("utf-8")).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        # Vetor bipolar: 50% de -1 e 50% de +1
        vec = rng.choice([-1.0, 1.0], size=self.dimension)
        self.item_memory[atom_name] = vec
        return vec

    def bind(self, vec_a: np.ndarray, vec_b: np.ndarray) -> np.ndarray:
        """Operação de Binding (Associação): Produto elemento a elemento (Hadamard product)."""
        return vec_a * vec_b

    def bundle(self, vectors: List[np.ndarray]) -> np.ndarray:
        """Operação de Bundling (Superposição): Soma com função sinal (maioria de votos)."""
        if not vectors:
            return np.zeros(self.dimension)
        accum = np.sum(vectors, axis=0)
        # Desempata zeros para +1
        bundled = np.where(accum >= 0, 1.0, -1.0)
        return bundled

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Calcula similaridade de cosseno normalizada entre vetores bipolares (escala -1 a +1)."""
        dot = np.dot(vec_a, vec_b)
        return float(dot / self.dimension)

    def encode_key_value_record(self, record: Dict[str, str]) -> np.ndarray:
        """Codifica um registro chave-valor inteiro em um único vetor holográfico de 2048 bits."""
        bound_pairs = []
        for key, val in record.items():
            k_vec = self.get_or_create_basis_vector(f"KEY_{key}")
            v_vec = self.get_or_create_basis_vector(f"VAL_{val}")
            bound_pairs.append(self.bind(k_vec, v_vec))
        return self.bundle(bound_pairs)

    def query_value_for_key(self, record_hologram: np.ndarray, key: str, candidate_values: List[str]) -> Dict[str, Any]:
        """Recupera o valor associado a uma chave desempacotando o holograma: (K * V_bundled) * K ≈ V."""
        start = time.perf_counter()
        k_vec = self.get_or_create_basis_vector(f"KEY_{key}")
        # Desempacota multiplicando pelo vetor da chave
        unbound_query = self.bind(record_hologram, k_vec)

        # Mede a similaridade com os candidatos conhecidos
        best_candidate = None
        best_similarity = -2.0
        scores = {}

        for val in candidate_values:
            v_vec = self.get_or_create_basis_vector(f"VAL_{val}")
            sim = self.similarity(unbound_query, v_vec)
            scores[val] = round(sim, 4)
            if sim > best_similarity:
                best_similarity = sim
                best_candidate = val

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "queried_key": key,
            "recovered_value": best_candidate,
            "confidence_similarity": round(best_similarity, 4),
            "candidate_scores": scores,
            "elapsed_ms": round(elapsed_ms, 3)
        }
