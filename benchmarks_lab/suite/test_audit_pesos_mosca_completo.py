# -*- coding: utf-8 -*-
"""
AETHERMIND STRICT AUDITOR TEST: TORNEIO COMPLETO PESOS-MOSCA (26 VARIANTES Q4_K_M A F16/BF16)
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

PROOF_FILE = Path(r"F:\data\proof_pesos_mosca_completo.json")


def main():
    if not PROOF_FILE.exists():
        print(f"[-] FALHA: {PROOF_FILE} nao encontrado.")
        sys.exit(1)

    data = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
    completed = [v for v in data.values() if v.get("completed")]
    if len(completed) < 26:
        print(f"[-] FALHA: Apenas {len(completed)}/26 variantes concluidas.")
        sys.exit(1)

    # Verifica se Lambda-RLM de fato produziu resgates empiricos (anti-falha silenciosa)
    total_rescues = sum(
        max(0, v.get("score_13_areas", 0) - v.get("baseline_13_areas", 0))
        for v in completed
    )
    if total_rescues == 0:
        print("[-] FALHA: Zero resgates Lambda-RLM em todas as 26 variantes (possivel falha silenciosa do motor).")
        sys.exit(1)

    print(f"[+] AUDITORIA EMPIRICA: {len(completed)}/26 variantes Pesos-Mosca certificadas | Resgates Lambda-RLM totais: +{total_rescues}")
    items = sorted(
        completed,
        key=lambda x: (x.get("tier", ""), x.get("score_opus", 0), x.get("score_13_areas", 0), x.get("tg_tok_s", 0)),
        reverse=True,
    )
    for it in items:
        print(
            f"  [{it['tier']:4s}] {it['champ_short']:22s} {it['quant']:6s} | "
            f"13A: {it['score_13_areas']:2d}/39 (Base {it['baseline_13_areas']:2d}) | "
            f"Opus: {it['score_opus']:2d}/10 | GPU: {it['tg_tok_s']:6.2f} t/s | "
            f"CPU: {it['cpu_tg_tok_s']:5.2f} t/s | {it['size_mb']:6.1f} MB"
        )

    print("\n[+] SUCESSO: Malha completa Pesos-Mosca (Q4_K_M a F16/BF16) verificada pelo Strict Auditor.")
    sys.exit(0)


if __name__ == "__main__":
    main()
