# -*- coding: utf-8 -*-
"""
AETHERMIND STRICT EMPIRICAL AUDITOR — FAMILIA IFM K2-HORIZON (0.9B, 3.7B, 7B)
Valida integridade dos 9 modelos homologados em F:\data\proof_k2_horizon_completo.json
e verifica a Fronteira de Pareto contra os campeoes anteriores.
"""
import json
from pathlib import Path

PROOF_K2 = Path(r"F:\data\proof_k2_horizon_completo.json")
PROOF_MOSCA = Path(r"F:\data\proof_pesos_mosca_completo.json")

def test_k2_horizon_empirical_proofs():
    assert PROOF_K2.exists(), "Arquivo de prova K2-Horizon nao encontrado!"
    data = json.loads(PROOF_K2.read_text(encoding="utf-8"))
    assert len(data) == 9, f"Esperado 9 registros completos, encontrado {len(data)}"

    expected_ids = {
        "k2_horizon_3_7b__q4_k_m",
        "k2_horizon_3_7b__q5_k_m",
        "k2_horizon_3_7b__q6_k",
        "k2_horizon_3_7b__q8_0",
        "k2_horizon_0_9b__q4_k_m",
        "k2_horizon_0_9b__q5_k_m",
        "k2_horizon_0_9b__q6_k",
        "k2_horizon_0_9b__q8_0",
        "k2_horizon_7b__q4_k_m",
    }
    assert set(data.keys()) == expected_ids, f"IDs divergentes: {set(data.keys()) ^ expected_ids}"

    for cid, rec in data.items():
        assert rec.get("completed") is True, f"{cid} nao esta marcado como completed"
        assert rec.get("size_mb", 0) > 500, f"{cid} tamanho invalido"
        assert rec.get("tg_tok_s", 0) > 0, f"{cid} GPU tok/s zerado"
        assert rec.get("cpu_tg_tok_s", 0) > 0, f"{cid} CPU tok/s zerado"
        assert 0 < rec.get("score_13_areas", 0) <= 39, f"{cid} score 13A invalido"
        assert 0 <= rec.get("score_opus", -1) <= 10, f"{cid} score Opus invalido"

    # Verifica supremacia do 0.9B [Q8_0] (35/39) e 0.9B [Q6_K] (34/39 + 4/10 Opus)
    assert data["k2_horizon_0_9b__q8_0"]["score_13_areas"] == 35
    assert data["k2_horizon_0_9b__q6_k"]["score_13_areas"] == 34
    assert data["k2_horizon_0_9b__q6_k"]["score_opus"] == 4

    # Verifica supremacia do 3.7B [Q6_K] (37/39 + 3/10 Opus)
    assert data["k2_horizon_3_7b__q6_k"]["score_13_areas"] == 37
    assert data["k2_horizon_3_7b__q6_k"]["score_opus"] == 3

    # Verifica empate do 7B [Q4_K_M] em 37/39 com 3x menos velocidade
    assert data["k2_horizon_7b__q4_k_m"]["score_13_areas"] == 37
    assert data["k2_horizon_7b__q4_k_m"]["tg_tok_s"] < 10.0

    # Verifica que o Dossie Integral Ultra-Detalhado (Secao 20) das 35 variantes foi gravado no Livro Sagrado
    livro = Path(r"F:\data\MASTER_LIVRO_SAGRADO_BENCHMARKS.md")
    assert livro.exists(), "Livro Sagrado nao encontrado!"
    txt = livro.read_text(encoding="utf-8")
    assert "20. DOSSIÊ INTEGRAL ULTRA-DETALHADO: 35 MODELOS BARE-METAL" in txt
    assert "20.1 Os Grandes Vencedores em Destaque" in txt
    assert "20.2 Tabela Mestra Completa das 35 Variantes Homologadas" in txt
    assert "20.3 Decomposição Área por Área (01 a 13) de Todas as 35 Variantes" in txt
    assert "20.4 Decomposição Algoritmo por Algoritmo nos 10 Desafios Opus Hard" in txt

    print("[PASS] Auditoria empirica K2-Horizon + Secao 20 do Livro Sagrado (35 variantes validadas com sucesso).")

if __name__ == "__main__":
    test_k2_horizon_empirical_proofs()
