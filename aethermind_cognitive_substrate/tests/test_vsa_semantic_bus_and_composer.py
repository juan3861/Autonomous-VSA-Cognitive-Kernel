"""Discovery-100 Mathematical Audit Suite: VSA Hyperdimensional Bus & Autonomous Composer.

Validates the holographic algebra of the 10,240-bit semantic bus and the provable
safety properties of the dynamic Autonomous Cognitive Composer.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
import unittest
import numpy as np

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aethermind_cognitive_substrate.memory_vault.vsa_semantic_bus import (
    VSAHyperdimensionalBus,
    VSAEvent
)
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import (
    AutonomousCognitiveComposer,
    CompositionReceipt
)
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestVSASemanticBusAndComposer(unittest.TestCase):
    """Test suite for 10,240-bit VSA semantic bus and Autonomous Cognitive Composer."""

    def setUp(self):
        self.bus = VSAHyperdimensionalBus(dimension=10240, seed=42)
        self.composer = AutonomousCognitiveComposer(bus=self.bus)

    def test_01_vsa_hyperdimensional_algebra_orthogonality(self):
        """Verify concentration of measure: random 10,240-bit hypervectors are quasi-orthogonal."""
        u = self.bus.vsa.generate_random_hypervector()
        v = self.bus.vsa.generate_random_hypervector()
        sim = self.bus.vsa.cosine_similarity(u, v)
        # In D=10,240 dimensions, 3*sigma = 3/sqrt(10240) ~ 0.0296
        self.assertLess(abs(sim), 0.05, f"Expected quasi-orthogonality (|sim| < 0.05), got {sim}")

    def test_02_vsa_binding_self_inverse(self):
        """Verify holographic binding exact self-inverseness: (u * v) * u == v."""
        u = self.bus.vsa.register_symbol("sym_alpha")
        v = self.bus.vsa.register_symbol("sym_beta")

        bound = self.bus.vsa.bind(u, v)
        unbound = self.bus.vsa.bind(bound, u)

        sim = self.bus.vsa.cosine_similarity(unbound, v)
        self.assertAlmostEqual(sim, 1.0, places=5, msg="Unbinding must strictly restore original vector.")

    def test_03_vsa_scalar_thermometer_encoding(self):
        """Verify continuous scalar thermometer encoding preserves topological distance."""
        vec_0 = self.bus.encode_scalar("temp", 0.0, min_val=-10.0, max_val=10.0)
        vec_1 = self.bus.encode_scalar("temp", 1.0, min_val=-10.0, max_val=10.0)
        vec_9 = self.bus.encode_scalar("temp", 9.0, min_val=-10.0, max_val=10.0)

        sim_near = self.bus.vsa.cosine_similarity(vec_0, vec_1)
        sim_far = self.bus.vsa.cosine_similarity(vec_0, vec_9)

        self.assertGreater(sim_near, sim_far, "Near values must have strictly higher similarity than distant values.")
        self.assertGreater(sim_near, 0.85, "Values separated by 1/20 of range must have high cosine overlap.")

    def test_04_vsa_bus_publish_and_topic_query(self):
        """Verify event publishing and topic retrieval over the semantic bus."""
        evt1 = self.bus.publish(
            topic="state.kinematics",
            payload={"velocity": 12.5, "heading": 1.57},
            organ_id="inertial_filter"
        )
        evt2 = self.bus.publish(
            topic="safety.barrier",
            payload={"margin": 0.42, "violation": False},
            organ_id="cbf_shield"
        )

        matches = self.bus.query_by_topic("state.kinematics")
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].organ_id, "inertial_filter")
        self.assertEqual(matches[0].payload["velocity"], 12.5)

        summary = self.bus.get_bus_state_summary()
        self.assertEqual(summary["total_events"], 2)
        self.assertIn("state.kinematics", summary["topics"])
        self.assertIn("safety.barrier", summary["topics"])

    def test_05_autonomous_composer_pipeline_synthesis(self):
        """Verify dynamic DAG synthesis for different cognitive objective classes."""
        # 1. Closed-loop safe control
        p_safe = self.composer.synthesize_pipeline("safe_stabilization", {})
        self.assertIn("ukf_state_estimator", p_safe)
        self.assertIn("ilqr_trajectory_optimizer", p_safe)
        self.assertIn("cbf_control_barrier_shield", p_safe)
        self.assertIn("stl_temporal_logic_monitor", p_safe)

        # 2. Causal discovery
        p_causal = self.composer.synthesize_pipeline("causal_structure_discovery", {})
        self.assertIn("notears_causal", p_causal)
        self.assertIn("z3_formal_solver", p_causal)

        # 3. Motion navigation
        p_motion = self.composer.synthesize_pipeline("optimal_motion_planning", {})
        self.assertIn("rrt_star_planner", p_motion)

    def test_06_autonomous_composer_execution_and_receipt(self):
        """Verify end-to-end execution of a synthesized pipeline with formal certification."""
        receipt = self.composer.execute_pipeline(
            objective="safe_stabilization_closed_loop",
            spec={"observations": [0.2, -0.05], "horizon": 8}
        )

        self.assertIsInstance(receipt, CompositionReceipt)
        self.assertTrue(receipt.overall_success)
        self.assertTrue(receipt.certified_safe)
        self.assertGreater(len(receipt.stages), 2)
        self.assertGreater(len(receipt.bus_event_ids), 2)

        # Check formal guarantees present in certificate
        guarantees = receipt.formal_certificate.get("guarantees", [])
        self.assertGreaterEqual(len(guarantees), 3)
        for g in guarantees:
            self.assertTrue(g["verified"], f"Guarantee for {g['organ_id']} failed")

    def test_07_cortex_runtime_integration(self):
        """Verify integration with SovereignCortexRuntime cognitive missions."""
        runtime = SovereignCortexRuntime()

        # Publish mission
        pub_res = runtime.execute_mission(
            "vsa_bus_publish",
            {"topic": "telemetry.flight", "data": {"alt": 150.0, "pitch": 0.05}, "organ_id": "avionics"}
        )
        self.assertEqual(pub_res["result"]["status"], "PUBLISHED")

        # Query mission
        query_res = runtime.execute_mission(
            "vsa_bus_query",
            {"topic": "telemetry.flight"}
        )
        self.assertEqual(query_res["result"]["count"], 1)

        # Autonomous composition mission
        comp_res = runtime.execute_mission(
            "autonomous_compose_pipeline",
            {"objective": "safe_stabilization", "spec": {"observations": [1.0, 0.0]}}
        )
        self.assertTrue(comp_res["result"]["overall_success"])
        self.assertTrue(comp_res["result"]["certified_safe"])
        self.assertGreater(comp_res["result"]["stages_count"], 0)


if __name__ == "__main__":
    unittest.main()
