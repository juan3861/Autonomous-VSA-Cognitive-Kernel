"""Suíte de Testes Adversariais do Motor KAN B-Spline Adaptativo (Protocolo O.M.E.G.A.).

Validação empírica:
1. Partição da Unidade Exata: sum_j B_j(x) = 1.0 em todo o domínio [-1, 1].
2. Ajuste Fechado em 1-Shot de Função Não-Linear Multivariada com R2 > 0.995.
3. Extração Simbólica Analítica e Poda de Arestas Inativas (L1 Regularization).
4. Resiliência Adversarial a Entradas nos Limites e Fora do Domínio.
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

from aethermind_cognitive_substrate.logic_symbolic.kan_adaptive_bspline import AdaptiveBSplineKANEngine


def test_partition_of_unity():
    print("[TESTE 1] Partição da Unidade dos B-Splines Cúbicos (Cox-de Boor)...")
    kan = AdaptiveBSplineKANEngine(in_features=2, out_features=1, grid_intervals=6, spline_degree=3)

    x_points = np.linspace(-1.0, 1.0, 200)
    bases = kan._compute_b_spline_bases(x_points)

    assert bases.shape == (200, 9), f"Dimensão incorreta: {bases.shape}"
    sums = np.sum(bases, axis=1)
    min_sum, max_sum = float(np.min(sums)), float(np.max(sums))

    print(f"   -> Soma Mínima: {min_sum:.14f} | Soma Máxima: {max_sum:.14f}")
    assert np.allclose(sums, 1.0, atol=1e-12), "Falha na Partição da Unidade dos B-splines!"
    print("   [OK] Partição da unidade 100% exata comprovada.")


def test_1shot_nonlinear_fit():
    print("\n[TESTE 2] Ajuste em 1-Shot Fechado de Função Não-Linear Multivariada...")
    np.random.seed(1337)
    N = 600

    # Função ground-truth complexa não-linear:
    # y = exp(sin(pi * x0)) + x1**2 - 0.5 * x2
    X = np.random.uniform(-1.0, 1.0, size=(N, 3))
    y = np.exp(np.sin(np.pi * X[:, 0])) + (X[:, 1] ** 2) - 0.5 * X[:, 2]

    kan = AdaptiveBSplineKANEngine(in_features=3, out_features=1, grid_intervals=8, spline_degree=3)
    res = kan.fit_closed_form_1shot(X, y, lambda_reg=1e-5)

    print(f"   -> Tempo de Ajuste Analítico: {res['elapsed_ms']} ms")
    print(f"   -> MSE: {res['mse']:.6f} | R2 Score: {res['r2_score']:.6f}")

    assert res["status"] == "FIT_CONVERGED_1SHOT"
    assert res["r2_score"] > 0.995, f"R2 insuficiente: {res['r2_score']}"
    assert res["mse"] < 0.005, f"MSE muito alto: {res['mse']}"
    print("   [OK] Aproximação exata alcançada sem gradient descent.")


def test_symbolic_extraction_and_pruning():
    print("\n[TESTE 3] Extração Simbólica Analítica e Poda de Arestas...")
    np.random.seed(42)
    N = 300
    # Entrada com variável irrelevante X1
    X = np.random.uniform(-1.0, 1.0, size=(N, 2))
    y = 2.0 * (X[:, 0] ** 2)  # Apenas X0 afeta y, X1 é ruído

    kan = AdaptiveBSplineKANEngine(in_features=2, out_features=1, grid_intervals=5)
    kan.fit_closed_form_1shot(X, y, lambda_reg=1e-4)

    sig = kan.compute_edge_significance()
    print(f"   -> Significância da Aresta X0: {sig[0, 0]:.4f} | Aresta X1 (Inativa): {sig[0, 1]:.4f}")
    assert sig[0, 0] > sig[0, 1] * 2.0, "Falha na diferenciação de significância causal da aresta!"

    formulas = kan.extract_symbolic_formulas(significance_threshold=sig[0, 1] + 0.1)
    print(f"   -> Fórmula Extraída: {formulas[0]}")
    assert "x_0" in formulas[0]
    print("   [OK] Extração analítica e discriminação de aresta comprovadas.")


def test_adversarial_boundaries():
    print("\n[TESTE 4] Teste Adversarial nos Limites Extremos...")
    kan = AdaptiveBSplineKANEngine(in_features=2, out_features=1)
    # Entradas fora do domínio [-1, 1]
    X_extreme = np.array([[-500.0, 500.0], [1e8, -1e8]])
    Y_pred = kan.forward(X_extreme)

    assert not np.isnan(Y_pred).any(), "NaN detectado em entrada extrema!"
    assert not np.isinf(Y_pred).any(), "Inf detectado em entrada extrema!"
    print(f"   -> Saídas Estáveis sob Extremos: {Y_pred.flatten()}")
    print("   [OK] Clamping defensivo preveniu falhas numéricas.")


def main():
    print("=" * 80)
    print(" SUÍTE DE TESTES OMEGA: ADAPTIVE CUBIC B-SPLINE KAN ENGINE")
    print("=" * 80)
    test_partition_of_unity()
    test_1shot_nonlinear_fit()
    test_symbolic_extraction_and_pruning()
    test_adversarial_boundaries()
    print("\n" + "=" * 80)
    print(" TODOS OS TESTES PASSARAM COM SUCESSO (KAN 2.0 B-SPLINE PRONTO).")
    print("=" * 80)


if __name__ == "__main__":
    main()
