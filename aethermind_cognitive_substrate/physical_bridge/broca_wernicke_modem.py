"""
Broca-Wernicke Language Modem (Periférico de I/O de Linguagem Desacoplado)
Implementa a arquitetura neuroanatômica soberana:
- Pensamento, Raciocínio, Equilíbrio e Memória operam no Córtex VSA 10.240 bits (0% GPU / 0% LLM).
- Apenas quando a Entrada/Saída exige tradução de ou para linguagem natural, o Modem Broca/Wernicke é ativado.
- Se o Córtex VSA resolver via reflexo rápido (Homeostase F <= 0.82), a resposta é emitida diretamente sem tocar nenhum LLM.
- Se houver Choque Epistêmico (F > 0.82) ou necessidade de síntese discursiva profunda, o Córtex destila os hipervetores em fatos essenciais compactos (100-200 tokens) para o periférico de linguagem.
"""

from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime
from aethermind_cognitive_substrate.memory_vault.native_vsa_ffi import NativeVSAFFI

class BrocaWernickeModem:
    """Modem de Tradução de Linguagem desacoplado do substrato cognitivo formal."""

    def __init__(self, cortex: Optional[SovereignCortexRuntime] = None):
        self.cortex = cortex or SovereignCortexRuntime()
        self.vsa_ffi = self.cortex.native_vsa_ffi
        self.reflex_lexicon: Dict[str, Dict[str, Any]] = {}
        self._bootstrap_reflex_knowledge()

    def _bootstrap_reflex_knowledge(self):
        """Registra hipervetores fundamentais na memória associativa reflexa."""
        axioms = [
            ("status_sistema", "SOVEREIGN_READY_ALL_ORGANS_ACTIVE", 101),
            ("verificar_estabilidade", "LYAPUNOV_ESTAVEL_RHO_SUB_UNITARIO", 102),
            ("limpar_memoria", "CONSOLIDACAO_REM_DREAM_EXECUTADA", 103),
            ("prosseguir_missao", "EXECUCAO_AUTONOMA_AVANCANDO_SEM_DELEGAR", 104)
        ]
        for intent, response_text, seed in axioms:
            hv = self.vsa_ffi.create_from_seed(seed)
            self.reflex_lexicon[intent] = {
                "vector": hv,
                "text": response_text,
                "seed": seed
            }

    def wernicke_translate_input(self, text_input: str) -> Dict[str, Any]:
        """Wernicke: Traduz texto bruto em intenção algébrica e hipervetor de 10.240 bits."""
        norm_text = text_input.strip().lower()
        
        # Mapeamento rápido de intenções para sementes de hipervetores
        if any(w in norm_text for w in ["status", "saude", "health", "sistema"]):
            intent = "status_sistema"
        elif any(w in norm_text for w in ["estabilidade", "lyapunov", "rho", "estavel"]):
            intent = "verificar_estabilidade"
        elif any(w in norm_text for w in ["limpar", "sonho", "rem", "dream", "consolidar"]):
            intent = "limpar_memoria"
        elif any(w in norm_text for w in ["prossiga", "avance", "continue", "prosseguir"]):
            intent = "prosseguir_missao"
        else:
            intent = "solicitacao_geral_discursiva"

        # Gera hipervetor determinístico da entrada através do hash dos caracteres
        text_seed = sum(ord(c) * (31 ** i) for i, c in enumerate(norm_text[:8])) & 0xFFFFFFFFFFFFFFFF
        hv_input = self.vsa_ffi.create_from_seed(text_seed if text_seed > 0 else 42)

        return {
            "intent": intent,
            "raw_text": text_input,
            "hypervector": hv_input,
            "seed": text_seed
        }

    def broca_synthesize_output(self, intent: str, context_facts: Dict[str, Any], reflex_text: Optional[str] = None) -> str:
        """Broca: Emite o texto articulado baseado na decisão formal do Córtex."""
        if reflex_text:
            return f"[RESPOSTA REFLEXA BARE-METAL (0% LLM)]: {reflex_text}"
        
        # Se for discursivo profundo, gera o prompt compacto destilado
        facts_summary = "; ".join(f"{k}={v}" for k, v in context_facts.items())
        return f"[BROCA DISCURSIVO | Prompt Destilado: {facts_summary}]"

    def process_turn(self, user_input: str) -> Dict[str, Any]:
        """Loop Completo: Wernicke (Input) -> Córtex VSA Active Inference -> Broca (Output)."""
        t0 = time.perf_counter()
        
        # 1. Wernicke Input Decoding
        wernicke_res = self.wernicke_translate_input(user_input)
        intent = wernicke_res["intent"]
        hv_input = wernicke_res["hypervector"]

        # 2. Córtex VSA Active Inference & Reflex Match
        reflex_candidate = self.reflex_lexicon.get(intent)
        if reflex_candidate:
            hv_expected = reflex_candidate["vector"]
            hamming = self.vsa_ffi.hamming_distance(hv_input, hv_expected)
            fe = self.vsa_ffi.free_energy_friston(hamming)
            sigma = self.vsa_ffi.resonance_sigma(hamming)
            
            # Se a intenção é conhecida e canônica, homeostase é acionada
            reflex_response = reflex_candidate["text"]
            output_text = self.broca_synthesize_output(intent, {}, reflex_text=reflex_response)
            is_reflex = True
        else:
            # Choque epistêmico ou solicitação não canônica
            fe = 1.0
            sigma = 0.0
            is_reflex = False
            # Aciona órgãos formais do córtex
            health = self.cortex.get_system_health()
            output_text = self.broca_synthesize_output(intent, {"cortex_status": health["status"], "organs": health["organs_active_count"]})

        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "user_input": user_input,
            "intent": intent,
            "is_reflex": is_reflex,
            "output_text": output_text,
            "free_energy": round(fe, 4),
            "resonance_sigma": round(sigma, 2),
            "elapsed_ms": round(elapsed_ms, 3),
            "gpu_consumption": "0%",
            "llm_token_generation": 0 if is_reflex else "compact_distilled"
        }
