"""Test Suite — Ciclo 19 (v5.2.0, 54 Órgãos): Rust SMC Kernel + IMM Hybrid Filter (53) + Lyapunov/LQR DARE Certifier (54).

Verifica empiricamente:
1. Prontidão do Córtex v5.2.0 com 54 órgãos determinísticos ativos.
2. Kernel Bare-Metal Rust `smc_quadratic_track_f64` (Órgão 51 acelerado em DLL):
   - Preserva bimodalidade ±2.0 (`multimodal_detected == True`) e entrega speedup empírico
     real contra o caminho puro em NumPy para 1.024 partículas x 20 passos.
3. IMMRegimeSwitchingFilter (Órgão 53):
   - Rastreia transição de regime nominal suave para manobra abrupta de aceleração,
     elevando a probabilidade de modo manobra > 0.70 e detectando os passos da comutação.
4. LyapunovSDPStabilityCertifier (Órgão 54):
   - Resolve A^T P A - P = -Q por duplicação de Smith com resíduo Frobenius < 1e-10;
   - Rejeita planta originalmente instável (rho > 1.0), sintetiza controlador LQR ótimo via
     DARE e certifica estabilidade assintótica de Lyapunov da malha fechada A - B K.
"""
import os
import sys
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
from aethermind_cognitive_substrate.planning.particle_filter_smc import ParticleFilterSMCEngine


def main() -> int:
    print("=" * 82)
    print("[CICLO 19 — 54 ÓRGÃOS] RUST SMC KERNEL + IMM REGIME FILTER (53) + LYAPUNOV DARE (54)")
    print("=" * 82)

    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY", health
    assert health["organs_active_count"] >= 54, f"Esperado >= 54 órgãos, obtido {health['organs_active_count']}"
    assert health["imm_regime_switching_filter_active"] is True
    assert health["lyapunov_sdp_stability_certifier_active"] is True
    print(f"[PASS] Córtex {health['version']} pronto com {health['organs_active_count']} órgãos.")

    # 1. Benchmark Rust Bare-Metal SMC vs NumPy Python (1024 partículas x 20 passos)
    bench_smc = ParticleFilterSMCEngine(num_particles=1024, state_dim=1, resample_ratio=0.5, seed=202619)
    obs_smc = [4.0 + 0.05 * ((i % 3) - 1) for i in range(20)]
    res_rust = bench_smc.track_sequence(obs_smc, prefer_native=True)
    res_py = bench_smc.track_sequence(obs_smc, prefer_native=False)

    assert "Rust" in res_rust.get("backend", ""), res_rust
    assert res_rust["multimodal_detected"] is True, res_rust
    modes = res_rust["final_dominant_modes_dim0"]
    assert any(1.3 <= m["center"] <= 2.7 for m in modes) and any(-2.7 <= m["center"] <= -1.3 for m in modes), modes
    speedup = res_py["elapsed_ms"] / max(res_rust["elapsed_ms"], 1e-6)
    assert speedup > 1.5, f"Speedup Rust SMC inesperado: {speedup:.2f}x (Rust={res_rust['elapsed_ms']}ms, Py={res_py['elapsed_ms']}ms)"
    print(
        f"[PASS] Rust LTO SMC (1024p x 20t): {res_rust['elapsed_ms']} ms vs NumPy {res_py['elapsed_ms']} ms "
        f"({speedup:.2f}x speedup) | modos={modes}"
    )

    # 2. Órgão 53 — IMMRegimeSwitchingFilter: detecção de comutação de regime nominal -> manobra
    hybrid_obs = [0.0, 0.01, 0.02, 0.03, 0.04, 0.05, 0.65, 1.55, 2.75, 4.20, 5.90, 7.80]
    imm_res = cortex.execute_cognitive_mission(
        "imm_regime_track",
        {"observations": hybrid_obs, "maneuver_prob_threshold": 0.50},
    )["result"]
    assert imm_res["status"] == "IMM_HYBRID_REGIME_TRACKED", imm_res
    assert imm_res["peak_maneuver_probability"] > 0.70, f"Probabilidade de manobra baixa: {imm_res}"
    assert len(imm_res["maneuver_steps_detected"]) >= 1, imm_res
    assert any(step >= 6 for step in imm_res["maneuver_steps_detected"]), imm_res
    print(
        f"[PASS] Órgão 53 (IMM Hybrid Filter): pico manobra={imm_res['peak_maneuver_probability']} | "
        f"steps={imm_res['maneuver_steps_detected']} | RMSE={imm_res['tracking_rmse_vs_raw_obs']} | {imm_res['elapsed_us']} us"
    )

    # 3. Órgão 54 — LyapunovSDPStabilityCertifier (Stein Cert + Falsificação Instável + Síntese DARE)
    stable_cert = cortex.execute_cognitive_mission(
        "lyapunov_lqr_certify",
        {"mode": "certify_only", "A": [[0.85, 0.10], [-0.05, 0.78]]},
    )["result"]
    assert stable_cert["status"] == "LYAPUNOV_STABILITY_CERTIFIED", stable_cert
    assert stable_cert["asymptotically_stable"] is True
    assert stable_cert["positive_definite_P"] is True
    assert stable_cert["stein_residual_fro"] < 1e-10

    unstable_cert = cortex.execute_cognitive_mission(
        "lyapunov_lqr_certify",
        {"mode": "certify_only", "A": [[1.15, 0.20], [0.0, 1.05]]},
    )["result"]
    assert unstable_cert["status"] == "LYAPUNOV_UNSTABLE_SYSTEM", unstable_cert
    assert unstable_cert["asymptotically_stable"] is False

    lqr_res = cortex.execute_cognitive_mission(
        "lyapunov_lqr_certify",
        {"mode": "lqr_synthesize", "A": [[1.15, 0.20], [0.0, 1.05]], "B": [[0.0], [1.0]]},
    )["result"]
    assert lqr_res["status"] == "LQR_DARE_STABILIZED_AND_CERTIFIED", lqr_res
    assert lqr_res["dare_converged"] is True
    assert lqr_res["open_loop_spectral_radius"] > 1.0
    assert lqr_res["closed_loop_spectral_radius"] < 1.0
    assert lqr_res["closed_loop_lyapunov_certified"] is True
    assert lqr_res["closed_loop_stein_residual"] < 1e-9
    print(
        f"[PASS] Órgão 54 (Lyapunov + DARE LQR): rho_open={lqr_res['open_loop_spectral_radius']} -> "
        f"rho_cl={lqr_res['closed_loop_spectral_radius']} | resíduo={lqr_res['closed_loop_stein_residual']} | "
        f"K={lqr_res['optimal_gain_K']} em {lqr_res['elapsed_us']} us"
    )

    print("=" * 82)
    print("SUCESSO ABSOLUTO: TODOS OS 54 ÓRGÃOS E INVARIANTES DO CICLO 19 VERIFICADOS!")
    print("=" * 82)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
