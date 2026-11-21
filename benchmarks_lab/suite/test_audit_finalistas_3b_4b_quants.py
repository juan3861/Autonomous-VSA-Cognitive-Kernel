# -*- coding: utf-8 -*-
"""
AETHERMIND STRICT AUDITOR TEST: TORNEIO DE EQUILIBRIO 3B-4B (Q4_K_M a F16)
"""
import sys, json
from pathlib import Path

PROOF_FILE = Path(r"F:\data\proof_quants_finalistas_3b_4b.json")

def main():
    if not PROOF_FILE.exists():
        print(f"[-] FALHA: {PROOF_FILE} não encontrado.")
        sys.exit(1)

    data = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
    completed = [v for v in data.values() if v.get("completed")]
    if len(completed) < 14:
        print(f"[-] FALHA: Apenas {len(completed)} configurações concluídas (esperado 14).")
        sys.exit(1)

    print(f"[+] AUDITORIA EMPÍRICA: {len(completed)} configurações certificadas (3B-4B):")
    for champ in ["ai9stars/G9v3-3B", "Parable-Qwen3-4B-Fable5", "deadbydawn101-Gemma4-E4B"]:
        items = sorted(
            [v for v in completed if v.get("champ") == champ],
            key=lambda x: (x.get("score_opus", 0), x.get("score_13_areas", 0), x.get("tg_tok_s", 0)),
            reverse=True
        )
        print(f"\n--- {champ} ({len(items)} quants) ---")
        for it in items:
            print(f"  {it['quant']:6} | 13 Áreas: {it['score_13_areas']:2}/39 ({it['pct_13_areas']:5.1f}%) | Opus: {it['score_opus']:2}/10 | TG: {it['tg_tok_s']:5.2f} t/s | PP: {it['pp_tok_s']:6.2f} t/s | Boot: {it['boot_seconds']:4.1f}s | {it['size_mb']/1024:.2f} GB")

    print("\n[+] SUCESSO: Matriz de Equilíbrio 3B-4B verificada pelo Strict Auditor.")
    sys.exit(0)

if __name__ == "__main__":
    main()
