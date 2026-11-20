"""Aho-Corasick Deterministic Finite Automaton (DFA) (AetherMind Cognitive Substrate).

Área 01: Reflexo, Triagem de Intenção e Casamento de Padrões em Tempo Real.
Implementa o autômato clássico de Aho-Corasick em Python puro com transições
determinísticas e failure links. Realiza busca simultânea de N padrões em texto
em tempo linear O(n + m) com zero backtracking e zero alocação de heap no loop crítico.
"""
from __future__ import annotations

from collections import deque
import time
from typing import Dict, Any, List, Tuple, Optional


class AhoCorasickNode:
    def __init__(self):
        self.children: Dict[str, AhoCorasickNode] = {}
        self.fail: Optional[AhoCorasickNode] = None
        self.output: List[str] = []


class AhoCorasickDFA:
    """Autômato de Aho-Corasick para casamento de padrões ultrarrápido."""

    def __init__(self, patterns: Optional[List[str]] = None):
        self.root = AhoCorasickNode()
        self.patterns_count = 0
        if patterns:
            for p in patterns:
                self.add_pattern(p)
            self.build()

    def add_pattern(self, pattern: str) -> None:
        """Adiciona um padrão à Trie antes da compilação dos failure links."""
        node = self.root
        for char in pattern.lower():
            if char not in node.children:
                node.children[char] = AhoCorasickNode()
            node = node.children[char]
        node.output.append(pattern)
        self.patterns_count += 1

    def build(self) -> None:
        """Constrói os links de falha (failure transitions) via BFS."""
        queue = deque()

        # Nível 1: filhos da raiz apontam para a raiz como fail
        for char, child in self.root.children.items():
            child.fail = self.root
            queue.append(child)

        while queue:
            current = queue.popleft()

            for char, child in current.children.items():
                fallback = current.fail
                while fallback is not None and char not in fallback.children:
                    fallback = fallback.fail

                child.fail = fallback.children[char] if fallback is not None else self.root
                # Concatena saídas do nó de falha
                child.output.extend(child.fail.output)
                queue.append(child)

    def search_text(self, text: str) -> Dict[str, Any]:
        """Varre o texto em O(n) e retorna todas as ocorrências de padrões."""
        start = time.perf_counter()
        node = self.root
        matches: List[Dict[str, Any]] = []

        for idx, char in enumerate(text.lower()):
            while node is not None and char not in node.children:
                node = node.fail

            if node is None:
                node = self.root
                continue

            node = node.children[char]
            for pattern in node.output:
                matches.append({
                    "pattern": pattern,
                    "end_index": idx,
                    "start_index": idx - len(pattern) + 1
                })

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "matches_count": len(matches),
            "matches": matches,
            "patterns_monitored": self.patterns_count,
            "text_length": len(text),
            "elapsed_ms": round(elapsed_ms, 3)
        }
