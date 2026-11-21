# -*- coding: utf-8 -*-
"""
AUDITORIA ESTRITA OMEGA DO DUELO DE ENGENHARIA DE CÓDIGO (10 TESTES: 8B-RLM vs 9B-HERETIC)
Valida fisicamente F:\\data\\proof_duelo_codigo_8b_vs_9b.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

PROOF_DUEL_PATH = Path(r"F:\data\proof_duelo_codigo_8b_vs_9b.json")


def main() -> int:
    assert PROOF_DUEL_PATH.exists() and PROOF_DUEL_PATH.stat().st_size > 5000, "Prova do duelo de código ausente!"
    data = json.loads(PROOF_DUEL_PATH.read_text(encoding="utf-8"))

    contenders = data.get("contenders", {})
    assert set(contenders.keys()) == {"8b-rlm", "9b-heretic"}

    c8 = contenders["8b-rlm"]
    c9 = contenders["9b-heretic"]

    assert len(c8["tests"]) == 10 and len(c9["tests"]) == 10
    assert c8["final_passes"] == 10, f"8b-rlm deveria ter 10/10 final_passes: {c8['final_passes']}"
    assert c9["final_passes"] == 10, f"9b-heretic deveria ter 10/10 final_passes: {c9['final_passes']}"
    assert c8["zero_shot_passes"] >= 9, f"8b-rlm obteve {c8['zero_shot_passes']}/10 zero-shot"

    print("=" * 84)
    print(" [AUDITORIA OMEGA APROVADA] DUELO DE ENGENHARIA DE CÓDIGO (10 ALGORITMOS REAIS)")
    print("=" * 84)
    print(
        f" * [8b-rlm    ] Zero-Shot: {c8['zero_shot_passes']}/10 ({c8['zero_shot_pct']}%) | "
        f"Final c/ Reparo: {c8['final_passes']}/10 ({c8['final_pass_pct']}%) | "
        f"Tempo: {c8['total_time_s']}s"
    )
    print(
        f" * [9b-heretic] Zero-Shot: {c9['zero_shot_passes']}/10 ({c9['zero_shot_pct']}%) | "
        f"Final c/ Reparo: {c9['final_passes']}/10 ({c9['final_pass_pct']}%) | "
        f"Tempo: {c9['total_time_s']}s"
    )
    print("=" * 84)
    return 0


if __name__ == "__main__":
    sys.exit(main())
