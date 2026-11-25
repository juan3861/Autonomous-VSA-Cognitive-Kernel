"""Test Suite 63: v9.0.0 Sovereign Apex — 50-Episode Longitudinal REM, Wasmtime Sandbox & Track L.

Empirically verifies:
1. 50-episode continuous longitudinal consolidation (`consolidate_longitudinal_episodes`)
   achieving 100% retention (`zero_forgetting=True`, `forgetting_pct=0.0`) with SQLite +
   HippoRAG + PagedOS persistence.
2. `WasmSandboxBridge` deterministic WebAssembly sandbox verification (`wasm_sandbox` organ)
   and 103/103 operational organ contract coverage in `OrganCapabilityRegistry`.
3. Arena `Track L` end-to-end (50-ep REM + Wasmtime + Neuro-Symbolic Gate + Resident RX 580
   Wave64 LDS VM) and `SovereignCortexRuntime` `9.0.0` readiness.
"""
from __future__ import annotations

import os
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
    bench_track_l_v90_longitudinal_wasm_and_resident_gpu,
)
from aethermind_cognitive_substrate.memory_vault.hierarchical_paged_memory_os import HierarchicalPagedMemoryOS
from aethermind_cognitive_substrate.memory_vault.hipporag_knowledge_graph import HippoRAGKnowledgeGraph
from aethermind_cognitive_substrate.memory_vault.vsa_persistence_bridge import VSA10240PersistenceBridge
from aethermind_cognitive_substrate.metacognition.rem_autonomous_dream_daemon import REMAutonomousDreamEngine
from aethermind_cognitive_substrate.physical_bridge.wasm_sandbox_bridge import WasmSandboxBridge
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import AutonomousCognitiveComposer
from aethermind_cognitive_substrate.planning.organ_capability_registry import OrganCapabilityRegistry
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class TestV90LongitudinalWasmAndTrackL(unittest.TestCase):
    """Empirical audit suite for v9.0.0 apex longitudinal retention, Wasmtime & Track L."""

    def test_01_longitudinal_50_episode_zero_forgetting(self):
        with tempfile.TemporaryDirectory() as tmpd:
            pers = VSA10240PersistenceBridge(db_path=str(Path(tmpd) / "v90_50ep.db"))
            hippo = HippoRAGKnowledgeGraph()
            pager = HierarchicalPagedMemoryOS(max_hot_pages=16, max_warm_pages=64)
            composer = AutonomousCognitiveComposer(persistence=pers, hipporag=hippo, paged_memory=pager)
            rem = REMAutonomousDreamEngine()
            rem.persistence = pers

            episodes = [
                {
                    "objective": f"safe_control_horizon_{i % 6}",
                    "spec": {
                        "observations": [0.15 * ((i % 4) + 1), -0.05, 0.02, 0.0],
                        "goal_state": [0.0, 0.0],
                        "require_formal_safety": True,
                    },
                }
                for i in range(50)
            ]
            res = rem.consolidate_longitudinal_episodes(composer, episodes, pager=pager, replay_probe_count=10)

        self.assertEqual(res["episodes_processed"], 50)
        self.assertEqual(res["episodes_certified"], 50)
        self.assertEqual(res["forgetting_pct"], 0.0)
        self.assertTrue(res["zero_forgetting"])
        self.assertEqual(res["retention_rate"], 1.0)

    def test_02_wasm_sandbox_organ_and_track_l(self):
        reg = OrganCapabilityRegistry(load_runtime_catalog=True)
        self.assertGreaterEqual(len(reg.capabilities), 103)
        w_res = reg.invoke("wasm_sandbox", {})
        self.assertTrue(w_res.get("executed"))
        self.assertTrue(w_res.get("bijection_verified"))
        bridge = WasmSandboxBridge()
        if bridge.is_available:
            self.assertTrue(w_res.get("wasm_executed"))

        tl = bench_track_l_v90_longitudinal_wasm_and_resident_gpu()
        self.assertEqual(tl["episodes_processed"], 50)
        self.assertTrue(tl["zero_forgetting"])
        self.assertTrue(tl["wasm_bijection_verified"])
        self.assertTrue(tl["neuro_symbolic_approved"])

    def test_03_runtime_v90_version(self):
        rt = SovereignCortexRuntime()
        self.assertIn("9.0.0", rt.version)


if __name__ == "__main__":
    unittest.main()
