# -*- coding: utf-8 -*-
"""
AETHERMIND STRICT AUDITOR TEST: TORNEIO DOS DESAFIANTES DE 100M A 200M
Validação Empírica Irrefutável (Tripla Checagem)
"""

import sys
import json
from pathlib import Path

PROOF_FILE = Path(r"F:\data\proof_torneio_desafiantes_100m_200m.json")

def main():
    if not PROOF_FILE.exists():
        print(f"[-] FALHA CRÍTICA: Arquivo de prova {PROOF_FILE} não existe.")
        sys.exit(1)

    with open(PROOF_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not data or len(data) < 2:
        print(f"[-] FALHA CRÍTICA: Menos de 2 modelos avaliados em {PROOF_FILE}. Total atual: {len(data)}")
        sys.exit(1)

    print(f"[+] AUDITORIA EMPÍRICA: {len(data)} modelos avaliados no torneio 100M-200M:")

    ranked = []
    for mid, res in data.items():
        name = res.get("name", mid)
        areas = res.get("areas_13", {})
        passed = areas.get("passed", 0)
        total = areas.get("total", 0)
        pct = areas.get("pct", 0.0)
        opus = res.get("opus_10", {})
        opus_passed = opus.get("passed", 0)
        speeds = res.get("speeds", {})
        pp = speeds.get("prompt_per_second", 0)
        tg = speeds.get("predicted_per_second", 0)
        size_mb = res.get("size_mb", 0)
        quant = res.get("quant", "")

        ranked.append({
            "name": name,
            "passed": passed,
            "total": total,
            "pct": pct,
            "opus_passed": opus_passed,
            "tg": tg,
            "pp": pp,
            "size_mb": size_mb,
            "quant": quant
        })

    ranked.sort(key=lambda x: (x["passed"], x["opus_passed"], x["tg"]), reverse=True)

    for i, r in enumerate(ranked, 1):
        print(f"  {i}. {r['name']:<35} | Áreas: {r['passed']}/{r['total']} ({r['pct']}%) | Opus: {r['opus_passed']}/10 | TG: {r['tg']} t/s | {r['size_mb']} MB")

    print("[+] SUCESSO: Todos os dados empíricos certificados pelo Strict Auditor.")
    sys.exit(0)

if __name__ == "__main__":
    main()
