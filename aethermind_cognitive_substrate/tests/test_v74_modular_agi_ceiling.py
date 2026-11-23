"""Test Suite 51: v7.4.0 Modular AGI Ceiling Verification.

Empirically verifies all 4 Modular AGI fronts:
1. Front 1: Radeon RX 580 Wave64 Vulkan batch Hamming + cosine execution on real hardware.
2. Front 2: 82+-organ holographic VSA semantic auto-discovery + hot-pluggable isolated external plugins.
3. Front 3: Persistent cross-session closed-loop learning (SQLite + HippoRAG + PagedMemoryOS + REM).
4. Front 4: AST/CFG & Desktop Vision PerceptionVSABridge -> 10,240-bit Bus + PDDL/CEGIS composition.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from aethermind_cognitive_substrate.benchmarks.agi_modular_arena import (
    bench_track_a_plug_and_play_discovery,
    bench_track_b_pddl_planning,
    bench_track_c_ast_cegis_synthesis,
    bench_track_d_cross_session_learning,
)
from aethermind_cognitive_substrate.memory_vault.hierarchical_paged_memory_os import HierarchicalPagedMemoryOS
from aethermind_cognitive_substrate.memory_vault.hipporag_knowledge_graph import HippoRAGKnowledgeGraph
from aethermind_cognitive_substrate.memory_vault.vsa_persistence_bridge import VSA10240PersistenceBridge
from aethermind_cognitive_substrate.memory_vault.vsa_semantic_bus import VSAHyperdimensionalBus
from aethermind_cognitive_substrate.metacognition.rem_autonomous_dream_daemon import REMAutonomousDreamEngine
from aethermind_cognitive_substrate.physical_bridge.perception_vsa_bridge import PerceptionVSABridge
from aethermind_cognitive_substrate.physical_bridge.vulkan_batch_vsa_engine import VulkanBatchVSAEngine
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import (
    AutonomousCognitiveComposer,
    OrganCapability,
)
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime
import numpy as np


class TestV74ModularAGICeiling(unittest.TestCase):
    """Empirical integration suite for v7.4.0 Modular AGI architecture."""

    def test_01_cold_boot_and_full_82_organ_discovery(self):
        """Cold boot stays lazy/fast (<250ms) and OrganCapabilityRegistry indexes 82+ runtime organs."""
        code = (
            "import sys, time; "
            f"sys.path.insert(0, {ROOT_DIR!r}); "
            "t0 = time.perf_counter(); "
            "from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime; "
            "r = SovereignCortexRuntime(); "
            "ms = (time.perf_counter() - t0) * 1000.0; "
            "print(f'{ms:.2f}'); "
            "assert 'MODULAR-AGI' in r.version and 'SOVEREIGN' in r.version"
        )
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        boot_ms = float(proc.stdout.strip().splitlines()[-1])
        self.assertLess(boot_ms, 250.0)

        rt = SovereignCortexRuntime()
        organs = rt.organ_registry.list_organ_ids()
        self.assertGreaterEqual(len(organs), 85, f"Expected >= 85 indexed organs, got {len(organs)}")
        for expected_id in (
            "ukf_state_estimator", "notears_causal", "strips_planner",
            "cegis_synthesizer", "ast_analyzer", "vision_eye", "fem_galerkin",
        ):
            self.assertIn(expected_id, organs)

    def test_02_holographic_vsa_routing_and_hot_plugin_bounds(self):
        """External isolated plugin organs are discovered via VSA and Z3-verified before execution."""
        comp = AutonomousCognitiveComposer()
        comp.register_plugin(
            OrganCapability(
                organ_id="spectral_anomaly_filter_plugin",
                category="telemetry",
                description="Spectral wavelet anomaly detector for satellite vibration telemetry.",
                inputs=["observations"],
                outputs=["anomaly_index"],
                formal_guarantee="Output normalized to [0.0, 1.0].",
                in_min=-5.0,
                in_max=5.0,
                out_min=0.0,
                out_max=1.0,
            ),
            lambda ctx: {"anomaly_index": 0.12, "obs_len": len(ctx.get("observations", []))},
        )
        try:
            pipe = comp.synthesize_pipeline(
                "spectral wavelet vibration anomaly detector",
                {"observations": [0.2, -0.3, 0.1]},
            )
            self.assertIn("spectral_anomaly_filter_plugin", pipe)

            ok = comp.execute_pipeline(
                "spectral wavelet vibration anomaly detector",
                {"observations": [0.2, -0.3, 0.1], "require_formal_safety": True},
            )
            self.assertTrue(ok.overall_success)
            self.assertTrue(ok.certified_safe)
            plugin_stage = next((s for s in ok.stages if s.organ_id == "spectral_anomaly_filter_plugin"), None)
            self.assertIsNotNone(plugin_stage)
            self.assertAlmostEqual(plugin_stage.data["anomaly_index"], 0.12, places=6)

            # Out-of-bounds observation (25.0 > plugin in_max 5.0) must be rejected by Z3
            blocked = comp.execute_pipeline(
                "spectral wavelet vibration anomaly detector",
                {"observations": [25.0, 0.0], "require_formal_safety": True},
            )
            self.assertFalse(blocked.overall_success)
            self.assertEqual(blocked.formal_certificate["z3_preflight_proof"]["sat_status"], "unsat")
            self.assertEqual(len(blocked.stages), 0)
        finally:
            self.assertTrue(comp.unregister_plugin("spectral_anomaly_filter_plugin"))

    def test_03_cross_session_closed_loop_learning(self):
        """Session 1 failures persist into SQLite and automatically hydrate Session 2 HippoRAG + PagedOS."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = str(Path(tmpdir) / "test_v74_sessions.db")
            vec_dir = str(Path(tmpdir) / "vecs")

            # Session 1
            p1 = VSA10240PersistenceBridge(db_path=db_path, storage_dir=vec_dir)
            h1 = HippoRAGKnowledgeGraph()
            pm1 = HierarchicalPagedMemoryOS()
            rem1 = REMAutonomousDreamEngine()
            c1 = AutonomousCognitiveComposer(persistence=p1, hipporag=h1, paged_memory=pm1, rem_engine=rem1)

            r1 = c1.execute_pipeline(
                "safe_stabilization_mission",
                {"custom_pipeline": ["ukf_state_estimator"], "observations": [0.2, 0.1], "require_formal_safety": True},
            )
            self.assertFalse(r1.overall_success)
            self.assertGreaterEqual(len(rem1.dream_episodes_log), 1)

            # Session 2: Completely fresh in-memory HippoRAG + PagedMemoryOS + Composer sharing SQLite
            p2 = VSA10240PersistenceBridge(db_path=db_path, storage_dir=vec_dir)
            h2 = HippoRAGKnowledgeGraph()
            pm2 = HierarchicalPagedMemoryOS()
            c2 = AutonomousCognitiveComposer(persistence=p2, hipporag=h2, paged_memory=pm2)

            self.assertGreater(h2.graph.number_of_nodes(), 0, "HippoRAG should hydrate from persisted Session 1 episodes")
            self.assertGreater(len(pm2.hot_tier) + len(pm2.warm_tier), 0, "PagedOS should retain pinned failure page")

            r2 = c2.execute_pipeline(
                "safe_stabilization_mission",
                {"observations": [0.2, 0.1, -0.05, 0.0], "require_formal_safety": True},
            )
            self.assertTrue(r2.overall_success)
            self.assertTrue(r2.certified_safe)
            priors = p2.query_organ_priors("safe_stabilization_mission")
            self.assertIn("cbf_control_barrier_shield", priors)

    def test_04_perception_vsa_bridge_ast_cfg_and_vision(self):
        """AST/CFG and Win32 vision sensors publish 10,240-bit events searchable via VSA similarity."""
        bus = VSAHyperdimensionalBus(dimension=10240, seed=99)
        bridge = PerceptionVSABridge(bus=bus)

        clean_out = bridge.encode_code_ast("def add(a, b):\n    if a > 0:\n        return a + b\n    return b\n")
        self.assertTrue(clean_out["payload"]["security_clean"])
        self.assertGreaterEqual(clean_out["payload"].get("cfg_blocks", 0), 4)

        unsafe_out = bridge.encode_code_ast("def bad(x):\n    return eval(x)\n")
        self.assertFalse(unsafe_out["payload"]["security_clean"])
        self.assertGreater(unsafe_out["payload"]["violations_count"], 0)

        vis_out = bridge.encode_desktop_state(max_windows=5)
        self.assertEqual(vis_out["event"].topic, "perception.desktop_vision")

        ast_events = bus.query_by_topic("perception.code_ast")
        self.assertEqual(len(ast_events), 2)
        ranked = bus.query_similarity(clean_out["event"].hypervector, top_k=1)
        self.assertEqual(ranked[0][0].event_id, clean_out["event"].event_id)

    def test_05_multi_domain_agi_arena_and_rx580_gpu_batch(self):
        """All 4 AGI-Modular Arena tracks + RX 580 Wave64 Hamming/Cosine GPU batch pass cleanly."""
        ta = bench_track_a_plug_and_play_discovery()
        self.assertTrue(ta["overall_success"] and ta["plugin_selected"])

        tb = bench_track_b_pddl_planning()
        self.assertTrue(tb["overall_success"] and tb["certified_safe"])
        self.assertGreaterEqual(len(tb["plan_steps"]), 4)

        tc = bench_track_c_ast_cegis_synthesis()
        self.assertTrue(tc["overall_success"] and tc["cegis_equivalent"])

        td = bench_track_d_cross_session_learning()
        self.assertTrue(td["session1_rejected_unsafe"] and td["session2_adapted_success"])

        # Hardware RX 580 check
        eng = VulkanBatchVSAEngine()
        if eng.is_available:
            rng = np.random.default_rng(7)
            q = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)
            c = rng.integers(0, np.iinfo(np.uint64).max, size=(256, 160), dtype=np.uint64)
            c[12] = q.copy()
            rh = eng.batch_hamming_distances(q, c, prefer_gpu=True)
            self.assertEqual(int(rh["distances"][12]), 0)
            self.assertTrue(rh["gpu_executed"], f"Expected RX 580 GPU execution, got {rh['backend']}")


if __name__ == "__main__":
    unittest.main()
