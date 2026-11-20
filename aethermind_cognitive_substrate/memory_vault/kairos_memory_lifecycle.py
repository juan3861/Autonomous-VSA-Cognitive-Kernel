"""KAIROS Memory Lifecycle Daemon (AetherMind Cognitive Substrate).

Área 05: Consolidação Perene de Memória (autoDream).
Executa o ciclo contínuo em 4 fases:
Orientar -> Coletar -> Consolidar -> Podar (Orient -> Gather -> Consolidate -> Prune).
Garante que a memória de longo prazo seja mantida pura e livre de inchaço.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Set, Optional


class KAIROSMemoryLifecycle:
    """Orquestrador do Ciclo de Vida da Memória KAIROS."""

    def __init__(self):
        self.working_memory: List[Dict[str, Any]] = []
        self.consolidated_vault: List[Dict[str, Any]] = []
        self.pruned_records_count: int = 0

    def record_working_event(self, event_type: str, content: str, importance: float = 1.0) -> None:
        """Registra um evento ou aprendizado na memória de trabalho de curto prazo."""
        self.working_memory.append({
            "timestamp": time.time(),
            "type": event_type,
            "content": content,
            "importance": importance
        })

    def run_autodream_cycle(self, retention_threshold: float = 0.5) -> Dict[str, Any]:
        """Executa o ciclo completo de consolidação em 4 fases."""
        start = time.perf_counter()

        # FASE 1: ORIENT
        total_working = len(self.working_memory)
        orient_meta = {
            "unconsolidated_events": total_working,
            "vault_existing_size": len(self.consolidated_vault)
        }

        # FASE 2: GATHER
        high_value_items = []
        low_value_items = []
        for item in self.working_memory:
            if item["importance"] >= retention_threshold:
                high_value_items.append(item)
            else:
                low_value_items.append(item)

        # FASE 3: CONSOLIDATE
        for item in high_value_items:
            consolidated_record = {
                "id": f"KAIROS_{len(self.consolidated_vault) + 1}",
                "consolidated_at": time.time(),
                "type": item["type"],
                "content": item["content"],
                "crystallized_importance": item["importance"]
            }
            self.consolidated_vault.append(consolidated_record)

        # FASE 4: PRUNE
        pruned_count = len(low_value_items)
        self.pruned_records_count += pruned_count
        self.working_memory.clear()  # Limpa o buffer de trabalho

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "AUTODREAM_COMPLETED",
            "orient_phase": orient_meta,
            "gathered_items": len(high_value_items),
            "consolidated_total": len(self.consolidated_vault),
            "pruned_items": pruned_count,
            "total_lifetime_pruned": self.pruned_records_count,
            "elapsed_ms": round(elapsed_ms, 3)
        }
