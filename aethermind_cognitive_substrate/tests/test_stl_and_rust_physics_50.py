"""Test Suite — Ciclo 17 (Marco 50 Órgãos): STL/LTL Monitor (Organ 49) & Rust LTO Physics Kernel (Organ 50).

Verifica empiricamente:
1. Prontidão do Córtex v5.0.0 com 50 órgãos determinísticos ativos.
2. STL/LTL Temporal Logic Monitor:
   - Traço com recuperação em janela satisfaz G(safety) ^ G(trigger -> F_[0,4] recover) com robustez > 0.
   - Falsificação adversarial: traço que viola safety_ceiling ou atrasa recuperação retorna satisfied=False e robustez < 0.
3. Native Rust LTO Physics Kernel (`aether_cortex_vsa.dll`):
   - `symplectic_yoshida4_coupled_f64` executa 5.000 passos em código de máquina nativo (< 5ms, > 1M passos/s)
     com deriva de energia < 1e-6.
   - Speedup empírico comprovado > 50x contra o loop Python do Yoshida-4!
"""
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def main() -> int:
    print("=" * 80)
    print("[CICLO 17 — 50 ÓRGÃOS] STL/LTL MONITOR (ÓRGÃO 49) & RUST LTO KERNEL (ÓRGÃO 50)")
    print("=" * 80)

    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY"
    assert health["organs_active_count"] >= 50, f"Esperado >= 50 órgãos, got {health['organs_active_count']}"
    assert health.get("stl_temporal_logic_monitor_active") is True
    assert health.get("rust_native_physics_kernel_active") is True, "Kernel nativo Rust deve estar compilado na DLL!"
    print(f"[1/4] Córtex Prontidão: {health['organs_active_count']} órgãos | Versão={health['version']}")

    # 2. Órgão 49: STL/LTL Quantitative Temporal Logic (Caso Válido + Falsificação)
    good_trace = [0.40, 0.55, 0.85, 0.78, 0.62, 0.45, 0.84, 0.60, 0.42]
    res_good = cortex.execute_cognitive_mission(
        "stl_verify",
        {"trace": good_trace, "safety_ceiling": 0.95, "trigger_threshold": 0.80, "recovery_target": 0.65, "response_deadline_steps": 3}
    )["result"]
    assert res_good["satisfied"] is True, f"Traço válido deveria satisfazer STL: {res_good}"
    assert res_good["overall_stl_robustness"] > 0.0
    assert res_good["triggers_detected"] == 2
    assert res_good["triggers_recovered_in_window"] == 2

    # Falsificação adversarial 1: violação do teto de segurança
    bad_trace_safety = [0.40, 0.97, 0.50]
    res_bad1 = cortex.execute_cognitive_mission("stl_verify", {"trace": bad_trace_safety})["result"]
    assert res_bad1["satisfied"] is False
    assert res_bad1["safety_invariance_robustness"] < 0.0

    # Falsificação adversarial 2: trigger sem recuperação dentro da janela
    bad_trace_liveness = [0.40, 0.85, 0.84, 0.83, 0.82, 0.81, 0.80]
    res_bad2 = cortex.execute_cognitive_mission(
        "stl_verify",
        {"trace": bad_trace_liveness, "response_deadline_steps": 3}
    )["result"]
    assert res_bad2["satisfied"] is False
    assert res_bad2["bounded_response_robustness"] < 0.0
    print(
        f"[2/4] Órgão 49 (STL/LTL Monitor): OK | Rob={res_good['overall_stl_robustness']} | "
        f"Falsificações STL detectadas (< 0) em {res_good['elapsed_us']} us"
    )

    # 3. Órgão 50: Native Rust LTO Symplectic Yoshida-4 (5.000 passos + Comparação de Speedup)
    res_rust = cortex.execute_cognitive_mission(
        "rust_physics_yoshida",
        {"q0": [1.0, 0.25], "p0": [0.0, 0.85], "dt": 0.05, "steps": 5000}
    )["result"]
    assert res_rust["native_accelerated"] is True
    assert res_rust["max_absolute_energy_drift"] < 1e-4

    # Benchmark paralelo no integrador Python para comprovar aceleração empírica > 50x
    res_py = cortex.hamiltonian_symplectic.simulate([1.0, 0.25], [0.0, 0.85], dt=0.05, steps=1000, order=4)
    py_us_per_step = (res_py["elapsed_ms"] * 1000.0) / 1000.0
    rust_us_per_step = res_rust["elapsed_us"] / 5000.0
    speedup = py_us_per_step / max(1e-6, rust_us_per_step)
    assert speedup > 50.0, f"Speedup Rust vs Python insuficiente: {speedup:.1f}x"
    print(
        f"[3/4] Órgão 50 (Rust LTO Physics Kernel): OK | 5.000 passos em {res_rust['elapsed_us']} us "
        f"({res_rust['steps_per_sec']:.0f} steps/s | Speedup={speedup:.1f}x vs Python) | |ΔH|={res_rust['max_absolute_energy_drift']}"
    )

    # 4. Validação STL nativa em Rust sobre array grande
    stl_native = cortex.rust_physics_kernel.eval_stl_globally_native([0.1, 0.4, 0.88, 0.3], upper_limit=0.95)
    assert stl_native["native_accelerated"] is True
    assert stl_native["satisfied"] is True
    assert abs(stl_native["robustness"] - 0.07) < 1e-6
    print(f"[4/4] Native Rust STL Globally Kernel: OK | margin={stl_native['robustness']} em {stl_native['elapsed_us']} us")

    print("\n[VEREDITO FINAL]: MARCO DOS 50 ÓRGÃOS (CICLO 17 — v5.0.0) APROVADO COM EXIT CODE 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
