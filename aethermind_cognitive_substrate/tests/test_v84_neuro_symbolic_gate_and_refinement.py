"""Test Suite 61: v8.4.0 Zero-Trust Neuro-Symbolic Proposal -> Formal Verifier Gate.

Empirically verifies:
1. Untrusted adversarial proposals (`os.system`, wrong AST candidate `x * 7` vs `x * 8`,
   and out-of-envelope control actions) are unconditionally blocked by AST/Z3/CBF gates
   with explicit counterexample feedback.
2. Counterexample-guided refinement converges to certified execution (`x << 3` and CBF-safe
   control + verified DAG pipeline).
3. `neuro_symbolic_bridge` integrates cleanly into the 102+-organ registry and `8.4.0` runtime.
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

from aethermind_cognitive_substrate.planning.neuro_symbolic_bridge import VerifiedNeuroSymbolicBridge
from aethermind_cognitive_substrate.planning.organ_capability_registry import OrganCapabilityRegistry
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


class _AdversarialThenCorrectedProposer:
    """Simulates a flawed/unsafe proposer refined via formal counterexample feedback."""

    def propose_candidates(self, task_prompt, context, counterexample_feedback):
        if len(counterexample_feedback) == 0:
            # Round 1: unsafe OS call
            return [{"kind": "python_code", "source_code": "import os\ndef f(x):\n    os.system('calc')\n    return x * 8\n"}]
        if len(counterexample_feedback) == 1:
            # Round 2: mathematically wrong candidate (Z3 counterexample expected!)
            return [{"kind": "python_code", "source_code": "def f(x):\n    return x * 7\n"}]
        # Round 3: refined optimal shift matching spec
        return [{"kind": "python_code", "source_code": "def f(x):\n    return x << 3\n"}]


class TestV84NeuroSymbolicGate(unittest.TestCase):
    """Empirical audit suite for v8.4.0 Zero-Trust neuro-symbolic verification."""

    def test_01_adversarial_rejection_and_counterexample_refinement(self):
        bridge = VerifiedNeuroSymbolicBridge(proposer=_AdversarialThenCorrectedProposer())
        res = bridge.propose_verify_and_refine(
            "optimize shift by 8",
            context={"target_spec_source": "def spec(x):\n    return x * 8\n"},
            max_rounds=4,
        )
        self.assertTrue(res["approved"])
        self.assertEqual(res["rounds_taken"], 3)
        self.assertEqual(res["rejected_count"], 2)
        self.assertEqual(res["rejected_history"][0]["gate"], "AST_SECURITY_BARRIER")
        self.assertEqual(res["rejected_history"][1]["gate"], "Z3_EQUIVALENCE_BARRIER")
        self.assertIsNotNone(res["rejected_history"][1]["counterexample"])
        self.assertEqual(res["verification"]["gate"], "FORMAL_CODE_CERTIFIED")

    def test_02_cbf_barrier_rejection_and_dag_gate(self):
        bridge = VerifiedNeuroSymbolicBridge()
        rej = bridge.verify_proposal(
            {"kind": "control_action", "x_state": [0.1, 0.1, 0.0, 0.0], "u_nominal": [9.0, 9.0, 0.0, 0.0]},
            context={"max_nominal_norm": 2.0},
        )
        self.assertFalse(rej["approved"])
        self.assertEqual(rej["gate"], "CBF_NOMINAL_BOUND_BARRIER")

        refined = bridge.propose_verify_and_refine(
            "safe stabilization control",
            context={"proposal_kind": "control_action", "nominal_control": [2.4, 0.0, 0.0, 0.0], "max_nominal_norm": 1.0},
            max_rounds=3,
        )
        self.assertTrue(refined["approved"])
        self.assertGreaterEqual(refined["rounds_taken"], 2)

        dag_rej = bridge.verify_proposal({"kind": "dag_pipeline", "pipeline": ["ukf_state_estimator"]}, context={"require_formal_safety": True})
        self.assertFalse(dag_rej["approved"])
        self.assertEqual(dag_rej["gate"], "Z3_DAG_CONTRACT_BARRIER")

    def test_03_registry_integration_and_runtime_v84(self):
        reg = OrganCapabilityRegistry(load_runtime_catalog=True)
        self.assertGreaterEqual(len(reg.capabilities), 102)
        res = reg.invoke("neuro_symbolic_bridge", {})
        self.assertTrue(res.get("executed"))
        self.assertTrue(res.get("approved"))

        rt = SovereignCortexRuntime()
        self.assertIn("8.4.0", rt.version)


if __name__ == "__main__":
    unittest.main()
