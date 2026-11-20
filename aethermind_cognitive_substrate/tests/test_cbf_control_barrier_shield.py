import sys
import os
from pathlib import Path

# Injeta a raiz do repositório em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.metacognition.cbf_control_barrier_shield import CBFControlBarrierShield
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: CBF-QP CONTROL BARRIER SHIELD & RUST HNSW ACCELERATION (ÓRGÃO 30)")
    print("=" * 80)

    shield = CBFControlBarrierShield(state_dim=4, control_dim=4, gamma=2.0)

    # 1. Ação Nominal Segura deve passar com intervenção zero
    x_safe = [0.30, 0.40, 0.35, 0.70]
    u_safe_nom = [0.05, 0.05, 0.02, 0.01]
    res_nom = shield.filter_control_action(x_safe, u_safe_nom)
    assert res_nom["intervened"] is False
    assert res_nom["is_formally_safe"] is True
    assert res_nom["correction_l2_norm"] == 0.0
    print(f" -> [TESTE 1/5]: Ação nominal segura aprovada sem intervenção (Correção L2 = {res_nom['correction_l2_norm']}, Tempo={res_nom['elapsed_us']} us).")

    # 2. Ação Insegura (CPU=0.88, RAM=0.85 perto do limite, comando tentando aumentar +1.5)
    x_edge = [0.88, 0.85, 0.80, 0.90]
    u_unsafe = [1.50, 1.20, 0.90, 0.50]
    res_filtered = shield.filter_control_action(x_edge, u_unsafe)
    assert res_filtered["intervened"] is True
    assert res_filtered["is_formally_safe"] is True
    assert res_filtered["correction_l2_norm"] > 0.1
    assert all(d >= -1e-7 for d in res_filtered["cbf_lie_conditions"])
    print(f" -> [TESTE 2/5]: Ação insegura interceptada e projetada via KKT! Correção L2 = {res_filtered['correction_l2_norm']}, Restrições={res_filtered['active_constraints']}.")

    # 3. Falsificação Adversarial: Violação da Barreira Esférica Acoplada de Lyapunov
    x_high_energy = [0.82, 0.82, 0.82, 0.82]  # ||x||^2 = 2.6896 vs R^2 = 2.7225 (h_global ~ 0.0329)
    u_blast = [0.15, 0.15, 0.15, 0.15]
    res_sphere = shield.filter_control_action(x_high_energy, u_blast)
    assert res_sphere["intervened"] is True
    assert res_sphere["kkt_multiplier_lambda"] > 0.0, "Multiplicador KKT de Lagrange deve ser positivo na barreira esférica!"
    assert res_sphere["is_formally_safe"] is True
    print(f" -> [TESTE 3/5]: Falsificação Adversarial (Barreira Esférica): Multiplicador KKT lambda={res_sphere['kkt_multiplier_lambda']} bloqueou divergência de energia.")

    # 4. Verificação do Runtime Soberano e HNSW Rust FFI ativo
    runtime = SovereignCortexRuntime()
    health = runtime.get_system_health()
    assert health["organs_active_count"] >= 30, f"Esperado >= 30 órgãos, obtido {health['organs_active_count']}"
    assert health["cbf_safety_shield_active"] is True
    assert health["hnsw_rust_baremetal_active"] is True, "Kernel Rust AVX2 do HNSW deve estar acoplado na DLL!"
    print(f" -> [TESTE 4/5]: Córtex v4.0.0 (30 Órgãos) + Kernel Rust HNSW (DLL FFI={health['hnsw_rust_baremetal_active']}) validados.")

    # 5. Despacho via Missão do Córtex Runtime
    mission_res = runtime.execute_cognitive_mission("cbf_safety_filter", {
        "x_state": [0.90, 0.88, 0.82, 0.92],
        "u_nominal": [0.80, 0.80, 0.80, 0.80]
    })
    assert mission_res["result"]["intervened"] is True
    assert mission_res["result"]["is_formally_safe"] is True
    print(f" -> [TESTE 5/5]: Despacho CBF-QP no Córtex Runtime concluído com sucesso ({mission_res['orchestration_overhead_ms']} ms).")

    print("\n[VEREDITO EMPÍRICO]: CBF-QP CONTROL BARRIER SHIELD & HNSW RUST FFI APROVADOS COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
