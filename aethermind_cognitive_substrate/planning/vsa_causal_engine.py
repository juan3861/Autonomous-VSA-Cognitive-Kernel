"""
Hyperdimensional Vector Symbolic Architecture Causal Engine (VSA 10,240-bit Causal Binding)
Represents causal relations directly in the 10,240-bit holographic space:
- Causal Edge Binding: Edge(A -> B) = A ^ permute(B, 1)
- Causal Graph Superposition: SCM_Hologram = Bundle(Edge_1, Edge_2, ..., Edge_N)
- Interventional Surgery: Unbind A from SCM and inject intervention value do(A = v)
- Downstream Effect Propagation via Algebraic Roll / Unbind in nanoseconds.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from aethermind_cognitive_substrate.memory_vault.native_vsa_ffi import NativeVSAFFI, WORDS, BITS

class VSACausalEngine:
    """Motor Causal Puro em Espaço Algébrico de Hipervetores de 10.240 Bits."""

    def __init__(self, ffi: Optional[NativeVSAFFI] = None):
        self.ffi = ffi or NativeVSAFFI()
        self.symbols: Dict[str, np.ndarray] = {}
        self.edges: List[Tuple[str, str]] = []
        self.hologram: np.ndarray = np.zeros(WORDS, dtype=np.uint64)

    def get_or_create_concept(self, name: str, seed: Optional[int] = None) -> np.ndarray:
        concept = name.strip().lower()
        if concept not in self.symbols:
            s = seed if seed is not None else sum(ord(c) * (37 ** i) for i, c in enumerate(concept[:8])) & 0xFFFFFFFFFFFFFFFF
            self.symbols[concept] = self.ffi.create_from_seed(s if s > 0 else 42)
        return self.symbols[concept]

    def permute_forward(self, vec: np.ndarray, shift_words: int = 1) -> np.ndarray:
        """Deslocamento de palavras u64 para codificar direção causal (A -> B)."""
        return np.roll(vec, shift_words)

    def permute_backward(self, vec: np.ndarray, shift_words: int = 1) -> np.ndarray:
        """Deslocamento reverso para recuperar o efeito downstream."""
        return np.roll(vec, -shift_words)

    def add_causal_relation(self, cause: str, effect: str):
        """Codifica a relação causal: Edge = Cause ^ Roll(Effect, 1)."""
        c_vec = self.get_or_create_concept(cause)
        e_vec = self.get_or_create_concept(effect)
        e_shifted = self.permute_forward(e_vec, shift_words=1)
        
        edge_vec = self.ffi.bind(c_vec, e_shifted)
        self.edges.append((cause.lower(), effect.lower()))
        
        # Superposição no Holograma Causal Geral
        if len(self.edges) == 1:
            self.hologram = np.copy(edge_vec)
        else:
            self.hologram = self.ffi.bundle_two(self.hologram, edge_vec, tie_seed=len(self.edges) * 101)

    def query_causal_effect(self, cause: str) -> Dict[str, Any]:
        """
        Recupera algebricamente o efeito direto da causa a partir do holograma:
        Effect_shifted = Hologram ^ Cause
        Effect = Unroll(Effect_shifted, 1)
        """
        start = time.perf_counter()
        c_vec = self.get_or_create_concept(cause)
        
        # Desempacotamento por XOR com a causa
        unbound_shifted = self.ffi.bind(self.hologram, c_vec)
        predicted_effect_vec = self.permute_backward(unbound_shifted, shift_words=1)
        
        # Limpeza associativa procurando o efeito com menor distância de Hamming
        best_match = None
        min_dist = BITS
        best_sigma = -99.0
        
        for name, item_vec in self.symbols.items():
            if name == cause.lower():
                continue
            dist = self.ffi.hamming_distance(predicted_effect_vec, item_vec)
            sigma = self.ffi.resonance_sigma(dist)
            if dist < min_dist:
                min_dist = dist
                best_match = name
                best_sigma = sigma

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "query_cause": cause,
            "predicted_effect": best_match,
            "hamming_distance": min_dist,
            "resonance_sigma": round(best_sigma, 2),
            "is_causal_signal_strong": best_sigma > 5.0,
            "elapsed_ms": round(elapsed_ms, 3)
        }
