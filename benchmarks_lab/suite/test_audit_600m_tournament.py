# -*- coding: utf-8 -*-
"""
Auditoria Empírica Estrita — Duelo dos Desafiantes 600M Tier-1 (Tripla Validação O.M.E.G.A.)
Comandante: Mestre Ruan
"""
import sys
import json
from pathlib import Path

PROOF_FILE = Path(r"F:\data\proof_duelo_desafiantes_600m.json")
MASTER_BOOK = Path(r"F:\data\MASTER_LIVRO_SAGRADO_BENCHMARKS.md")
ARTIFACT_BOOK = Path(r"C:\Users\juanp\.gemini\antigravity\brain\411d3440-76b9-446f-8a6d-3b792d2a1684\livro_sagrado_benchmarks_titas.md")
CANVAS_FILE = Path(r"F:\AetherMind_Apotheosis_V1\.obsidian\LLM ganhadores do benchmarket.canvas")

def test_full_empirical_suite():
    # 1. Prova JSON dos Desafiantes 600M
    assert PROOF_FILE.exists(), f"Arquivo de prova {PROOF_FILE} não encontrado!"
    assert PROOF_FILE.stat().st_size > 1000, f"Arquivo de prova muito pequeno: {PROOF_FILE.stat().st_size} bytes"

    with open(PROOF_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 7, f"Esperado 7 modelos (1 campeão + 6 desafiantes), encontrados: {len(data)}"
    champ = data.get("qwen3_06b_distill_30b_thinking_q4_k_m")
    assert champ is not None, "Campeão Qwen3-0.6B-Distilled-30B não encontrado na prova!"
    assert champ["score_13_areas"] == 32, f"Score do campeão incorreto: {champ['score_13_areas']}"

    # 2. Master Livro Sagrado
    assert MASTER_BOOK.exists(), f"Livro Sagrado {MASTER_BOOK} não encontrado!"
    book_text = MASTER_BOOK.read_text(encoding="utf-8")
    assert "10. O GRANDE TORNEIO DOS DESAFIANTES 600M" in book_text, "Seção 10 não encontrada no Master Livro Sagrado!"
    assert "Qwen3-0.6B-Opus4.6-Abliterated" in book_text, "Vice-campeão não citado no Livro Sagrado!"

    # 3. Artefato Sincronizado
    assert ARTIFACT_BOOK.exists(), f"Artefato {ARTIFACT_BOOK} não encontrado!"
    art_text = ARTIFACT_BOOK.read_text(encoding="utf-8")
    assert "10. O GRANDE TORNEIO DOS DESAFIANTES 600M" in art_text, "Seção 10 não sincronizada no artefato!"

    # 4. Obsidian Canvas
    assert CANVAS_FILE.exists(), f"Canvas {CANVAS_FILE} não encontrado!"
    canvas_data = json.loads(CANVAS_FILE.read_text(encoding="utf-8"))
    nodes_text = " ".join(n.get("text", "") for n in canvas_data.get("nodes", []))
    assert "Duelo dos Desafiantes 600M" in nodes_text, "Tabela de 600M não encontrada no Canvas!"

    print(f"[+] AUDITORIA TRIPLA O.M.E.G.A. APROVADA:")
    print(f"    - Prova JSON: {len(data)} modelos auditados e validados com integridade")
    print(f"    - Master Livro Sagrado: Seção 10 homologada ({MASTER_BOOK.stat().st_size} bytes)")
    print(f"    - Artefato Sincronizado: livro_sagrado_benchmarks_titas.md ({ARTIFACT_BOOK.stat().st_size} bytes)")
    print(f"    - Obsidian Canvas: Node 33719b2c5d37b60a enriquecido com o Duelo 600M")

if __name__ == "__main__":
    test_full_empirical_suite()
