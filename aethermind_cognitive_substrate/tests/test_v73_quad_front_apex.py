"""Test Suite 50: v7.3.0 Quad-Front Ceiling Verification.

Empirically verifies all 4 parallel engineering fronts:
1. Front 1: Zero-copy Cython+Rust Lyapunov fast-path beating SciPy (`< 1e-10` parity).
2. Front 2: Compiled Vulkan 1.3 SPIR-V Wave64 batch Hamming/cosine shaders & RX 580/fallback engine.
3. Front 3: Portable WebAssembly (`wasm32-unknown-unknown`) kernel inside Wasmtime sandbox.
4. Front 4: Zero-dep x86_64 AVX2 W^X JIT machine-code emitter + Z3 edge numeric range proofs.
"""
from __future__ import annotations

import ctypes
import os
import struct
import sys
import time
import unittest
from pathlib import Path
import numpy as np
import scipy.linalg

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aethermind_cognitive_substrate.logic_symbolic.lyapunov_sdp_stability_certifier import LyapunovSDPStabilityCertifier
from aethermind_cognitive_substrate.memory_vault.native_vsa_ffi import NativeVSAFFI
from aethermind_cognitive_substrate.physical_bridge.native_cortex_dll_singleton import get_native_cortex_dll
from aethermind_cognitive_substrate.physical_bridge.vulkan_batch_vsa_engine import VulkanBatchVSAEngine
from aethermind_cognitive_substrate.physical_bridge.wasm_sandbox_bridge import WasmSandboxBridge
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import AutonomousCognitiveComposer


class TestV73QuadFrontApex(unittest.TestCase):
    """Empirical test suite covering all 4 v7.3.0 ceiling fronts."""

    def test_01_lyapunov_fast_path_beats_scipy(self):
        """Front 1: Cython+Rust Lyapunov fast-path matches SciPy (< 1e-10) and runs faster."""
        rng = np.random.default_rng(77)
        M = rng.normal(0.0, 0.1, size=(16, 16))
        A = np.ascontiguousarray(M / (np.max(np.abs(np.linalg.eigvals(M))) + 0.35), dtype=np.float64)
        Q = np.eye(16, dtype=np.float64)

        cert = LyapunovSDPStabilityCertifier()
        # Warm-up
        P_fast, res_fast, iters = cert.solve_discrete_lyapunov_fast(A, Q)
        P_sp = scipy.linalg.solve_discrete_lyapunov(A.T, Q)

        self.assertLess(res_fast, 1e-10)
        self.assertLess(float(np.max(np.abs(P_fast - P_sp))), 1e-9)
        self.assertGreaterEqual(iters, 1)

        t0 = time.perf_counter()
        for _ in range(100):
            scipy.linalg.solve_discrete_lyapunov(A.T, Q)
        scipy_ms = (time.perf_counter() - t0) * 1000.0

        t0 = time.perf_counter()
        for _ in range(100):
            cert.solve_discrete_lyapunov_fast(A, Q)
        fast_ms = (time.perf_counter() - t0) * 1000.0

        self.assertLess(fast_ms, scipy_ms, f"Expected fast-path ({fast_ms:.2f}ms) < SciPy ({scipy_ms:.2f}ms)")

        raw_res = cert.certify_discrete_lyapunov(A, Q, raw_matrix=True)
        self.assertIsInstance(raw_res["lyapunov_matrix_P"], np.ndarray)

    def test_02_vulkan_spirv_shaders_and_batch_engine(self):
        """Front 2: Valid SPIR-V shaders exist and VulkanBatchVSAEngine computes exact batch distances."""
        eng = VulkanBatchVSAEngine()
        for spv in (eng.vsa_spv_path, eng.cosine_spv_path):
            self.assertTrue(spv.exists(), f"Compiled SPIR-V missing: {spv}")
            data = spv.read_bytes()
            magic = struct.unpack("<I", data[:4])[0]
            self.assertEqual(magic, 0x07230203, f"Invalid SPIR-V magic in {spv.name}: {hex(magic)}")

        rng = np.random.default_rng(123)
        q_u64 = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)
        cands_u64 = rng.integers(0, np.iinfo(np.uint64).max, size=(128, 160), dtype=np.uint64)
        cands_u64[37] = q_u64.copy()

        res_h = eng.batch_hamming_distances(q_u64, cands_u64, prefer_gpu=True)
        self.assertEqual(int(res_h["distances"][37]), 0)
        self.assertTrue(4500 <= int(res_h["distances"][0]) <= 5700)

        q_f32 = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)
        cands_f32 = np.array([[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0]], dtype=np.float32)
        res_c = eng.batch_cosine_distances(q_f32, cands_f32, prefer_gpu=True)
        self.assertAlmostEqual(float(res_c["distances"][0]), 0.0, places=5)
        self.assertAlmostEqual(float(res_c["distances"][1]), 1.0, places=5)

    def test_03_wasm32_sandbox_parity(self):
        """Front 3: Portable wasm32 Rust kernel inside Wasmtime matches native C-ABI bit-for-bit."""
        wb = WasmSandboxBridge()
        self.assertTrue(wb.is_available, "aether_cortex_vsa.wasm must load via wasmtime.")
        try:
            ffi = NativeVSAFFI()
            w1 = wb.create_from_seed(1111)
            w2 = wb.create_from_seed(2222)
            n1 = ffi.create_from_seed(1111)
            n2 = ffi.create_from_seed(2222)

            np.testing.assert_array_equal(w1, n1)
            np.testing.assert_array_equal(w2, n2)

            wbnd = wb.bind(w1, w2)
            nbnd = ffi.bind(n1, n2)
            np.testing.assert_array_equal(wbnd, nbnd)
            self.assertEqual(wb.hamming_distance(w1, wb.bind(wbnd, w2)), 0)
        finally:
            wb.close()

    def test_04_native_x64_avx2_wx_jit_xor_chain(self):
        """Front 4a: Native x86_64 AVX2 W^X JIT machine code executes 5-way XOR chain bit-exactly."""
        lib = get_native_cortex_dll()
        self.assertIsNotNone(lib)
        self.assertTrue(hasattr(lib, "vsa_jit_compile_xor_chain"))

        rng = np.random.default_rng(909)
        vecs = [rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64) for _ in range(5)]
        expected = np.bitwise_xor.reduce(vecs)

        handle = lib.vsa_jit_compile_xor_chain(5)
        self.assertTrue(handle)
        try:
            ptrs = (ctypes.POINTER(ctypes.c_uint64) * 5)(
                *[v.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)) for v in vecs]
            )
            out = np.zeros(160, dtype=np.uint64)
            exec_mode = int(
                lib.vsa_jit_exec_xor_chain(handle, ptrs, out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)))
            )
            self.assertEqual(exec_mode, 1, "Expected native emitted x86_64 AVX2 W^X machine code execution")
            np.testing.assert_array_equal(out, expected)
        finally:
            lib.vsa_jit_free_xor_chain(handle)

    def test_05_z3_edge_numeric_range_contracts(self):
        """Front 4b: Z3 SMT proves edge numeric domain propagation and blocks out-of-range inputs."""
        comp = AutonomousCognitiveComposer()

        ok = comp.verify_dag_contracts(
            ["ukf_state_estimator", "ilqr_trajectory_optimizer", "cbf_control_barrier_shield", "stl_temporal_logic_monitor"],
            {"observations": [0.4, -0.2, 0.1, 0.0], "lyapunov_rho": 0.85},
        )
        self.assertTrue(ok["verified"])
        self.assertEqual(ok["edge_numeric_invariants_proven"], 4)

        # Out-of-range observation (500.0 > CBF in_max 10.0) must be blocked by Z3 BEFORE stage execution
        bad_receipt = comp.execute_pipeline(
            "safe_stabilization",
            {"observations": [500.0, 0.0], "lyapunov_rho": 0.85},
        )
        self.assertFalse(bad_receipt.overall_success)
        self.assertFalse(bad_receipt.certified_safe)
        self.assertEqual(bad_receipt.formal_certificate["z3_preflight_proof"]["sat_status"], "unsat")
        self.assertEqual(len(bad_receipt.stages), 0)


if __name__ == "__main__":
    unittest.main()
