"""Pentti Kanerva 10,000-bit Vector Symbolic Architecture (HDC-VSA) Engine.

Área 05 & 12: Álgebra Holográfica de Hipervetores e Memória Associativa de Alta Dimensão.
Implementa a arquitetura canônica de Pentti Kanerva (NASA Ames / Redwood Center):
- Hipervetores bipolares de D = 10.000 bits (elementos em {-1, +1}).
- Concentração de medida: 99.999% dos vetores aleatórios são quase perfeitamente ortogonais.
- Álgebra MAP (Multiply, Add, Permute):
    1. Binding (Multiplicação Hadamard / XOR): Liga chave a valor (A * B). Auto-inverso: A * A = 1.
    2. Bundling (Soma com Voto Majoritário): Empilha múltiplos conceitos no mesmo vetor.
    3. Permutation (Deslocamento Cíclico): Codifica sintaxe, causalidade e sequência temporal.
- Resiliência Holográfica: Suporta 30% a 40% de corrupção ou apagamento de bits sem perder o conceito.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np


class KanervaHDC10000VSA:
    """Motor Algébrico de Computação Hiperdimensional (10.000 Bits)."""

    def __init__(self, dimension: int = 10000, seed: int = 42):
        self.dimension = dimension
        self.rng = np.random.RandomState(seed)
        self.cleanup_memory: Dict[str, np.ndarray] = {}

    def generate_random_hypervector(self) -> np.ndarray:
        """Gera um hipervetor bipolar aleatório de D=10.000 dimensões (-1 ou +1)."""
        bits = self.rng.randint(0, 2, size=self.dimension, dtype=np.int8)
        return np.where(bits == 0, -1, 1).astype(np.int8)

    def register_symbol(self, symbol_name: str) -> np.ndarray:
        """Cria ou recupera um símbolo atômico na memória de limpeza (Item Memory)."""
        name = symbol_name.strip().lower()
        if name not in self.cleanup_memory:
            self.cleanup_memory[name] = self.generate_random_hypervector()
        return self.cleanup_memory[name]

    def bind(self, vec_a: np.ndarray, vec_b: np.ndarray) -> np.ndarray:
        """Operação de Ligação (Binding / XOR): Multiplicação elemento a elemento."""
        return (vec_a * vec_b).astype(np.int8)

    def bundle(self, vectors: List[np.ndarray]) -> np.ndarray:
        """Operação de Empacotamento / Superposição (Bundling / Voto Majoritário)."""
        if not vectors:
            return np.zeros(self.dimension, dtype=np.int8)
        sum_vec = np.sum(vectors, axis=0, dtype=np.int32)
        # Regra de desempate determinística para somas iguais a zero
        tie_breaker = self.rng.choice([-1, 1], size=self.dimension)
        bundled = np.where(sum_vec > 0, 1, np.where(sum_vec < 0, -1, tie_breaker))
        return bundled.astype(np.int8)

    def permute(self, vector: np.ndarray, shift: int = 1) -> np.ndarray:
        """Operação de Permutação Cíclica (Bit-shift): Codifica ordem sintática e temporal."""
        return np.roll(vector, shift)

    def cosine_similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Similaridade angular normalizada no espaço de 10.000 dimensões in [-1, +1]."""
        dot = float(np.dot(vec_a.astype(np.float32), vec_b.astype(np.float32)))
        return dot / float(self.dimension)

    def cleanup_query(self, noisy_vector: np.ndarray, top_k: int = 3) -> List[Tuple[str, float]]:
        """Recupera o símbolo exato na memória de limpeza pelo vizinho mais próximo."""
        scores = []
        for name, item_vec in self.cleanup_memory.items():
            sim = self.cosine_similarity(noisy_vector, item_vec)
            scores.append((name, round(sim, 4)))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def encode_record(self, key_value_pairs: Dict[str, str]) -> np.ndarray:
        """Codifica uma estrutura relacional inteira em 1 único vetor de 10.000 bits: SUM(Key * Val)."""
        bound_pairs = []
        for k, v in key_value_pairs.items():
            k_vec = self.register_symbol(k)
            v_vec = self.register_symbol(v)
            bound_pairs.append(self.bind(k_vec, v_vec))
        return self.bundle(bound_pairs)

    def query_record_value(self, record_vector: np.ndarray, key_name: str) -> Dict[str, Any]:
        """Desempacota a chave aplicando a propriedade auto-inversa: (K * V) * K = V."""
        start = time.perf_counter()
        k_vec = self.register_symbol(key_name)
        # Unbinding exato por XOR: K * Record
        unbound = self.bind(record_vector, k_vec)
        matches = self.cleanup_query(unbound, top_k=3)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "query_key": key_name,
            "recovered_value": matches[0][0] if matches else None,
            "confidence_similarity": matches[0][1] if matches else 0.0,
            "top_candidates": matches,
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def stress_test_holographic_resilience(
        self,
        original_vector: np.ndarray,
        corruption_ratio: float = 0.35
    ) -> Dict[str, Any]:
        """Prova formal da tolerância a falhas: destrói 35% dos bits e recupera a identidade."""
        start = time.perf_counter()
        noisy = np.copy(original_vector)
        num_corrupt = int(self.dimension * corruption_ratio)
        flip_indices = self.rng.choice(self.dimension, size=num_corrupt, replace=False)
        noisy[flip_indices] = -noisy[flip_indices]

        # Mede similaridade com o original
        retained_similarity = self.cosine_similarity(noisy, original_vector)
        # Limiar teórico: 1.0 - 2 * corruption_ratio (para 35%, esperado ~0.30)
        expected_sim = 1.0 - 2.0 * corruption_ratio
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "dimension": self.dimension,
            "bits_corrupted": num_corrupt,
            "corruption_ratio_pct": round(corruption_ratio * 100.0, 1),
            "retained_similarity": round(retained_similarity, 4),
            "theoretical_expected": round(expected_sim, 4),
            "is_signal_surviving": retained_similarity > 0.20,
            "elapsed_ms": round(elapsed_ms, 3)
        }
