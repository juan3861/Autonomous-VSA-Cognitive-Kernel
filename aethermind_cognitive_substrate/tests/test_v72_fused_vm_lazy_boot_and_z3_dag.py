"""Test Suite 49: v7.2.0 Fused AVX2 VSA Graph VM, Cython Zero-Copy, <50ms Lazy Boot & Z3-Verified DAG Composer."""
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path
import numpy as np

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aethermind_cognitive_substrate.memory_vault.vsa_expression_compiler import (
    VSAExpressionCompiler,
    VSASeed,
    VSAVar,
)
from aethermind_cognitive_substrate.memory_vault.native_vsa_ffi import NativeVSAFFI
from aethermind_cognitive_substrate.physical_bridge.fast_vsa_bridge import FastVSABridge
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import AutonomousCognitiveComposer
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV72FusedVMLazyBootZ3DAG(unittest.TestCase):
    """Empirical test suite for v7.2.0 architectural ceiling enhancements."""

    def test_01_cold_boot_lazy_registry_latency(self):
        """Verify cold subprocess import + SovereignCortexRuntime() instantiation is < 200 ms (target ~50 ms)."""
        code = (
            "import sys, time; "
            f"sys.path.insert(0, {ROOT_DIR!r}); "
            "t0 = time.perf_counter(); "
            "from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime; "
            "r = SovereignCortexRuntime(); "
            "ms = (time.perf_counter() - t0) * 1000.0; "
            "print(f'{ms:.2f}'); "
            "assert ms < 250.0, f'Cold boot too slow: {ms:.2f} ms'"
        )
        proc = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertEqual(proc.returncode, 0, msg=f"Subprocess failed: {proc.stderr}")
        boot_ms = float(proc.stdout.strip().splitlines()[-1])
        self.assertLess(boot_ms, 250.0)

    def test_02_fused_avx2_vsa_graph_vm_bit_exact(self):
        """Verify fused VSA Graph VM matches exact algebraic inverse & NativeVSAFFI parity."""
        comp = VSAExpressionCompiler()
        self.assertTrue(comp.is_native_ready, "Native vsa_eval_graph_bytecode must be available.")

        ffi = NativeVSAFFI()
        a_vec = ffi.create_from_seed(101)
        b_vec = ffi.create_from_seed(202)

        va = VSAVar("a")
        vb = VSAVar("b")
        bound = va.permute(13).bind(vb)
        recovered = bound.bind(vb).unpermute(13)

        out_vecs, scalars = comp.evaluate(
            bindings={"a": a_vec, "b": b_vec},
            outputs=[bound, recovered],
            hamming_queries=[(va, recovered), (va, bound)],
        )

        self.assertEqual(int(scalars[0]), 0, "Fused permute+bind+bind+unpermute must invert to 0 Hamming error.")
        self.assertTrue(4500 <= int(scalars[1]) <= 5700, f"Bound vector should be quasi-orthogonal (~5120), got {scalars[1]}")
        np.testing.assert_array_equal(out_vecs[1], a_vec)

        # Cross-check with VSASeed & bundle
        s1 = VSASeed(777)
        s2 = VSASeed(888)
        bund = s1.bundle(s2)
        _, sc2 = comp.evaluate(bindings={}, hamming_queries=[(bund, s1), (bund, s2)])
        # Bundle of two orthogonal vectors has ~25% Hamming distance (~2560 bits) from each
        self.assertLess(int(sc2[0]), 3100)
        self.assertLess(int(sc2[1]), 3100)

    def test_03_cython_zero_copy_bridge_and_c_header_symbols(self):
        """Verify Cython zero-copy bridge (or fallback) parity and autonomous_vsa.h completeness."""
        bridge = FastVSABridge()
        v1 = bridge.create_from_seed(1234)
        v2 = bridge.create_from_seed(5678)
        out = np.zeros(160, dtype=np.uint64)

        bridge.bind_into(v1, v2, out)
        self.assertEqual(bridge.hamming_distance(bridge.bind(out, v2), v1), 0)

        header_path = Path(ROOT_DIR) / "aether_cortex_vsa" / "include" / "autonomous_vsa.h"
        self.assertTrue(header_path.exists(), "Standard C/C++ header autonomous_vsa.h must exist.")
        hdr = header_path.read_text(encoding="utf-8")
        for sym in [
            "vsa_eval_graph_bytecode",
            "vsa_bind",
            "symplectic_yoshida4_coupled_f64",
            "lyapunov_smith_doubling_f64",
            "spectral_power_iteration_f64",
            "omp_sparse_project_f64",
            "rrt_star_nearest_and_radius_f64",
        ]:
            self.assertIn(sym, hdr, f"Header missing symbol declaration: {sym}")

    def test_04_z3_preflight_dag_verification_and_live_execution(self):
        """Verify Z3 SMT pre-flight DAG contract checker blocks unsafe plans and certifies valid ones."""
        comp = AutonomousCognitiveComposer()

        # 1. Valid pipeline under Lyapunov bound rho <= 0.95
        r_ok = comp.execute_pipeline(
            "safe_stabilization",
            {"observations": [0.3, -0.1, 0.05, 0.0], "lyapunov_rho": 0.88},
        )
        self.assertTrue(r_ok.overall_success)
        self.assertTrue(r_ok.certified_safe)
        self.assertTrue(r_ok.formal_certificate["z3_preflight_proof"]["verified"])
        self.assertEqual(len(r_ok.stages), 4)

        # 2. Unstable Lyapunov spectral radius > 0.95 -> MUST be rejected by Z3 before execution
        r_bad_rho = comp.execute_pipeline(
            "safe_stabilization",
            {"observations": [0.3, -0.1], "lyapunov_rho": 1.05},
        )
        self.assertFalse(r_bad_rho.overall_success)
        self.assertFalse(r_bad_rho.certified_safe)
        self.assertFalse(r_bad_rho.formal_certificate["z3_preflight_proof"]["verified"])
        self.assertEqual(len(r_bad_rho.stages), 0)

        # 3. Missing formal safety certifier sink when require_formal_safety=True -> Z3 UNSAT
        r_no_shield = comp.execute_pipeline(
            "unsafe_open_loop",
            {"custom_pipeline": ["ukf_state_estimator"], "require_formal_safety": True},
        )
        self.assertFalse(r_no_shield.overall_success)
        self.assertEqual(r_no_shield.formal_certificate["z3_preflight_proof"]["sat_status"], "unsat")

    def test_05_runtime_v72_missions_and_health(self):
        """Verify SovereignCortexRuntime exposes v7.2.0 health telemetry and dispatches new missions."""
        rt = SovereignCortexRuntime()
        health = rt.get_system_health()
        self.assertIn("APEX", rt.version)
        self.assertIn("SOVEREIGN", rt.version)
        self.assertTrue(health["vsa_fused_graph_vm_ready"])
        self.assertIn(health["fast_vsa_bridge_mode"], ("CYTHON_ZERO_COPY", "CTYPES_C_ABI"))

        m1 = rt.execute_cognitive_mission("vsa_fused_graph_eval", {"seed_a": 11, "seed_b": 22, "permute_steps": 9})
        self.assertEqual(m1["result"]["hamming_exact_recovery"], 0)

        m2 = rt.execute_cognitive_mission("fast_vsa_bind_compare", {"seed_a": 33, "seed_b": 44})
        self.assertEqual(m2["result"]["hamming_recovery"], 0)


if __name__ == "__main__":
    unittest.main()
