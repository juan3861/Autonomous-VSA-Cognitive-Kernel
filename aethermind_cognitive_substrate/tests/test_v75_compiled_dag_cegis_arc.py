"""Test Suite 52: v7.5.0 Compiled AVX2 DAG Routes, Python AST CEGIS & Hierarchical ARC Reasoning.

Empirically verifies:
1. Native AVX2 L1 Bytecode Compilation of DAG Routes + Bijection Proof (`tail_inversion_hamming == 0`).
2. Real Python AST CEGIS Synthesizer + E-Graph + Z3 BitVec(64) proofs (`unsat` across 2^64 inputs).
3. ARC-Style Symbolic Grid Reasoning (1-op & 2-op compositional transforms + Z3 conservation invariants).
4. Macro -> Meso -> Micro Hierarchical Cognitive Planning with x86_64 AVX2 W^X JIT route fusion.
5. SovereignCortexRuntime v7.5.0 integration & Arena Tracks E/F.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aethermind_cognitive_substrate.benchmarks.agi_modular_arena import (
    bench_track_e_python_ast_cegis,
    bench_track_f_hierarchical_arc_avx2,
)
from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
from aethermind_cognitive_substrate.logic_symbolic.symbolic_grid_arc_reasoner import SymbolicGridARCReasoner
from aethermind_cognitive_substrate.memory_vault.vsa_dag_compiler import VSADAGBytecodeCompiler
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import AutonomousCognitiveComposer
from aethermind_cognitive_substrate.planning.hierarchical_cognitive_planner import (
    HierarchicalCognitivePlanner,
    SubGoalSpec,
)
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV75CompiledDAGCEGISARC(unittest.TestCase):
    """Empirical test suite for v7.5.0 compiled AVX2 DAG routes, Python AST CEGIS, and ARC reasoning."""

    def test_01_compiled_avx2_dag_route_bijection(self):
        """Compiles DAG routes to L1 AVX2 bytecode and proves tail unbinding identity."""
        comp = VSADAGBytecodeCompiler()
        self.assertTrue(comp.is_native_ready, "Native vsa_eval_graph_bytecode must be loaded.")

        organs = [
            "ukf_state_estimator",
            "ilqr_trajectory_optimizer",
            "cbf_control_barrier_shield",
            "stl_temporal_logic_monitor",
        ]
        route = comp.compile_route(organs, objective="safe_stabilization")
        res = comp.execute_route(route)

        self.assertTrue(res["bijection_verified"])
        self.assertEqual(res["tail_inversion_hamming"], 0)
        self.assertIn(res["backend"], ("CYTHON_ZERO_COPY", "RUST_C_ABI_AVX2"))
        self.assertTrue(4400 <= res["objective_orthogonality_hamming"] <= 5840)

        # Also verified automatically inside AutonomousCognitiveComposer receipts
        composer = AutonomousCognitiveComposer()
        rec = composer.execute_pipeline("safe_stabilization", {"observations": [0.2, -0.1, 0.05, 0.0]})
        self.assertTrue(rec.overall_success)
        avx2_trace = rec.formal_certificate.get("avx2_route_trace")
        self.assertIsNotNone(avx2_trace)
        self.assertTrue(avx2_trace["bijection_verified"])
        self.assertEqual(avx2_trace["tail_inversion_hamming"], 0)

    def test_02_real_python_ast_cegis_and_z3_proof(self):
        """Synthesizes cheaper equivalent Python AST expressions proven across all 2^64 integers."""
        synth = CEGISCodeSynthesizer()

        r1 = synth.synthesize_python_ast_cegis("def mul8(x, y): return (x * 8) + (y ^ y)")
        self.assertTrue(r1["is_equivalent"])
        self.assertEqual(r1["z3_status"], "unsat")
        self.assertGreater(r1["cycle_speedup_ratio"], 1.5)
        self.assertIn("<< 3", r1["candidate_code"])

        r2 = synth.synthesize_python_ast_cegis("def mod4(x): return (x % 4) == 0")
        self.assertTrue(r2["is_equivalent"])
        self.assertEqual(r2["candidate_code"], "x & 3 == 0")

        r3 = synth.synthesize_python_ast_cegis("def cancel(x, y): return (x + y) - y")
        self.assertTrue(r3["is_equivalent"])
        self.assertEqual(r3["candidate_code"], "x")

        with self.assertRaises(ValueError):
            synth.synthesize_python_ast_cegis("eval(x)")

    def test_03_arc_symbolic_grid_compositional_induction(self):
        """Induces 2-op spatial transform program from few-shot grids and proves Z3 invariants."""
        reasoner = SymbolicGridARCReasoner()
        # Task: crop non-zero bounding box -> scale 2x
        train_pairs = [
            (
                [[0, 0, 0, 0], [0, 1, 2, 0], [0, 0, 3, 0], [0, 0, 0, 0]],
                [[1, 1, 2, 2], [1, 1, 2, 2], [0, 0, 3, 3], [0, 0, 3, 3]],
            ),
            (
                [[0, 4, 0], [0, 5, 6], [0, 0, 0]],
                [[4, 4, 0, 0], [4, 4, 0, 0], [5, 5, 6, 6], [5, 5, 6, 6]],
            ),
        ]
        test_in = [[0, 0, 0], [0, 7, 8], [0, 9, 0]]
        res = reasoner.solve_arc_task(train_pairs, test_in, max_program_depth=2)

        self.assertTrue(res["solved"])
        self.assertEqual(res["synthesized_program"], ["crop_nonzero", "scale_2x"])
        self.assertEqual(
            res["predicted_grid"],
            [[7, 7, 8, 8], [7, 7, 8, 8], [9, 9, 0, 0], [9, 9, 0, 0]],
        )
        self.assertTrue(res["z3_proof"]["z3_verified"])

    def test_04_hierarchical_multi_level_planning_and_runtime(self):
        """Macro -> Meso -> Micro hierarchical composition fuses subgoal signatures via AVX2 W^X JIT."""
        rt = SovereignCortexRuntime()
        self.assertIn("7.5.0", rt.version)

        res = rt.execute_cognitive_mission(
            "hierarchical_compose_mission",
            {
                "mission_name": "v75_hierarchical_validation",
                "subgoals": [
                    {
                        "subgoal_id": "sg_ast",
                        "objective": "ast code inspection",
                        "spec": {"source_code": "def scale(x): return x * 4", "require_formal_safety": True},
                    },
                    {
                        "subgoal_id": "sg_cegis",
                        "objective": "cegis inductive python code optimization verification",
                        "spec": {"cegis_mode": "python_ast", "cegis_source": "def scale(x): return x * 4"},
                        "dependencies": ["sg_ast"],
                    },
                    {
                        "subgoal_id": "sg_ctrl",
                        "objective": "safe_stabilization",
                        "spec": {"observations": [0.2, -0.1, 0.05, 0.0]},
                        "dependencies": ["sg_cegis"],
                    },
                ],
            },
        )["result"]

        self.assertTrue(res["overall_success"])
        self.assertTrue(res["certified_safe"])
        self.assertEqual(res["subgoals_executed"], 3)
        self.assertEqual(res["avx2_wx_jit_mode"], 1, "Expected native x86_64 AVX2 W^X JIT fusion")
        self.assertEqual(res["macro_schedule"]["execution_order"], ["sg_ast", "sg_cegis", "sg_ctrl"])

    def test_05_arena_tracks_e_and_f(self):
        """Arena tracks E (Real Python AST CEGIS) and F (Hierarchical ARC + JIT) pass cleanly."""
        te = bench_track_e_python_ast_cegis()
        self.assertTrue(te["scale_proven"] and te["mod4_proven"])

        tf = bench_track_f_hierarchical_arc_avx2()
        self.assertTrue(tf["overall_success"] and tf["certified_safe"] and tf["arc_stage_executed"])


if __name__ == "__main__":
    unittest.main()
