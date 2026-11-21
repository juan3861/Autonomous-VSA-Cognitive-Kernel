# -*- coding: utf-8 -*-
"""
Auditoria Empírica Estrita — Duelo de Quantizações dos 3 Campeões 600M
Comandante: Mestre Ruan
"""
import sys
import json
from pathlib import Path

PROOF_FILE = Path(r"F:\data\proof_quants_3_campeoes_600m.json")

def test_proof_exists_and_populated():
    assert PROOF_FILE.exists(), f"Arquivo de prova {PROOF_FILE} não encontrado!"
    size = PROOF_FILE.stat().st_size
    assert size > 1000, f"Arquivo de prova muito pequeno: {size} bytes"

    with open(PROOF_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict), "Dados de prova devem ser um dicionário JSON"
    assert len(data) >= 15, f"Esperado no mínimo 15 configurações (3 campeões x 5 quantizações), encontrados: {len(data)}"

    # Verifica os 3 campeões
    c1_count = sum(1 for v in data.values() if v.get("champ_short") == "Qwen3-0.6B-Distill-30B")
    c2_count = sum(1 for v in data.values() if v.get("champ_short") == "Qwen3-0.6B-Opus4.6")
    c3_count = sum(1 for v in data.values() if v.get("champ_short") == "TinyQwen3-Distill-0.6B")

    assert c1_count == 5, f"Esperado 5 quants para Campeão 1, encontrado: {c1_count}"
    assert c2_count == 5, f"Esperado 5 quants para Campeão 2, encontrado: {c2_count}"
    assert c3_count == 5, f"Esperado 5 quants para Campeão 3, encontrado: {c3_count}"

    for mid, m in data.items():
        assert "score_13_areas" in m, f"Modelo {mid} sem score_13_areas"
        assert "pct_13_areas" in m, f"Modelo {mid} sem pct_13_areas"
        assert "tg_tok_s" in m, f"Modelo {mid} sem tg_tok_s"
        assert "boot_seconds" in m, f"Modelo {mid} sem boot_seconds"
        assert m["tg_tok_s"] > 15.0, f"Velocidade suspeitamente baixa para {mid}: {m['tg_tok_s']} tok/s"

    print(f"[+] AUDITORIA EMPÍRICA APROVADA: {len(data)} configurações dos 3 Campeões 600M auditadas e validadas com sucesso!")

if __name__ == "__main__":
    test_proof_exists_and_populated()
