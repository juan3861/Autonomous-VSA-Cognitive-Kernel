"""Test Suite 56: v7.9.0 RX 580 Wave64 Fused PERMUTE+XOR GPU Shader & Nested-Loop Z3 Induction CEGIS.

Empirically verifies:
1. Compiled SPIR-V Wave64 compute shader `vsa_batch_permuted_xor.spv` executing on Radeon RX 580
   (`gpu_executed=True` when Vulkan hardware present) and matching CPU bitwise parity bit-for-bit
   across multiple rotation shifts (`0, 64, 199`).
2. Nested-loop Z3 Double Mathematical Induction (`synthesize_nested_loop_closed_form_cegis`)
   reducing O(n*m) rectangular & O(n^2) triangular nested loops to formally proven O(1) closed forms.
3. Track J Arena integration & `SovereignCortexRuntime` v7.9.0 readiness.
"""
from __future__ import annotations

import os
import struct
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

from aethermind_cognitive_substrate.benchmarks.agi_modular_arena import bench_track_j_vulkan_fused_vsa_and_nested_cegis
from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
from aethermind_cognitive_substrate.physical_bridge.vulkan_batch_vsa_engine import VulkanBatchVSAEngine
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV79VulkanFusedVSAAndNestedCEGIS(unittest.TestCase):
    """Empirical audit suite for v7.9.0 Vulkan Wave64 fused PERMUTE+XOR & nested-loop Z3 CEGIS."""

    def test_01_vulkan_wave64_fused_permuted_xor_bit_exact_vs_cpu(self):
        """RX 580 Wave64 shader `vsa_batch_permuted_xor.spv` matches CPU reference bit-exactly."""
        eng = VulkanBatchVSAEngine()
        self.assertTrue(eng.permuted_xor_spv_path.exists(), "Compiled vsa_batch_permuted_xor.spv missing.")
        magic = struct.unpack("<I", eng.permuted_xor_spv_path.read_bytes()[:4])[0]
        self.assertEqual(magic, 0x07230203)

        rng = np.random.default_rng(7901)
        n = 512
        a_cands = rng.integers(0, np.iinfo(np.uint64).max, size=(n, 160), dtype=np.uint64)
        b_cands = rng.integers(0, np.iinfo(np.uint64).max, size=(n, 160), dtype=np.uint64)

        for sh in (0, 64, 199):
            q = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)
            cpu_res = eng.batch_permuted_xor_distances(q, a_cands, b_cands, shift_steps=sh, prefer_gpu=False)
            gpu_res = eng.batch_permuted_xor_distances(q, a_cands, b_cands, shift_steps=sh, prefer_gpu=True)
            np.testing.assert_array_equal(gpu_res["distances"], cpu_res["distances"])
            if eng.is_available:
                self.assertTrue(gpu_res["gpu_executed"], f"Expected RX 580 GPU execution for shift={sh}")

    def test_02_nested_loop_z3_double_induction_cegis(self):
        """Proves O(n*m) and O(n^2) nested loop closed forms via Z3 inner + outer induction."""
        synth = CEGISCodeSynthesizer()

        r_rect = synth.synthesize_nested_loop_closed_form_cegis(
            "def rect_scale(x, n, m):\n    acc = 0\n    for i in range(n):\n        for j in range(m):\n            acc += x * 4\n    return acc\n"
        )
        self.assertTrue(r_rect["is_equivalent"])
        self.assertEqual(r_rect["z3_inner_proof"], "unsat")
        self.assertEqual(r_rect["z3_outer_base"], "unsat")
        self.assertEqual(r_rect["z3_outer_step"], "unsat")
        self.assertIn("<< 2", r_rect["candidate_code"])

        r_tri = synth.synthesize_nested_loop_closed_form_cegis(
            "def tri_pairs(n):\n    acc = 0\n    for i in range(n):\n        for j in range(i):\n            acc = acc + 1\n    return acc\n"
        )
        self.assertTrue(r_tri["is_equivalent"])
        self.assertEqual(r_tri["z3_inner_proof"], "unsat")
        self.assertEqual(r_tri["candidate_code"], "n * (n - 1) >> 1")

        r_wtri = synth.synthesize_nested_loop_closed_form_cegis(
            "def tri_weighted(x, n):\n    acc = 0\n    for i in range(n):\n        for j in range(i + 1):\n            acc = acc + x\n    return acc\n"
        )
        self.assertTrue(r_wtri["is_equivalent"])
        self.assertIn("n * (n + 1) >> 1", r_wtri["candidate_code"])

    def test_03_arena_track_j_and_runtime_v79(self):
        tj = bench_track_j_vulkan_fused_vsa_and_nested_cegis()
        self.assertTrue(tj["exact_pair_hit_hamming_0"])
        self.assertTrue(tj["rect_proven"] and tj["tri_proven"])

        rt = SovereignCortexRuntime()
        self.assertIn("MODULAR-AGI", rt.version)
        self.assertIn("SOVEREIGN", rt.version)


if __name__ == "__main__":
    unittest.main()
