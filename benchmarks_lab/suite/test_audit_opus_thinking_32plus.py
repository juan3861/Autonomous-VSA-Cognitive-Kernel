# -*- coding: utf-8 -*-
"""
Auditoria Empírica Estrita — Duelo Opus Hard (Modo Pensante Ativo + Lambda-RLM)
Para os 4 Campeões 600M com >= 32 acertos nas 13 Áreas Cognitivas.
Comandante: Mestre Ruan
"""
import json
from pathlib import Path

PROOF_FILE = Path(r"F:\data\proof_opus_thinking_lambda_campeoes_32plus.json")
MAIN_QUANTS_PROOF = Path(r"F:\data\proof_quants_3_campeoes_600m.json")
MASTER_BOOK = Path(r"F:\data\MASTER_LIVRO_SAGRADO_BENCHMARKS.md")
ARTIFACT_BOOK = Path(r"C:\Users\juanp\.gemini\antigravity\brain\411d3440-76b9-446f-8a6d-3b792d2a1684\livro_sagrado_benchmarks_titas.md")
CANVAS_FILE = Path(r"F:\AetherMind_Apotheosis_V1\.obsidian\LLM ganhadores do benchmarket.canvas")

def test_opus_thinking_proof():
    assert PROOF_FILE.exists(), f"Prova {PROOF_FILE} não encontrada!"
    assert PROOF_FILE.stat().st_size > 2000, f"Prova {PROOF_FILE} muito pequena!"

    data = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
    expected = [
        "tinyqwen3_distill_06b__q5_k_m",
        "tinyqwen3_distill_06b__q6_k",
        "qwen3_06b_distill_30b__q4_k_m",
        "qwen3_06b_opus46__q8_0",
    ]
    for cid in expected:
        assert cid in data, f"Campeão {cid} ausente na prova!"
        entry = data[cid]
        assert entry.get("completed") is True, f"{cid} incompleto!"
        assert entry.get("score_13_areas", 0) >= 32, f"{cid} abaixo de 32 acertos!"
        details = entry.get("details_opus", {}).get("details", {})
        assert len(details) == 10, f"{cid} sem os 10 testes Opus! Encontrados: {len(details)}"
        for tid, det in details.items():
            assert det.get("thought_and_code_tokens", 0) > 500, f"Tokens insuficientes em {cid}/{tid}"
            assert "Bloco de código Python vazio" not in det.get("result", ""), f"Timeout/bloco vazio em {cid}/{tid}"

    # Verifica sincronia no proof principal
    assert MAIN_QUANTS_PROOF.exists()
    mdata = json.loads(MAIN_QUANTS_PROOF.read_text(encoding="utf-8"))
    for cid in expected:
        assert "details_opus_thinking_lambda" in mdata[cid], f"{cid} não atualizado em {MAIN_QUANTS_PROOF}"

    # Verifica Livro Sagrado, Artefato e Canvas
    book_text = MASTER_BOOK.read_text(encoding="utf-8")
    assert "12. AUDITORIA OPUS HARD COM MODO PENSANTE ATIVO" in book_text, "Seção 12 ausente no Livro Sagrado!"
    art_text = ARTIFACT_BOOK.read_text(encoding="utf-8")
    assert "12. AUDITORIA OPUS HARD COM MODO PENSANTE ATIVO" in art_text, "Seção 12 ausente no Artefato!"
    canvas_text = CANVAS_FILE.read_text(encoding="utf-8")
    assert "Auditoria Opus Hard (Modo Pensante Ativo" in canvas_text, "Tabela Opus Thinking ausente no Canvas!"

    print(f"[+] AUDITORIA O.M.E.G.A. APROVADA: 4 campeões (>=32/39) x 10 desafios Opus em Modo Pensante Ativo + Lambda-RLM validados!")

if __name__ == "__main__":
    test_opus_thinking_proof()
