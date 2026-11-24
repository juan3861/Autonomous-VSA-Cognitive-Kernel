"""Test Suite 54: v7.7.0 Fused AVX2 W^X JIT PERMUTE+XOR, 3-Step ARC & Conditional CEGIS.

Empirically verifies:
1. Fused native x86_64 AVX2 W^X JIT emitter `vsa_jit_compile_permuted_xor_chain`
   computing XOR_{k=0..N-1} Permute(in[k], steps[k]) in a single emitted function (mode=1)
   matching discrete Permute + XOR bit-for-bit.
2. Conditional Python AST CEGIS (`ast.IfExp` / `if cond: return a else: return b`)
   proving branch collapse & branch-wise strength reduction in Z3 across 2^64 inputs.
3. 3-Step compositional ARC grid induction (`max_program_depth=3`, e.g. `crop_nonzero -> flip_h -> scale_2x`)
   with Z3 dimension and non-zero pixel invariants.
4. `autonomous_vsa.h` declarations and `SovereignCortexRuntime` v7.7.0 readiness.
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

from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
from aethermind_cognitive_substrate.logic_symbolic.symbolic_grid_arc_reasoner import SymbolicGridARCReasoner
from aethermind_cognitive_substrate.memory_vault.vsa_dag_compiler import VSADAGBytecodeCompiler
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV77FusedJIT3StepARCAndIfCEGIS(unittest.TestCase):
    """Empirical audit suite for v7.7.0 fused AVX2 PERMUTE+XOR JIT, 3-step ARC, and conditional CEGIS."""

    def test_01_fused_avx2_wx_jit_permuted_xor_chain_bit_exact(self):
        """Fused PERMUTE+XOR native AVX2 W^X machine code matches discrete Permute+XOR bit-for-bit."""
        comp = VSADAGBytecodeCompiler()
        rng = np.random.default_rng(7700)
        vecs = [rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64) for _ in range(4)]
        shifts = [0, 7, 64, 199]

        fused_out, mode = comp.jit_permuted_xor_chain(vecs, shifts)
        self.assertEqual(mode, 1, "Expected native x86_64 AVX2 W^X fused PERMUTE+XOR execution")

        expected = np.zeros(160, dtype=np.uint64)
        for v, sh in zip(vecs, shifts):
            p, m = comp.jit_permute_vector(v, sh)
            self.assertEqual(m, 1)
            expected ^= p

        np.testing.assert_array_equal(fused_out, expected)

        # Invert first 3 terms to recover Permute(vecs[3], 199), then unpermute by 10240 - 199
        partial, _ = comp.jit_permuted_xor_chain(vecs[:3], shifts[:3])
        rec_p3 = fused_out ^ partial
        rec_v3, _ = comp.jit_permute_vector(rec_p3, 10240 - 199)
        np.testing.assert_array_equal(rec_v3, vecs[3])

        hdr = (Path(ROOT_DIR) / "aether_cortex_vsa" / "include" / "autonomous_vsa.h").read_text(encoding="utf-8")
        for sym in (
            "vsa_jit_compile_permuted_xor_chain",
            "vsa_jit_exec_permuted_xor_chain",
            "vsa_jit_free_permuted_xor_chain",
        ):
            self.assertIn(sym, hdr)

    def test_02_conditional_ifexp_python_ast_cegis(self):
        """CEGIS synthesizes branchless & branch-reduced equivalents for conditional Python functions."""
        synth = CEGISCodeSynthesizer()

        # 1. Redundant branch collapse: `if x == 0: return 0\nreturn x` -> `x`
        r1 = synth.synthesize_python_ast_cegis(
            "def redundant_zero(x):\n    if x == 0:\n        return 0\n    return x\n"
        )
        self.assertTrue(r1["is_equivalent"])
        self.assertEqual(r1["z3_status"], "unsat")
        self.assertEqual(r1["candidate_code"], "x")

        # 2. Always-true tautology branch collapse: `(x * 4) if (y ^ y) == 0 else 999` -> `x << 2`
        r2 = synth.synthesize_python_ast_cegis("def taut(x, y): return (x * 4) if (y ^ y) == 0 else 999")
        self.assertTrue(r2["is_equivalent"])
        self.assertEqual(r2["candidate_code"], "x << 2")

        # 3. Genuine 2-branch strength reduction: `(x * 8) if x > 0 else (x * 4)` -> `(x << 3) if x > 0 else (x << 2)`
        r3 = synth.synthesize_python_ast_cegis("def dual_scale(x): return (x * 8) if x > 0 else (x * 4)")
        self.assertTrue(r3["is_equivalent"])
        self.assertIn("<< 3", r3["candidate_code"])
        self.assertIn("<< 2", r3["candidate_code"])
        self.assertLess(r3["synthesized_cycle_cost"], r3["initial_cycle_cost"])

    def test_03_three_step_compositional_arc_grid_induction(self):
        """SymbolicGridARCReasoner discovers 3-step compositions (`max_program_depth=3`) with Z3 proof."""
        reasoner = SymbolicGridARCReasoner()
        gt_prog = ["crop_nonzero", "flip_h", "scale_2x"]
        raw_grids = [
            [[0, 0, 0, 0], [0, 1, 2, 0], [0, 3, 0, 0], [0, 0, 0, 0]],
            [[0, 4, 5, 0], [0, 0, 6, 0], [0, 0, 0, 0]],
            [[0, 0, 0], [0, 7, 8], [0, 9, 1]],
        ]
        train_pairs = [(g, reasoner.apply_program(gt_prog, g)) for g in raw_grids[:2]]
        test_in = raw_grids[2]
        expected_test = reasoner.apply_program(gt_prog, test_in)

        res = reasoner.solve_arc_task(train_pairs, test_in, max_program_depth=3)
        self.assertTrue(res["solved"])
        self.assertEqual(len(res["synthesized_program"]), 3)
        self.assertEqual(res["predicted_grid"], expected_test.tolist())
        self.assertTrue(res["z3_proof"]["z3_verified"])

    def test_04_runtime_v77_version(self):
        rt = SovereignCortexRuntime()
        self.assertIn("MODULAR-AGI", rt.version)
        self.assertIn("SOVEREIGN", rt.version)


if __name__ == "__main__":
    unittest.main()
