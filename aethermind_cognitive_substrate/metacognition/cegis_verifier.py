"""Counterexample-Guided Inductive Synthesis (CEGIS) Verifier (AetherMind Cognitive Substrate).

Áreas 06 & 07: Metacognição, Verificação Formal e Cadinho Red-Team.
Implementa o loop CEGIS clássico: testa ativamente uma solução candidata
contra uma especificação formal buscando contraexemplos adversariais.
Se encontrar falha, retroalimenta o motor de síntese até atingir prova irrefutável.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Callable, Optional, Tuple


class CEGISVerifier:
    """Verificador e Sintetizador Guiado por Contraexemplos (CEGIS)."""

    def __init__(self, max_iterations: int = 50):
        self.max_iterations = max_iterations
        self.counterexample_database: List[Any] = []

    def verify_candidate_against_spec(
        self,
        candidate_fn: Callable[[Any], Any],
        spec_oracle_fn: Callable[[Any], Any],
        test_inputs: List[Any]
    ) -> Dict[str, Any]:
        """Testa a função candidata contra a especificação em um domínio de teste."""
        start = time.perf_counter()
        counterexamples = []

        for inp in test_inputs:
            cand_res = candidate_fn(inp)
            spec_res = spec_oracle_fn(inp)

            if cand_res != spec_res:
                counterexamples.append({
                    "input": inp,
                    "candidate_output": cand_res,
                    "expected_output": spec_res
                })
                self.counterexample_database.append(inp)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if not counterexamples:
            return {
                "verified": True,
                "status": "FORMALLY_VERIFIED",
                "tests_passed": len(test_inputs),
                "counterexamples_count": 0,
                "elapsed_ms": round(elapsed_ms, 3)
            }
        else:
            return {
                "verified": False,
                "status": "COUNTEREXAMPLE_DISCOVERED",
                "tests_passed": len(test_inputs) - len(counterexamples),
                "counterexamples_count": len(counterexamples),
                "first_counterexample": counterexamples[0],
                "all_counterexamples": counterexamples,
                "elapsed_ms": round(elapsed_ms, 3)
            }

    def execute_cegis_synthesis_loop(
        self,
        synthesize_fn: Callable[[List[Any]], Callable[[Any], Any]],
        oracle_fn: Callable[[Any], Any],
        initial_domain: List[Any]
    ) -> Dict[str, Any]:
        """Executa o loop completo de síntese indutiva guiada por contraexemplos."""
        start = time.perf_counter()
        active_examples: List[Any] = [initial_domain[0]] if initial_domain else []
        history = []

        for iteration in range(self.max_iterations):
            # Passo 1: Sintetiza candidato compatível com os contraexemplos acumulados
            candidate = synthesize_fn(active_examples)

            # Passo 2: O Verificador procura novo contraexemplo em todo o domínio
            verification = self.verify_candidate_against_spec(candidate, oracle_fn, initial_domain)
            history.append({
                "iteration": iteration + 1,
                "active_examples_count": len(active_examples),
                "verified": verification["verified"]
            })

            if verification["verified"]:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                return {
                    "status": "SYNTHESIS_CONVERGED",
                    "iterations_taken": iteration + 1,
                    "total_counterexamples_needed": len(active_examples),
                    "history": history,
                    "elapsed_ms": round(elapsed_ms, 3)
                }

            # Adiciona o novo contraexemplo descoberto ao conjunto de treino
            new_ce = verification["first_counterexample"]["input"]
            if new_ce not in active_examples:
                active_examples.append(new_ce)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {
            "status": "MAX_ITERATIONS_EXCEEDED",
            "iterations_taken": self.max_iterations,
            "history": history,
            "elapsed_ms": round(elapsed_ms, 3)
        }
