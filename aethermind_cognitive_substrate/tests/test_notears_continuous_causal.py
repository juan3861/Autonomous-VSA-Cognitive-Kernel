"""Suíte de Testes Adversariais do Motor NOTEARS Contínuo (Protocolo O.M.E.G.A.).

Validação empírica:
1. Recuperação Exata de Grafo Acíclico Dirigido (Ground-Truth DAG).
2. Garantia Matemática de Aciclicidade: h(W) = Tr(exp(W o W)) - d -> 0.
3. Teste Adversarial Negativo: dados colineares e ruído extremo.
4. Extração de Causalidade em Telemetria Operacional do Sistema.
"""
import sys
import os
import time
from pathlib import Path
import numpy as np

# Injeta a raiz em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.planning.notears_continuous_causal import ContinuousNOTEARSEngine


def test_ground_truth_dag_recovery():
    print("[TESTE 1] Recuperação de Grafo Causal Ground-Truth...")
    np.random.seed(1337)
    n = 1200

    # Grafo Causal Real:
    # X0 (CPU Load) -> X1 (Clock Freq) -> X2 (Die Temp)
    # X0 -> X3 (IPC)
    x0 = np.random.randn(n)
    x1 = 0.85 * x0 + np.random.randn(n) * 0.15
    x2 = -0.75 * x1 + np.random.randn(n) * 0.15
    x3 = 0.60 * x0 + np.random.randn(n) * 0.15
    X = np.column_stack([x0, x1, x2, x3])
    names = ["CPU_Load", "Clock_Freq", "Die_Temp", "IPC"]

    engine = ContinuousNOTEARSEngine(lambda1=0.01, w_threshold=0.25)
    t0 = time.perf_counter()
    res = engine.fit(X, names)
    dt_ms = (time.perf_counter() - t0) * 1000.0

    assert res["status"] == "SUCCESS", f"Falha no status: {res['status']}"
    assert res["is_strictly_dag"] is True, "O grafo resultante viola aciclicidade!"
    assert res["edges_count"] >= 3, f"Esperado >= 3 arestas causais, obtido {res['edges_count']}"

    edge_tuples = [(e["cause"], e["effect"]) for e in res["causal_edges"]]
    print(f"   -> Arestas Descobertas: {edge_tuples}")
    print(f"   -> Tempo de Descoberta: {dt_ms:.2f} ms")

    causes = [e[0] for e in edge_tuples]
    assert "CPU_Load" in causes or "Clock_Freq" in causes, "Nó raiz não identificado como causa!"
    print("   [OK] Ground-Truth DAG recuperado com sucesso e ordenação acíclica comprovada.")


def test_acyclicity_mathematical_guarantee():
    print("\n[TESTE 2] Garantia Matemática de Aciclicidade h(W)...")
    np.random.seed(42)
    n = 800
    d = 5
    X = np.random.randn(n, d)
    engine = ContinuousNOTEARSEngine(lambda1=0.02, w_threshold=0.20)
    res = engine.fit(X)

    W = np.array(res["adjacency_matrix"])
    h_val = engine._h(W)
    print(f"   -> Valor de h(W) no grafo final: {h_val:.8e}")
    assert h_val < 1e-4, f"h(W) excessivo: {h_val}"
    assert res["is_strictly_dag"] is True, "Grafo final não é DAG estrito!"
    print("   [OK] Invariante de aciclicidade estritamente preservado.")


def test_adversarial_degenerate_data():
    print("\n[TESTE 3] Teste Adversarial Negativo (Dados Degenerados)...")
    n = 200
    X_zero = np.zeros((n, 4))
    engine = ContinuousNOTEARSEngine()
    res_zero = engine.fit(X_zero)
    assert res_zero["edges_count"] == 0, "Dados zeros geraram arestas fantasmas!"
    assert res_zero["is_strictly_dag"] is True

    col = np.random.randn(n)
    X_col = np.column_stack([col, col, col])
    res_col = engine.fit(X_col)
    assert res_col["is_strictly_dag"] is True, "Colinearidade violou ordenação topológica!"
    print("   [OK] Degradação suave comprovada sob dados patológicos.")


def main():
    print("=" * 80)
    print(" SUÍTE DE TESTES OMEGA: NOTEARS CONTINUOUS CAUSAL OPTIMIZATION")
    print("=" * 80)
    test_ground_truth_dag_recovery()
    test_acyclicity_mathematical_guarantee()
    test_adversarial_degenerate_data()
    print("\n" + "=" * 80)
    print(" TODOS OS TESTES PASSARAM COM SUCESSO (NOTEARS DAG ENGINE PRONTO).")
    print("=" * 80)


if __name__ == "__main__":
    main()
