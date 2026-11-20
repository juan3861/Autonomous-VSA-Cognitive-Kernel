"""Test Suite — Ciclo 18 (v5.1.0, 52 Órgãos): SMC Particle Filter (Organ 51) & Multi-Agent Lock-Free mmap+STL Coordinator (Organ 52).

Verifica empiricamente:
1. Prontidão do Córtex v5.1.0 com 52 órgãos determinísticos ativos.
2. ParticleFilterSMCEngine (Órgão 51):
   - Observações quadráticas ambíguas y_t ~ x_t^2 (próximas a 4.0) geram densidade posterior
     bimodal preservada em torno de +2.0 e -2.0 (`multimodal_detected == True`), com reamostragem
     sistemática adaptativa disparada por queda de N_eff (`resample_count >= 1`).
3. MultiAgentMMapSTLCoordinator (Órgão 52):
   - Enxame saudável sobre 3 anéis `mmap` SPSC com zero perda CRC32 certifica robustez STL > 0;
   - Injeção adversarial de violação STL em um worker detecta exatamente o worker infrator;
   - Teste cross-process real via `subprocess` escrevendo em canal `mmap` compartilhado no Windows
     e auditado pelo consumidor externo com CRC32 + STL.
4. Delegação Nativa Fast-Path em `HamiltonianSymplecticIntegrator.simulate(include_euler_baseline=False)`
   para o kernel Rust LTO C-ABI (`aether_cortex_vsa.dll`).
"""
import os
import subprocess
import sys
import tempfile
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
from aethermind_cognitive_substrate.physical_bridge.shared_memory_mmap_ipc import SharedMemoryMMapSPSCBridge


def main() -> int:
    print("=" * 80)
    print("[CICLO 18 — 52 ÓRGÃOS] SMC PARTICLE FILTER (51) + MULTI-AGENT MMAP/STL (52)")
    print("=" * 80)

    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY", f"Status inesperado: {health}"
    assert health["organs_active_count"] >= 52, f"Esperado 52 órgãos, veio {health['organs_active_count']}"
    assert health["smc_particle_filter_active"] is True
    assert health["multi_agent_mmap_stl_coordinator_active"] is True
    print(f"[PASS] Córtex {health['version']} pronto com {health['organs_active_count']} órgãos.")

    # 1. ParticleFilterSMCEngine: posterior bimodal ±2.0
    smc_res = cortex.execute_cognitive_mission(
        "smc_particle_track",
        {"observations": [4.0, 4.08, 3.92, 4.02, 3.96, 4.05, 3.99, 4.01]},
    )["result"]
    assert smc_res["status"] == "SMC_PARTICLE_FILTER_COMPLETED"
    assert smc_res["resample_count"] >= 1, f"Reamostragem sistemática não disparada: {smc_res}"
    assert smc_res["multimodal_detected"] is True, f"Bimodalidade esperada não detectada: {smc_res}"
    modes = smc_res["final_dominant_modes_dim0"]
    has_pos_mode = any(1.3 <= m["center"] <= 2.7 for m in modes)
    has_neg_mode = any(-2.7 <= m["center"] <= -1.3 for m in modes)
    assert has_pos_mode and has_neg_mode, f"Modos bimodais esperados próximos de ±2.0 não encontrados: {modes}"
    print(f"[PASS] Órgão 51 (SMC Bimodal): resamples={smc_res['resample_count']} | modos={modes} | {smc_res['elapsed_ms']} ms")

    # 2. MultiAgentMMapSTLCoordinator: enxame saudável + violação adversarial
    swarm_ok = cortex.execute_cognitive_mission("multi_agent_mmap_stl", {})["result"]
    assert swarm_ok["status"] == "SWARM_MMAP_STL_CERTIFIED", swarm_ok
    assert swarm_ok["crc_zero_loss"] is True
    assert swarm_ok["total_frames_popped_crc_ok"] == swarm_ok["total_frames_pushed"] == 18
    assert swarm_ok["all_agents_satisfied"] is True
    assert swarm_ok["global_overall_stl_robustness"] >= 0.0
    print(
        f"[PASS] Órgão 52 (Enxame OK): {swarm_ok['total_frames_popped_crc_ok']}/18 frames CRC OK | "
        f"STL rho={swarm_ok['global_overall_stl_robustness']} | {swarm_ok['elapsed_ms']} ms"
    )

    swarm_bad = cortex.execute_cognitive_mission(
        "multi_agent_mmap_stl",
        {
            "worker_traces": {
                "worker_ok": [[0.45], [0.55], [0.60], [0.48]],
                "worker_rogue": [[0.45], [0.98], [0.97], [0.99]],  # viola safety_ceiling 0.95
            }
        },
    )["result"]
    assert swarm_bad["status"] == "SWARM_STL_VIOLATION_DETECTED", swarm_bad
    assert "worker_rogue" in swarm_bad["violating_agents"]
    assert swarm_bad["global_overall_stl_robustness"] < 0.0
    print(f"[PASS] Órgão 52 (Detecção Adversarial): infrator={swarm_bad['violating_agents']} | rho={swarm_bad['global_overall_stl_robustness']}")

    # 3. Cross-Process Real OS IPC (`subprocess` produtor -> `drain_external_channels` STL)
    tmp_dir = tempfile.mkdtemp(prefix="aethermind_ipc_subproc_")
    backing_path = os.path.join(tmp_dir, "worker_ext.mmap")
    bridge_owner = SharedMemoryMMapSPSCBridge(capacity_slots=64, backing_path=backing_path, create=True)
    try:
        prod_code = (
            "import sys; sys.path.insert(0, r'" + root_dir + "'); "
            "from aethermind_cognitive_substrate.physical_bridge.shared_memory_mmap_ipc import SharedMemoryMMapSPSCBridge; "
            "b = SharedMemoryMMapSPSCBridge(capacity_slots=64, backing_path=r'" + backing_path + "', create=False); "
            "[b.push_frame([v]) for v in [0.40, 0.83, 0.70, 0.58, 0.42]]; "
            "b.close(unlink=False)"
        )
        proc = subprocess.run([sys.executable, "-c", prod_code], capture_output=True, text=True, check=True)
        assert proc.returncode == 0
        ext_report = cortex.multi_agent_mmap_stl.drain_external_channels({"external_worker": backing_path})
        assert ext_report["status"] == "EXTERNAL_SWARM_CERTIFIED", ext_report
        assert ext_report["total_frames_popped_crc_ok"] == 5
        print(f"[PASS] Cross-Process OS mmap+STL: {ext_report['total_frames_popped_crc_ok']} frames CRC32+STL certificados entre processos!")
    finally:
        bridge_owner.close(unlink=True)
        try:
            os.rmdir(tmp_dir)
        except OSError:
            pass

    # 4. Fast-path Nativo Rust no Órgão 47 (HamiltonianSymplecticIntegrator sem baseline Euler)
    fast_symp = cortex.hamiltonian_symplectic.simulate(
        q0=[1.0, 0.25], p0=[0.0, 0.85], dt=0.05, steps=5000, order=4,
        prefer_native=True, include_euler_baseline=False
    )
    assert fast_symp["energy_conservation_verified"] is True
    assert fast_symp["max_absolute_energy_drift"] < 1e-5
    assert "Rust" in fast_symp.get("backend", ""), fast_symp
    print(f"[PASS] Fast-Path Simplético Nativo ({fast_symp['backend']}): 5000 passos em {fast_symp['elapsed_ms']} ms | |dH|={fast_symp['max_absolute_energy_drift']}")

    print("=" * 80)
    print("SUCESSO ABSOLUTO: TODOS OS 52 ÓRGÃOS E INVARIANTES DO CICLO 18 VERIFICADOS!")
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
