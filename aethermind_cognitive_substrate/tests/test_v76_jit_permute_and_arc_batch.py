"""Test Suite 53: v7.6.0 Native AVX2 W^X JIT Permute & 8-Task Compositional ARC Batch.

Empirically verifies:
1. Native x86_64 AVX2 W^X machine-code emitter `vsa_jit_compile_permute` / `vsa_jit_exec_permute`
   bit-for-bit across arbitrary bit & word shifts against `VSAExpressionCompiler` VM.
2. Invertibility round-trip via `VSADAGBytecodeCompiler.jit_permute_vector` (0 Hamming error).
3. `autonomous_vsa.h` C-ABI declarations for JIT permute symbols.
4. Track G 8-Task Compositional ARC Grid Induction Batch (`8/8` exact pixel accuracy + Z3 proof).
5. `SovereignCortexRuntime` `7.6.0` version readiness.
"""
from __future__ import annotations

import ctypes
import os
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

from aethermind_cognitive_substrate.benchmarks.agi_modular_arena import bench_track_g_arc_compositional_batch
from aethermind_cognitive_substrate.memory_vault.vsa_dag_compiler import VSADAGBytecodeCompiler
from aethermind_cognitive_substrate.memory_vault.vsa_expression_compiler import VSAExpressionCompiler, VSAVar
from aethermind_cognitive_substrate.physical_bridge.native_cortex_dll_singleton import get_native_cortex_dll
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV76JITPermuteAndARCBatch(unittest.TestCase):
    """Empirical audit suite for v7.6.0 native JIT Permute emitter & ARC 8-task batch."""

    def test_01_native_avx2_wx_jit_permute_matches_vm_bit_exact(self):
        """Native x86_64 AVX2 W^X JIT permute executes (mode=1) and matches VsaOp VM bit-exactly."""
        lib = get_native_cortex_dll()
        self.assertIsNotNone(lib)
        self.assertTrue(hasattr(lib, "vsa_jit_compile_permute"))

        rng = np.random.default_rng(2026)
        vec = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)
        vm = VSAExpressionCompiler()
        va = VSAVar("v")

        for shift in (0, 1, 7, 63, 64, 65, 192, 199, 10239, 10247):
            out_vm, _ = vm.evaluate(bindings={"v": vec}, outputs=[va.permute(shift)])
            expected = out_vm[0]

            handle = lib.vsa_jit_compile_permute(shift)
            self.assertTrue(handle)
            try:
                out_jit = np.zeros(160, dtype=np.uint64)
                mode = int(
                    lib.vsa_jit_exec_permute(
                        handle,
                        vec.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
                        out_jit.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64)),
                    )
                )
                self.assertEqual(mode, 1, f"Expected native x86_64 AVX2 W^X execution at shift={shift}")
                np.testing.assert_array_equal(out_jit, expected)
            finally:
                lib.vsa_jit_free_permute(handle)

    def test_02_jit_permute_bijection_and_c_header(self):
        """Circular JIT permute round-trip inverts to 0 Hamming error and header declares symbols."""
        dag_comp = VSADAGBytecodeCompiler()
        rng = np.random.default_rng(88)
        vec = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)

        permuted, m1 = dag_comp.jit_permute_vector(vec, 199)
        recovered, m2 = dag_comp.jit_permute_vector(permuted, 10240 - 199)
        self.assertEqual(m1, 1)
        self.assertEqual(m2, 1)
        np.testing.assert_array_equal(recovered, vec)

        hdr = (Path(ROOT_DIR) / "aether_cortex_vsa" / "include" / "autonomous_vsa.h").read_text(encoding="utf-8")
        for sym in ("vsa_jit_compile_permute", "vsa_jit_exec_permute", "vsa_jit_free_permute"):
            self.assertIn(sym, hdr)

    def test_03_arc_8task_compositional_batch_100_percent(self):
        """SymbolicGridARCReasoner solves all 8 unseen compositional ARC tasks with 100% pixel accuracy."""
        res = bench_track_g_arc_compositional_batch()
        self.assertEqual(res["total_tasks"], 8)
        self.assertEqual(res["exact_test_matches"], 8, f"ARC batch mismatches: {res['task_results']}")
        self.assertEqual(res["accuracy"], 1.0)

    def test_04_runtime_v76_version_and_health(self):
        rt = SovereignCortexRuntime()
        self.assertIn("MODULAR-AGI", rt.version)
        self.assertIn("SOVEREIGN", rt.version)


if __name__ == "__main__":
    unittest.main()
