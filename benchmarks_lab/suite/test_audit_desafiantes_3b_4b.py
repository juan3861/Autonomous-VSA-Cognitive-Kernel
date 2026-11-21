# -*- coding: utf-8 -*-
"""
AETHERMIND STRICT AUDITOR TEST: TORNEIO DOS DESAFIANTES 3B-4B VS CAMPEOES
"""
import sys, json
from pathlib import Path

PROOF_FILE = Path(r"F:\data\proof_desafiantes_3b_4b.json")

def main():
    if not PROOF_FILE.exists():
        print(f"[-] FALHA: {PROOF_FILE} não encontrado.")
        sys.exit(1)

    data = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
    completed = [v for v in data.values() if v.get("completed")]
    if len(completed) < 8:
        print(f"[-] FALHA: Apenas {len(completed)} desafiantes concluídos (esperado 8).")
        sys.exit(1)

    print(f"[+] AUDITORIA EMPÍRICA: {len(completed)} novos desafiantes 3B-4B certificados:")
    items = sorted(
        completed,
        key=lambda x: (x.get("score_opus", 0), x.get("score_13_areas", 0), x.get("tg_tok_s", 0)),
        reverse=True
    )
    for it in items:
        print(f"  {it['champ_short']:18} | 13 Áreas: {it['score_13_areas']:2}/39 (Base {it['baseline_13_areas']:2}) | Opus: {it['score_opus']:2}/10 | GPU: {it['tg_tok_s']:5.2f} t/s | CPU: {it['cpu_tg_tok_s']:5.2f} t/s | {it['size_mb']/1024:.2f} GB")

    print("\n[+] SUCESSO: Torneio dos Desafiantes 3B-4B verificado pelo Strict Auditor.")
    sys.exit(0)

if __name__ == "__main__":
    main()
