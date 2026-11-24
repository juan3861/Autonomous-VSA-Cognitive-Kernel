"""Test Suite 55: v7.8.0 Cython Zero-Copy Fused AVX2 JIT & Z3 Mathematical Induction Loop CEGIS.

Empirically verifies:
1. Cython zero-copy C-extension symbols `cy_jit_compile_permute`, `cy_jit_exec_permute`,
   `cy_jit_compile_permuted_xor_chain`, `cy_jit_exec_permuted_xor_chain` with `nogil`.
2. Z3 Mathematical Induction (`Base Case n=0` + `Inductive Step k -> k+1`) proving O(n) -> O(1)
   closed-form synthesis for `for` and `while` accumulator loops (`sum_odds`, `loop_scale`, `xor_loop`).
3. Track I integration in AGI-Modular Arena and `SovereignCortexRuntime` v7.8.0 readiness.
"""
from __future__ import annotations

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

from aethermind_cognitive_substrate.benchmarks.agi_modular_arena import bench_track_i_cython_jit_and_loop_induction
from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
from aethermind_cognitive_substrate.memory_vault.vsa_dag_compiler import VSADAGBytecodeCompiler
from aethermind_cognitive_substrate.physical_bridge.fast_vsa_bridge import _load_cython_ext
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV78CythonJITAndLoopCEGIS(unittest.TestCase):
    """Empirical audit suite for v7.8.0 Cython zero-copy JIT & Z3 loop induction CEGIS."""

    def test_01_cython_zero_copy_jit_permute_and_permuted_xor(self):
        """Cython zero-copy extension exposes and executes native AVX2 W^X JIT handles."""
        cy = _load_cython_ext()
        self.assertIsNotNone(cy, "Compiled fast_vsa_ext.pyd must be present.")
        for fn in (
            "cy_jit_compile_permute",
            "cy_jit_exec_permute",
            "cy_jit_free_permute",
            "cy_jit_compile_permuted_xor_chain",
            "cy_jit_exec_permuted_xor_chain",
            "cy_jit_free_permuted_xor_chain",
        ):
            self.assertTrue(hasattr(cy, fn), f"Missing Cython symbol {fn}")

        rng = np.random.default_rng(7801)
        mat = rng.integers(0, np.iinfo(np.uint64).max, size=(4, 160), dtype=np.uint64)
        shifts = np.array([0, 7, 64, 199], dtype=np.uint64)
        out_cy = np.zeros(160, dtype=np.uint64)

        h = int(cy.cy_jit_compile_permuted_xor_chain(shifts))
        self.assertGreater(h, 0)
        try:
            mode = int(cy.cy_jit_exec_permuted_xor_chain(h, mat, out_cy))
            self.assertEqual(mode, 1)
        finally:
            cy.cy_jit_free_permuted_xor_chain(h)

        # Verify parity against discrete Cython permutes + XOR
        expected = np.zeros(160, dtype=np.uint64)
        tmp = np.zeros(160, dtype=np.uint64)
        for idx, sh in enumerate(shifts):
            ph = int(cy.cy_jit_compile_permute(int(sh)))
            try:
                m = int(cy.cy_jit_exec_permute(ph, mat[idx], tmp))
                self.assertEqual(m, 1)
                expected ^= tmp
            finally:
                cy.cy_jit_free_permute(ph)

        np.testing.assert_array_equal(out_cy, expected)

    def test_02_z3_mathematical_induction_loop_closed_form_cegis(self):
        """Proves O(n) -> O(1) closed forms for for/while loops via Z3 Base Case + Inductive Step."""
        synth = CEGISCodeSynthesizer()

        # 1. Arithmetic progression: sum_{i=0..n-1} (2*i + 1) == n * n
        r1 = synth.synthesize_loop_closed_form_cegis(
            "def sum_odds(n):\n    acc = 0\n    for i in range(n):\n        acc = acc + (2 * i + 1)\n    return acc\n"
        )
        self.assertTrue(r1["is_equivalent"])
        self.assertEqual(r1["z3_base_case"], "unsat")
        self.assertEqual(r1["z3_inductive_step"], "unsat")
        self.assertEqual(r1["candidate_code"], "n * n")

        # 2. Scaled accumulation: sum_{i=0..n-1} (x * 4) == (x << 2) * n
        r2 = synth.synthesize_loop_closed_form_cegis(
            "def loop_scale(x, n):\n    acc = 0\n    for i in range(n):\n        acc += x * 4\n    return acc\n"
        )
        self.assertTrue(r2["is_equivalent"])
        self.assertEqual(r2["candidate_code"], "(x << 2) * n")

        # 3. Alternating while-loop XOR: xor_{i=0..n-1} x == x if n & 1 != 0 else 0
        r3 = synth.synthesize_loop_closed_form_cegis(
            "def xor_loop(x, n):\n    acc = 0\n    i = 0\n    while i < n:\n        acc = acc ^ x\n        i = i + 1\n    return acc\n"
        )
        self.assertTrue(r3["is_equivalent"])
        self.assertEqual(r3["candidate_code"], "x if n & 1 != 0 else 0")

    def test_03_arena_track_i_and_runtime_v78(self):
        ti = bench_track_i_cython_jit_and_loop_induction()
        self.assertTrue(ti["cython_zero_copy_jit_executed"])
        self.assertTrue(ti["odds_proven"] and ti["scale_proven"] and ti["xor_proven"])

        rt = SovereignCortexRuntime()
        self.assertIn("7.8.0", rt.version)
        self.assertIn("INDUCTIVE", rt.version)


if __name__ == "__main__":
    unittest.main()
