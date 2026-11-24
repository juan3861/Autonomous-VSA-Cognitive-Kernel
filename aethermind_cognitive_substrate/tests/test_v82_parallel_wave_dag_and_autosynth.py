"""Test Suite 59: v8.2.0 Typed Parallel Wave DAG & Self-Synthesizing Organs (Synthesis-on-Miss).

Empirically verifies:
1. `HierarchicalCognitivePlanner` executes independent DAG subgoals concurrently in parallel
   waves (`parallel_stages`, `ThreadPoolExecutor`) with explicit typed edge `input_bindings`
   and isolates sibling state cleanly.
2. `AutonomousCognitiveComposer.synthesize_and_register_missing_organ` & `execute_pipeline`
   synthesize missing organs from both nested-loop Python specs and raw I/O examples via
   `CEGISCodeSynthesizer` + `ASTCodeAnalyzer` + `HoareContractVerifier`, hot-plug them live,
   and execute them inside Z3-certified pipelines.
3. `SovereignCortexRuntime` carries `8.2.0` version tag.
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

from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import AutonomousCognitiveComposer
from aethermind_cognitive_substrate.planning.hierarchical_cognitive_planner import (
    HierarchicalCognitivePlanner,
    SubGoalSpec,
)
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV82ParallelWaveDAGAndAutoSynth(unittest.TestCase):
    """Empirical audit suite for v8.2.0 parallel wave planning & synthesis-on-miss."""

    def test_01_parallel_wave_dag_and_typed_edge_bindings(self):
        composer = AutonomousCognitiveComposer()
        planner = HierarchicalCognitivePlanner(composer=composer)

        # Register two lightweight custom plugins to feed deterministic typed outputs across diamond waves
        from aethermind_cognitive_substrate.planning.organ_capability_registry import OrganCapability
        composer.registry.register_plugin(
            OrganCapability(
                organ_id="wave_src_alpha",
                category="estimation",
                description="Produces calibrated observation vector x_obs",
                inputs=["seed_val"],
                outputs=["alpha_vec"],
                formal_guarantee="Deterministic 4D bounded state vector.",
            ),
            executor=lambda ctx: {"alpha_vec": [float(ctx.get("seed_val", 0.25)), 0.1, -0.05, 0.0], "sat_status": "sat"},
        )
        composer.registry.register_plugin(
            OrganCapability(
                organ_id="wave_src_beta",
                category="logic_symbolic",
                description="Produces symbolic scalar threshold margin",
                inputs=["beta_in"],
                outputs=["beta_margin"],
                formal_guarantee="Positive safety margin invariant.",
            ),
            executor=lambda ctx: {"beta_margin": float(ctx.get("beta_in", 0.45)), "sat_status": "sat"},
        )

        subgoals = [
            SubGoalSpec(
                subgoal_id="sg_alpha",
                objective="calibrated vector generation",
                spec={"custom_pipeline": ["wave_src_alpha", "z3_formal_solver"], "seed_val": 0.2},
            ),
            SubGoalSpec(
                subgoal_id="sg_beta",
                objective="scalar threshold synthesis",
                spec={"custom_pipeline": ["wave_src_beta", "z3_formal_solver"], "beta_in": 0.55},
            ),
            SubGoalSpec(
                subgoal_id="sg_join",
                objective="safe trajectory stabilization",
                dependencies=["sg_alpha", "sg_beta"],
                input_bindings={
                    "observations": ("sg_alpha", "alpha_vec"),
                    "trigger_threshold": ("sg_beta", "beta_margin"),
                },
                spec={"custom_pipeline": ["ukf_state_estimator", "cbf_control_barrier_shield"]},
            ),
        ]

        res = planner.execute_hierarchical_mission("diamond_parallel_wave_mission", subgoals, parallel_waves=True)
        self.assertTrue(res["overall_success"])
        self.assertTrue(res["certified_safe"])
        sched = res["macro_schedule"]
        self.assertEqual(sched["waves_executed"], 2)
        self.assertEqual(sched["max_wave_width"], 2)
        self.assertTrue(sched["parallel_execution_used"])
        self.assertEqual(sched["typed_bindings_resolved"], 2)
        self.assertEqual(res["avx2_wx_jit_mode"], 1)

    def test_02_synthesis_on_miss_nested_loop_and_io_examples(self):
        composer = AutonomousCognitiveComposer()

        # A: Missing nested-loop triangular pair accumulator synthesized on-the-fly -> O(1) Z3-proven organ
        r_loop = composer.execute_pipeline(
            "triangular pair accumulator",
            {
                "synthesize_on_miss": True,
                "synthesize_organ_id": "auto_tri_pairs_v82",
                "missing_organ_source": (
                    "def tri_pairs_v82(n):\n"
                    "    acc = 0\n"
                    "    for i in range(n):\n"
                    "        for j in range(i):\n"
                    "            acc = acc + 1\n"
                    "    return acc\n"
                ),
                "n": 10,
            },
        )
        self.assertTrue(r_loop.overall_success)
        self.assertTrue(r_loop.certified_safe)
        synth_rec = r_loop.formal_certificate.get("synthesized_organ_receipt")
        self.assertIsNotNone(synth_rec)
        self.assertTrue(synth_rec["registered"])
        self.assertEqual(synth_rec["candidate_code"], "n * (n - 1) >> 1")
        self.assertIn("auto_tri_pairs_v82", [s.organ_id for s in r_loop.stages])
        stage_data = next(s.data for s in r_loop.stages if s.organ_id == "auto_tri_pairs_v82")
        self.assertEqual(stage_data["synthesized_output"], 45)

        # B: Missing arithmetic shift synthesized from raw I/O examples + Hoare contract verification
        r_io = composer.execute_pipeline(
            "octuple bitshift scaling",
            {
                "synthesize_on_miss": True,
                "synthesize_organ_id": "auto_octuple_v82",
                "io_examples": [({"x": 2}, 16), ({"x": 5}, 40), ({"x": -3}, -24)],
                "hoare_contract": {
                    "declarations": {"x": "int"},
                    "precondition": "x == 7",
                    "assignment_var": "x",
                    "assigned_expr": "x * 8",
                    "postcondition": "x == 56",
                },
                "x": 7,
            },
        )
        self.assertTrue(r_io.overall_success)
        self.assertTrue(r_io.certified_safe)
        io_rec = r_io.formal_certificate.get("synthesized_organ_receipt")
        self.assertTrue(io_rec["registered"])
        self.assertEqual(io_rec["candidate_code"], "x << 3")
        io_stage = next(s.data for s in r_io.stages if s.organ_id == "auto_octuple_v82")
        self.assertEqual(io_stage["synthesized_output"], 56)

    def test_03_runtime_v82_version(self):
        rt = SovereignCortexRuntime()
        self.assertIn("8.2.0", rt.version)


if __name__ == "__main__":
    unittest.main()
