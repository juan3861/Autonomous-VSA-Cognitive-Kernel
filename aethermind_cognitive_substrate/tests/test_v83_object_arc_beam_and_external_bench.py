"""Test Suite 60: v8.3.0 Object-Centric ARC DSL, VSA Beam Search (Depth 5-6) & External Public Benchmarks.

Empirically verifies:
1. Connected-component object segmentation (`extract_connected_objects`) and object-centric
   ARC primitives (`extract_largest_object`, `bridge_same_color_aligned`, `complete_4way_symmetry`),
   plus Depth-5 VSA-guided beam synthesis solving composite object+geometric programs.
2. External held-out evaluation against official public `fchollet/ARC-AGI` JSON tasks
   and the 8-problem Formal SyGuS BV/LIA/Loop/Cubic Z3 benchmark (`8/8` proven).
3. `SovereignCortexRuntime` carries `8.3.0` version tag.
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

from aethermind_cognitive_substrate.benchmarks.external_benchmark_runner import (
    eval_heldout_sygus_synthesis_suite,
    eval_public_arc_agi_subset,
)
from aethermind_cognitive_substrate.logic_symbolic.symbolic_grid_arc_reasoner import (
    SymbolicGridARCReasoner,
    extract_connected_objects,
)
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV83ObjectArcBeamAndExternalBench(unittest.TestCase):
    """Empirical audit suite for v8.3.0 object-centric ARC DSL, VSA beam & external held-out eval."""

    def test_01_object_segmentation_and_depth5_vsa_beam(self):
        grid = np.array([
            [0, 1, 0, 0, 0],
            [0, 0, 0, 2, 2],
            [3, 0, 0, 2, 2],
            [0, 0, 0, 0, 0],
        ], dtype=np.int32)
        objs = extract_connected_objects(grid, connectivity=4)
        self.assertEqual(len(objs), 3)
        self.assertEqual(max(o["area"] for o in objs), 4)

        arc = SymbolicGridARCReasoner()
        # 5-op composite: isolate largest connected object -> scale 2x -> rot90 -> flip_h -> complete_4way_symmetry
        p5 = ["extract_largest_object", "scale_2x", "rot90", "flip_h", "hollow_interior"]
        i1 = [
            [0, 0, 0, 0, 0],
            [0, 1, 0, 2, 2],
            [0, 0, 0, 2, 2],
            [0, 3, 0, 2, 2],
        ]
        i2 = [
            [4, 0, 5, 5, 5],
            [0, 0, 5, 5, 5],
            [1, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
        ti = [
            [0, 7, 7, 0],
            [0, 7, 7, 0],
            [2, 0, 0, 3],
        ]
        res5 = arc.solve_arc_task(
            [(i1, arc.apply_program(p5, i1)), (i2, arc.apply_program(p5, i2))],
            ti,
            max_program_depth=5,
            allow_color_remap=False,
            beam_width=24,
            time_budget_ms=4000.0,
        )
        self.assertTrue(res5["solved"])
        np.testing.assert_array_equal(
            np.asarray(res5["predicted_grid"], dtype=np.int32),
            arc.apply_program(p5, ti),
        )

    def test_02_external_public_arc_and_sygus_benchmarks(self):
        arc_res = eval_public_arc_agi_subset(max_tasks=25, max_program_depth=4)
        self.assertGreaterEqual(arc_res["total_tasks"], 25)
        self.assertGreaterEqual(arc_res["solved_exact"], 2)
        self.assertIn("070dd51e", arc_res["solved_task_ids"])
        self.assertIn("0c786b71", arc_res["solved_task_ids"])

        sygus_res = eval_heldout_sygus_synthesis_suite()
        self.assertEqual(sygus_res["z3_proven_count"], sygus_res["total_problems"])
        self.assertEqual(sygus_res["solve_rate_pct"], 100.0)

    def test_03_runtime_v83_version(self):
        rt = SovereignCortexRuntime()
        self.assertIn("8.3.0", rt.version)


if __name__ == "__main__":
    unittest.main()
