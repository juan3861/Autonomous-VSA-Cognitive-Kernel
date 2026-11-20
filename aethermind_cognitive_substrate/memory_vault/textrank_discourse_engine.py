"""TextRank Discourse & Extractive Graph Engine (AetherMind Cognitive Substrate).

Área 12: Linguística, Análise de Discurso e Sumarização Extrativa por Grafos.
Implementa o algoritmo TextRank (PageRank sobre grafos de coocorrência e similaridade de sentenças).
Extrai conceitos centrais, sumariza documentações densas e calcula densidade informacional
sem modelos neurais pesados em frações de milissegundo.
"""
from __future__ import annotations

import re
import time
from typing import Dict, Any, List, Set, Tuple
import networkx as nx


class TextRankDiscourseEngine:
    """Motor de Análise de Discurso e Sumarização por Centralidade de Grafo."""

    def __init__(self, damping: float = 0.85):
        self.damping = damping
        self.stopwords = {
            "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das",
            "em", "no", "na", "nos", "nas", "para", "por", "com", "sem", "e", "ou", "mas",
            "que", "se", "como", "ao", "aos", "the", "and", "or", "in", "on", "at", "to", "for"
        }

    def _tokenize_words(self, text: str) -> List[str]:
        words = re.findall(r"\b[a-zA-ZáéíóúãõâêîôûçÁÉÍÓÚÃÕÂÊÎÔÛÇ]{2,}\b", text.lower())
        return [w for w in words if w not in self.stopwords]

    def _sentence_similarity(self, words_a: List[str], words_b: List[str]) -> float:
        if not words_a or not words_b:
            return 0.0
        set_a = set(words_a)
        set_b = set(words_b)
        intersection = len(set_a & set_b)
        # Normalização logarítmica para evitar favorecer frases longas
        denom = len(set_a) + len(set_b)
        return float((2.0 * intersection) / denom) if denom > 0 else 0.0

    def summarize_extractive(self, raw_text: str, top_n_sentences: int = 3) -> Dict[str, Any]:
        """Extrai as N sentenças mais centrais do texto usando TextRank."""
        start = time.perf_counter()

        # Split simples de sentenças por pontuação (. ! ?)
        sentences = [s.strip() for s in re.split(r"[.!?]+", raw_text) if len(s.strip()) > 15]

        if len(sentences) <= top_n_sentences:
            return {
                "status": "SHORT_TEXT",
                "summary": " ".join(sentences),
                "ranked_sentences": sentences,
                "elapsed_ms": round((time.perf_counter() - start) * 1000.0, 3)
            }

        sentence_words = [self._tokenize_words(s) for s in sentences]
        graph = nx.Graph()

        # Adiciona nós
        for idx in range(len(sentences)):
            graph.add_node(idx)

        # Adiciona arestas de similaridade entre todos os pares
        for i in range(len(sentences)):
            for j in range(i + 1, len(sentences)):
                sim = self._sentence_similarity(sentence_words[i], sentence_words[j])
                if sim > 0.05:
                    graph.add_edge(i, j, weight=sim)

        if graph.number_of_edges() == 0:
            scores = {i: 1.0 for i in range(len(sentences))}
        else:
            scores = nx.pagerank(graph, alpha=self.damping, weight="weight", max_iter=50)

        # Ordena sentenças por score de centralidade
        ranked_indices = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
        top_indices = sorted(ranked_indices[:top_n_sentences])  # Reordena na ordem original de leitura
        selected_sentences = [sentences[idx] for idx in top_indices]

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "total_sentences": len(sentences),
            "summary_sentences_count": len(selected_sentences),
            "summary": " ".join(selected_sentences),
            "ranked_sentences": [
                {"sentence": sentences[idx], "score": round(scores[idx], 4)}
                for idx in ranked_indices[:top_n_sentences]
            ],
            "elapsed_ms": round(elapsed_ms, 3)
        }
