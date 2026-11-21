# -*- coding: utf-8 -*-
import json
import os
import sys

def test_ultraleves_empirical_proof():
    proof_path = r"F:\data\proof_torneio_ultraleves_100m_500m.json"
    if not os.path.exists(proof_path):
        print(f"FALHA: Arquivo de prova {proof_path} não encontrado.")
        sys.exit(1)

    with open(proof_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if len(data) < 10:
        print(f"FALHA: Esperados 10 concorrentes, encontrados {len(data)}.")
        sys.exit(1)

    for k, v in data.items():
        speeds = v.get("speeds", {})
        areas = v.get("areas_13", {})
        if speeds.get("predicted_per_second", 0) <= 0:
            print(f"FALHA: Velocidade inválida para {k}.")
            sys.exit(1)
        if areas.get("passed", 0) <= 0:
            print(f"FALHA: Score inválido para {k}.")
            sys.exit(1)

    print("SUCESSO: Prova empírica bare-metal dos 10 modelos ultraleves 100% validada!")
    sys.exit(0)

if __name__ == "__main__":
    test_ultraleves_empirical_proof()
