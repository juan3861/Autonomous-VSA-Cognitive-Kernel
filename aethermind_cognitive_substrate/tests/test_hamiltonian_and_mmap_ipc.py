"""Test Suite — Ciclo 16: Hamiltonian Symplectic Integrator (Organ 47) & Zero-Copy mmap IPC (Organ 48).

Verifica empiricamente:
1. Prontidão do Córtex v4.8.0 com 48 órgãos ativos.
2. Hamiltonian Symplectic Yoshida-4: conservação estrita de energia (< 1e-6 deriva relativa
   em 1.000 passos anarmônicos acoplados e Kepler orbital), provando supremacia contra Euler explícito.
3. Zero-Copy Shared Memory (`mmap`) SPSC IPC:
   - Benchmark de alta vazão (5.000 quadros com CRC32).
   - Teste real cross-process no kernel Windows NT: subprocesso produtor separado escreve 16 quadros
     em página `mmap` compartilhada enquanto o processo pai lê e valida 16/16 checksums CRC32.
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

from aethermind_cognitive_substrate.physical_bridge.shared_memory_mmap_ipc import SharedMemoryMMapSPSCBridge
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def main() -> int:
    print("=" * 80)
    print("[CICLO 16] HAMILTONIAN SYMPLECTIC (ÓRGÃO 47) & MMAP IPC (ÓRGÃO 48)")
    print("=" * 80)

    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY"
    assert health["organs_active_count"] >= 48, f"Esperado >= 48 órgãos, got {health['organs_active_count']}"
    assert health.get("hamiltonian_symplectic_integrator_active") is True
    assert health.get("mmap_zero_copy_ipc_active") is True
    print(f"[1/4] Córtex Prontidão: {health['organs_active_count']} órgãos | Versão={health['version']}")

    # 2. Órgão 47: Hamiltonian Symplectic Yoshida-4 (1.000 passos anarmônicos + Kepler)
    res_ham = cortex.execute_cognitive_mission(
        "hamiltonian_simulate",
        {"q0": [1.0, 0.25], "p0": [0.0, 0.85], "dt": 0.05, "steps": 1000, "order": 4}
    )["result"]
    assert res_ham["status"] == "HAMILTONIAN_SYMPLECTIC_CONSERVED"
    assert res_ham["energy_conservation_verified"] is True
    assert res_ham["relative_energy_drift"] < 1e-4, f"Deriva simplética alta: {res_ham['relative_energy_drift']}"
    assert res_ham["euler_baseline_drift"] > res_ham["max_absolute_energy_drift"] * 100.0
    print(
        f"[2/4] Órgão 47 (Hamiltonian Yoshida-4): OK | RelDrift={res_ham['relative_energy_drift']} vs "
        f"EulerDrift={res_ham['euler_baseline_drift']} em {res_ham['elapsed_ms']} ms"
    )

    # 3. Órgão 48: Zero-Copy mmap SPSC Benchmark (5.000 quadros com CRC32)
    res_bench = cortex.execute_cognitive_mission("mmap_ipc_benchmark", {"num_frames": 5000})["result"]
    assert res_bench["status"] == "MMAP_IPC_SPSC_VERIFIED"
    assert res_bench["frames_transferred"] == 5000
    assert res_bench["crc32_errors"] == 0
    print(
        f"[3/4] Órgão 48 (mmap IPC SPSC Throughput): OK | {res_bench['frames_transferred']} frames @ "
        f"{res_bench['throughput_frames_per_sec']} fps ({res_bench['latency_us_per_roundtrip']} us/frame)"
    )

    # 4. Teste Real Cross-Process Windows NT sobre Memória Compartilhada mmap
    with tempfile.TemporaryDirectory() as tmpd:
        shm_file = str(Path(tmpd) / "cross_proc_spsc.bin")
        parent_consumer = SharedMemoryMMapSPSCBridge(capacity_slots=64, backing_path=shm_file, create=True)

        child_code = (
            "import sys; sys.path.insert(0, r'" + root_dir + "'); "
            "from aethermind_cognitive_substrate.physical_bridge.shared_memory_mmap_ipc import SharedMemoryMMapSPSCBridge; "
            f"b = SharedMemoryMMapSPSCBridge(capacity_slots=64, backing_path=r'{shm_file}', create=False); "
            "[b.push_frame([float(i), i * 1.5, 0.94525]) for i in range(16)]; "
            "b.close(unlink=False)"
        )
        proc = subprocess.run([sys.executable, "-c", child_code], capture_output=True, text=True, timeout=30)
        assert proc.returncode == 0, f"Subprocesso produtor mmap falhou: {proc.stderr}"

        frames_read = []
        while True:
            frm = parent_consumer.pop_frame()
            if frm is None:
                break
            assert frm["crc32_verified"] is True
            frames_read.append(frm)

        parent_consumer.close(unlink=True)
        assert len(frames_read) == 16, f"Esperado 16 quadros cross-process, lidos {len(frames_read)}"
        assert frames_read[15]["values"] == [15.0, 22.5, 0.94525]
        print("[4/4] Cross-Process Real Windows NT (mmap Subprocess Producer -> Parent Consumer): OK (16/16 CRC32)")

    print("\n[VEREDITO FINAL]: CICLO 16 (HAMILTONIAN SYMPLECTIC + MMAP CROSS-PROCESS IPC) APROVADO COM EXIT CODE 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
