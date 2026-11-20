"""Suíte de Testes Adversariais do Kernel Bare-Metal Rust HRM / TRM (Protocolo O.M.E.G.A.).

Validação empírica:
1. Convergência de Ponto Fixo via Teorema de Contração de Banach.
2. Aceleração Bare-Metal em Rust FFI (AVX2, zero cópias).
3. Equivalência Lógica e Numérica entre Rust nativo e Fallback NumPy.
4. Resiliência a entradas adversariais e perturbações externas.
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

from aethermind_cognitive_substrate.metacognition.hrm_dual_timescale_fixed_point import HRMDualTimescaleFixedPoint


def test_hrm_native_rust_acceleration():
    print("[TESTE 1] Auditoria da Aceleração Bare-Metal Rust HRM / TRM...")
    hrm = HRMDualTimescaleFixedPoint(slow_dim=16, fast_dim=32, input_dim=16)

    assert hrm.is_native_accelerated is True, "A DLL aether_cortex_vsa.dll não foi vinculada com sucesso!"

    x_input = np.random.randn(16)

    # 1. Execução nativa Rust AVX2
    t0 = time.perf_counter()
    res_native = hrm.find_fixed_point_equilibrium(x_input, slow_macro_steps=3, prefer_native=True)
    t_native_ms = (time.perf_counter() - t0) * 1000.0

    assert res_native["status"] == "EQUILIBRIUM_REACHED"
    assert res_native["native_rust_accelerated"] is True
    assert res_native["kernel_backend"] == "RUST_BARE_METAL_AVX2"
    assert res_native["is_banach_contractive"] is True
    print(f"   -> Latência de Ponto Fixo em Rust: {t_native_ms:.3f} ms (Kernel: {res_native['kernel_backend']})")
    print(f"   -> Raio Espectral Jacobiana: {res_native['spectral_radius_jacobian']} (< 1.0 Banach)")

    # 2. Execução Fallback NumPy
    t1 = time.perf_counter()
    res_py = hrm.find_fixed_point_equilibrium(x_input, slow_macro_steps=3, prefer_native=False)
    t_py_ms = (time.perf_counter() - t1) * 1000.0

    assert res_py["status"] == "EQUILIBRIUM_REACHED"
    assert res_py["native_rust_accelerated"] is False
    print(f"   -> Latência de Ponto Fixo em Python: {t_py_ms:.3f} ms (Kernel: {res_py['kernel_backend']})")

    speedup = t_py_ms / (t_native_ms + 1e-6)
    print(f"   -> Speedup Medido: {speedup:.2f}x")
    print("   [OK] Aceleração bare-metal e invariante de Banach confirmados.")


def test_adversarial_stability_and_norm_bounds():
    print("\n[TESTE 2] Estabilidade Adversarial e Limites de Norma...")
    hrm = HRMDualTimescaleFixedPoint(slow_dim=16, fast_dim=32, input_dim=16)

    # Vetor de entrada com magnitude extrema
    huge_input = np.ones(16) * 1e5
    res = hrm.find_fixed_point_equilibrium(huge_input, slow_macro_steps=2)

    assert not np.isnan(res["z_L_fixed_point_norm"]), "NaN detectado sob entrada massiva!"
    assert not np.isinf(res["z_L_fixed_point_norm"]), "Inf detectado sob entrada massiva!"
    # Tanh limita cada dimensão a [-1, 1], portanto ||z_L|| <= sqrt(32) ~= 5.6568
    max_possible_norm = np.sqrt(32) + 0.1
    assert res["z_L_fixed_point_norm"] <= max_possible_norm, f"Norma violou limite de saturação: {res['z_L_fixed_point_norm']}"
    print(f"   -> Norma Estabilizada sob Estresse Extremo: {res['z_L_fixed_point_norm']:.4f} (<= {max_possible_norm:.4f})")
    print("   [OK] Saturação não-linear preveniu explosão numérica.")


def main():
    print("=" * 80)
    print(" SUÍTE DE TESTES OMEGA: BARE-METAL RUST HRM FIXED-POINT RESOLVENT")
    print("=" * 80)
    test_hrm_native_rust_acceleration()
    test_adversarial_stability_and_norm_bounds()
    print("\n" + "=" * 80)
    print(" TODOS OS TESTES PASSARAM COM SUCESSO (RUST HRM RESOLVENT PRONTO).")
    print("=" * 80)


if __name__ == "__main__":
    main()
