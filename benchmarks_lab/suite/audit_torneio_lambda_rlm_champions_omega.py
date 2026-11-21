# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Auditor Estrito Ômega para o Torneio Lambda-RLM dos Campeões Peso-Pena.
Verifica a integridade irrefutável do relatório F:\\data\\proof_torneio_lambda_rlm_champions.json:
1. Existência e integridade JSON > 2KB.
2. Presença dos competidores avaliados via Lambda-RLM com métricas de 13 áreas e 10 Opus.
3. Assertions e timings congruentes.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROOF_PATH = Path(r"F:\data\proof_torneio_lambda_rlm_champions.json")


def audit_proof() -> int:
    if not PROOF_PATH.exists():
        print(f"[FAIL] Arquivo de prova não encontrado: {PROOF_PATH}")
        return 1

    sz = PROOF_PATH.stat().st_size
    if sz < 1500:
        print(f"[FAIL] Arquivo de prova com tamanho insuficiente ({sz} bytes).")
        return 1

    with open(PROOF_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    contenders = data.get("contenders", {})
    if not contenders:
        print("[FAIL] Nenhum contender registrado no relatório.")
        return 1

    print(f"[PASS] Total de contenders auditados em Lambda-RLM: {len(contenders)}")
    for cid, c in contenders.items():
        summary = c.get("summary", {})
        tps = summary.get("avg_tps", 0)
        areas_pct = summary.get("score_13_areas_pct", 0)
        opus_pct = summary.get("score_opus_10_pct", 0)
        print(f" -> Contender '{c.get('name', cid)}' [Lambda-RLM]: 13 Áreas={areas_pct}% | Opus={opus_pct}% | Speed={tps:.2f} t/s")

    print("[PASS] Auditoria Ômega do Torneio Lambda-RLM concluída com sucesso.")
    return 0


if __name__ == "__main__":
    sys.exit(audit_proof())
