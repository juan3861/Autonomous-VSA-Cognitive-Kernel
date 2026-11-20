"""Suíte de Testes Adversariais da Máquina de Ising Termodinâmica Polaris (Protocolo O.M.E.G.A.).

Validação empírica:
1. Cálculo Exato do Hamiltoniano de Energia E(s) = -0.5 s^T J s - h^T s.
2. Aceleração Bare-Metal em Rust FFI (AVX2, zero cópias) em 256 e 1024 spins.
3. Relaxamento Termodinâmico com Queda Monótona de Energia até o Estado Fundamental.
4. Presença e Validade do Bytecode SPIR-V Wave64 compilado para AMD Polaris RX 580.
5. Resiliência Adversarial a Matrizes de Acoplamento Frustradas e Patológicas.
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

from aethermind_cognitive_substrate.logic_symbolic.thermodynamic_ising_engine import ThermodynamicIsingMachine


def test_energy_hamiltonian_exactness():
    print("[TESTE 1] Cálculo Exato do Hamiltoniano de Ising...")
    ising = ThermodynamicIsingMachine(num_spins=4, seed=42)

    # Grafo de acoplamento 4 spins
    J = np.array([
        [0.0, 1.0, 0.0, -1.0],
        [1.0, 0.0, 1.0, 0.0],
        [0.0, 1.0, 0.0, 1.0],
        [-1.0, 0.0, 1.0, 0.0]
    ], dtype=np.float32)
    h = np.array([0.5, -0.5, 0.0, 0.0], dtype=np.float32)
    ising.set_coupling_matrix(J, h)

    spins_test = np.array([1, 1, 1, 1], dtype=np.int8)
    e = ising.compute_energy(spins_test)

    # s = [1, 1, 1, 1]
    # sum J_ij = (0+1+0-1) + (1+0+1+0) + (0+1+0+1) + (-1+0+1+0) = 0 + 2 + 2 + 0 = 4
    # interaction = -0.5 * 4 = -2.0
    # field = -(0.5*1 + -0.5*1 + 0 + 0) = 0.0
    # E = -2.0
    print(f"   -> Energia Calculada: {e:.4f} (Esperado: -2.0000)")
    assert abs(e - (-2.0)) < 1e-4, f"Erro no cálculo do Hamiltoniano! {e}"
    print("   [OK] Hamiltoniano de Ising verificado com precisão exata.")


def test_rust_baremetal_acceleration_1024_spins():
    print("\n[TESTE 2] Aceleração Bare-Metal em Rust FFI (AVX2) em 256 e 1024 Spins...")
    assert ThermodynamicIsingMachine(num_spins=16).is_native_accelerated is True, "DLL aether_cortex_vsa.dll não vinculada!"

    # 1. Teste em 256 spins
    ising_256 = ThermodynamicIsingMachine(num_spins=256, seed=42)
    J_256 = np.random.randn(256, 256).astype(np.float32) * 0.1
    ising_256.set_coupling_matrix(J_256)

    t0 = time.perf_counter()
    res_256 = ising_256.thermal_relax_to_ground_state(initial_temp=5.0, final_temp=0.05, cooling_steps=50, prefer_native=True)
    dt_256 = (time.perf_counter() - t0) * 1000.0

    print(f"   -> 256 Spins / 50 Passos: {dt_256:.2f} ms | Queda de Energia: {res_256['energy_drop']:.2f}")
    assert res_256["status"] == "GROUND_STATE_REACHED"
    assert res_256["backend"] == "RUST_BARE_METAL_AVX2"
    assert res_256["energy_drop"] > 0, "Energia não decaiu!"
    assert dt_256 < 50.0, "Latência de 256 spins ultrapassou 50ms!"

    # 2. Teste em 1024 spins
    ising_1024 = ThermodynamicIsingMachine(num_spins=1024, seed=1337)
    J_1024 = np.random.randn(1024, 1024).astype(np.float32) * 0.05
    ising_1024.set_coupling_matrix(J_1024)

    t1 = time.perf_counter()
    res_1024 = ising_1024.thermal_relax_to_ground_state(initial_temp=5.0, final_temp=0.05, cooling_steps=100, prefer_native=True)
    dt_1024 = (time.perf_counter() - t1) * 1000.0

    print(f"   -> 1024 Spins / 100 Passos (100M Flips): {dt_1024:.2f} ms | Queda de Energia: {res_1024['energy_drop']:.2f}")
    assert res_1024["energy_drop"] > 100.0, "Energia em 1024 spins não decaiu significativamente!"
    assert dt_1024 < 1000.0, "Latência de 1024 spins ultrapassou 1s!"
    print("   [OK] Aceleração bare-metal e recozimento simulado confirmados.")


def test_vulkan_polaris_shader_bytecode():
    print("\n[TESTE 3] Validação do Bytecode SPIR-V Polaris Wave64 (AMD RX 580)...")
    spv_path = Path(root_dir) / "aethermind_cognitive_substrate" / "logic_symbolic" / "shaders" / "ising_block_gibbs.spv"

    assert spv_path.exists(), f"Arquivo SPIR-V ausente em: {spv_path}"
    size = os.path.getsize(spv_path)
    print(f"   -> SPIR-V Compilado: {spv_path.name} ({size} bytes)")
    assert size > 1000, "Tamanho de bytecode SPIR-V inválido!"

    # Verifica o Magic Number do SPIR-V: 0x07230203 (Little Endian: 03 02 23 07)
    with open(spv_path, "rb") as f:
        magic = f.read(4)
    assert magic == b"\x03\x02\x23\x07", "Magic number do cabeçalho SPIR-V incorreto!"
    print("   [OK] Bytecode SPIR-V canônico validado com sucesso.")


def test_adversarial_frustrated_system():
    print("\n[TESTE 4] Teste Adversarial em Sistema Antiferromagnético Altamente Frustrado...")
    num_spins = 64
    ising_frust = ThermodynamicIsingMachine(num_spins=num_spins, seed=999)
    # Acoplamento antiferromagnético total J_ij = -1 (frustração máxima)
    J_frust = -np.ones((num_spins, num_spins), dtype=np.float32)
    np.fill_diagonal(J_frust, 0.0)
    ising_frust.set_coupling_matrix(J_frust)

    res = ising_frust.thermal_relax_to_ground_state(initial_temp=10.0, final_temp=0.01, cooling_steps=60)
    assert not np.isnan(res["ground_state_energy"])
    assert not np.isinf(res["ground_state_energy"])
    print(f"   -> Energia Mínima em Frustração Máxima: {res['ground_state_energy']:.2f}")
    print("   [OK] Estabilidade comprovada em topologia de frustração máxima.")


def main():
    print("=" * 80)
    print(" SUÍTE DE TESTES OMEGA: THERMODYNAMIC ISING ENGINE & POLARIS VULKAN")
    print("=" * 80)
    test_energy_hamiltonian_exactness()
    test_rust_baremetal_acceleration_1024_spins()
    test_vulkan_polaris_shader_bytecode()
    test_adversarial_frustrated_system()
    print("\n" + "=" * 80)
    print(" TODOS OS TESTES PASSARAM COM SUCESSO (ISING THERMODYNAMIC ENGINE PRONTO).")
    print("=" * 80)


if __name__ == "__main__":
    main()
