"""Zero-Trust Neuro-Symbolic Proposal -> Formal Verification Bridge (v8.4.0).

Decouples untrusted candidate proposal (`NeuralProposerProtocol`, offline deterministic
fallback by default or optional plug-in neural backend) from strict mathematical
certification gates (`ASTCodeAnalyzer`, `CEGISCodeSynthesizer`, `HoareContractVerifier`,
`CBFControlBarrierShield`, `ConformalPredictionUncertaintyShield`, `Z3FormalSolver`).

No proposal is ever executed or promoted unless all domain invariants pass formally.
Rejected proposals feed concrete counterexamples back to refine subsequent proposals.
"""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

import numpy as np

from ..code_inspector.ast_code_analyzer import ASTCodeAnalyzer
from ..logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer, _eval_ast_i64
from ..memory_vault.vsa_semantic_bus import VSAHyperdimensionalBus
from ..metacognition.cbf_control_barrier_shield import CBFControlBarrierShield
from ..metacognition.conformal_prediction_uncertainty_shield import ConformalPredictionUncertaintyShield
from ..metacognition.hoare_contract_verifier import HoareContractVerifier
from .autonomous_cognitive_composer import AutonomousCognitiveComposer


@runtime_checkable
class NeuralProposerProtocol(Protocol):
    """Interface for pluggable neural/LLM or symbolic proposers under Zero-Trust gating."""

    def propose_candidates(
        self,
        task_prompt: str,
        context: Dict[str, Any],
        counterexample_feedback: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        ...


class DeterministicSymbolicProposer:
    """Zero-LLM deterministic baseline proposer using structured cues and CEGIS refinement."""

    def propose_candidates(
        self,
        task_prompt: str,
        context: Dict[str, Any],
        counterexample_feedback: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        kind = str(context.get("proposal_kind", "python_code"))
        if kind == "python_code":
            src = context.get("target_spec_source") or "def f(x):\n    return x * 8\n"
            return [{"kind": "python_code", "source_code": src, "assume_non_negative": bool(context.get("assume_non_negative", False))}]
        if kind == "control_action":
            u_nom = list(context.get("nominal_control", [0.1, -0.1, 0.0, 0.0]))
            if counterexample_feedback:
                # Dampen aggressive control on barrier rejection feedback
                u_nom = [float(v) * 0.25 for v in u_nom]
            return [{"kind": "control_action", "x_state": list(context.get("x_state", [0.1, 0.1, 0.0, 0.0])), "u_nominal": u_nom}]
        return [{"kind": "dag_pipeline", "objective": task_prompt, "pipeline": list(context.get("candidate_pipeline", ["ukf_state_estimator", "cbf_control_barrier_shield"]))}]


class VerifiedNeuroSymbolicBridge:
    """Strict Proposal-Verification engine enforcing Z3, AST, Hoare & CBF gates."""

    def __init__(
        self,
        proposer: Optional[NeuralProposerProtocol] = None,
        bus: Optional[VSAHyperdimensionalBus] = None,
        composer: Optional[AutonomousCognitiveComposer] = None,
    ):
        self.proposer: NeuralProposerProtocol = proposer or DeterministicSymbolicProposer()
        self.bus = bus or VSAHyperdimensionalBus(dimension=10240, seed=840)
        self.composer = composer
        self._ast = ASTCodeAnalyzer()
        self._cegis = CEGISCodeSynthesizer()
        self._hoare = HoareContractVerifier()
        self._cbf = CBFControlBarrierShield(state_dim=4, control_dim=4, gamma=2.0)
        self._conformal = ConformalPredictionUncertaintyShield(alpha_target=0.10, aci_gamma=0.02)
        self._conformal.calibrate([0.05, 0.08, 0.10, 0.07, 0.09])

    def verify_proposal(self, proposal: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Strictly validate a single untrusted proposal against domain safety & equivalence barriers."""
        kind = str(proposal.get("kind", "python_code"))

        if kind == "python_code":
            src = str(proposal.get("source_code", ""))
            sec = self._ast.analyze_source(src)
            if not sec.get("is_valid_syntax") or not sec.get("security_clean"):
                return {
                    "approved": False,
                    "gate": "AST_SECURITY_BARRIER",
                    "reason": "Unsafe AST construct or invalid Python syntax blocked.",
                    "violations": sec.get("violations", []),
                }

            ref_spec = context.get("target_spec_source")
            if isinstance(ref_spec, str) and ref_spec.strip():
                import ast
                # Compare proposed AST return vs target spec over CEGIS/Z3
                try:
                    t_prop = ast.parse(src)
                    t_ref = ast.parse(ref_spec)
                    fn_prop = t_prop.body[0]
                    fn_ref = t_ref.body[0]
                    prop_ret = next(n.value for n in fn_prop.body if isinstance(n, ast.Return))
                    ref_ret = next(n.value for n in fn_ref.body if isinstance(n, ast.Return))
                    arg_names = [a.arg for a in fn_ref.args.args]
                    prop_args = [a.arg for a in fn_prop.args.args]
                    if len(prop_args) != len(arg_names):
                        return {"approved": False, "gate": "Z3_SIGNATURE_MISMATCH", "reason": "Arity mismatch vs specification."}
                    pre_fn = (lambda *zargs: [v >= 0 for v in zargs]) if bool(context.get("assume_non_negative", False)) else None
                    z3_res = self._cegis.verify_equivalence_z3(
                        var_names=arg_names,
                        spec_ast_builder=lambda *zargs, rn=ref_ret, an=arg_names: _ast_eval_z3_proxy(rn, dict(zip(an, zargs))),
                        candidate_ast_builder=lambda *zargs, pn=prop_ret, pn_args=prop_args: _ast_eval_z3_proxy(pn, dict(zip(pn_args, zargs))),
                        preconditions_builder=pre_fn,
                    )
                    if not z3_res.get("is_equivalent"):
                        return {
                            "approved": False,
                            "gate": "Z3_EQUIVALENCE_BARRIER",
                            "reason": "Proposed code differs mathematically from target specification.",
                            "counterexample": z3_res.get("counterexample"),
                        }
                except Exception as exc:
                    return {
                        "approved": False,
                        "gate": "Z3_SPEC_PARSE_ERROR",
                        "reason": str(exc),
                    }

            hoare = context.get("hoare_contract")
            if isinstance(hoare, dict):
                hc = self._hoare.verify_hoare_triple_assignment(
                    declarations=dict(hoare["declarations"]),
                    precondition=str(hoare["precondition"]),
                    assignment_var=str(hoare["assignment_var"]),
                    assigned_expr=str(hoare["assigned_expr"]),
                    postcondition=str(hoare["postcondition"]),
                )
                if not hc.get("is_contract_valid"):
                    return {
                        "approved": False,
                        "gate": "HOARE_CONTRACT_BARRIER",
                        "reason": hc.get("explanation", "Hoare contract failed."),
                        "counterexample": hc.get("counterexample"),
                    }

            return {"approved": True, "gate": "FORMAL_CODE_CERTIFIED", "proposal": proposal}

        if kind == "control_action":
            x_state = list(proposal.get("x_state", context.get("x_state", [0.1, 0.1, 0.0, 0.0])))
            u_nom = list(proposal.get("u_nominal", [0.0, 0.0, 0.0, 0.0]))
            x4 = (x_state + [0.0] * 4)[:4]
            u4 = (u_nom + [0.0] * 4)[:4]
            # Strict barrier check: reject excessively large raw commands or barrier failure unless filter explicitly requested
            max_u = float(context.get("max_nominal_norm", 2.0))
            if float(np.linalg.norm(u4)) > max_u and not bool(context.get("allow_cbf_projection", False)):
                return {
                    "approved": False,
                    "gate": "CBF_NOMINAL_BOUND_BARRIER",
                    "reason": f"Nominal control norm {np.linalg.norm(u4):.3f} exceeds safe envelope {max_u:.3f}.",
                    "counterexample": {"u_nominal": u4, "max_nominal_norm": max_u},
                }
            cbf_res = self._cbf.filter_control_action(x_state=x4, u_nominal=u4)
            margin = float(min(cbf_res.get("cbf_lie_conditions", [0.0])))
            if not cbf_res.get("is_formally_safe") or margin < 0.0:
                return {
                    "approved": False,
                    "gate": "CBF_LIE_BARRIER",
                    "reason": f"CBF Lie derivative margin violated ({margin:.4f}).",
                    "counterexample": {"x_state": x4, "u_nominal": u4, "margin": margin},
                }
            conf_res = self._conformal.certify_prediction_set([float(np.linalg.norm(x4))])
            return {
                "approved": True,
                "gate": "CBF_CONFORMAL_CERTIFIED",
                "safe_control": cbf_res["u_safe_certified"],
                "safety_margin": margin,
                "conformal_covered": bool(conf_res.get("within_conformal_band", True)),
            }

        if kind == "dag_pipeline":
            comp = self.composer or AutonomousCognitiveComposer(bus=self.bus)
            pipe = list(proposal.get("pipeline", []))
            z3_dag = comp.verify_dag_contracts(pipe, context)
            if not z3_dag.get("verified"):
                return {
                    "approved": False,
                    "gate": "Z3_DAG_CONTRACT_BARRIER",
                    "reason": "Proposed pipeline lacks formal certifier or violates edge interval bounds.",
                    "z3_dag": z3_dag,
                }
            return {"approved": True, "gate": "DAG_CONTRACT_CERTIFIED", "pipeline": pipe, "z3_dag": z3_dag}

        return {"approved": False, "gate": "UNKNOWN_PROPOSAL_KIND", "reason": f"Unsupported kind={kind}"}

    def propose_verify_and_refine(
        self,
        task_prompt: str,
        context: Optional[Dict[str, Any]] = None,
        max_rounds: int = 3,
    ) -> Dict[str, Any]:
        """Closed-loop neuro-symbolic cycle: propose -> formal gate -> counterexample refine."""
        t0 = time.perf_counter()
        ctx = dict(context or {})
        feedback: List[Dict[str, Any]] = []
        rejected_history: List[Dict[str, Any]] = []

        for round_idx in range(1, max_rounds + 1):
            candidates = self.proposer.propose_candidates(task_prompt, ctx, feedback)
            for cand in candidates:
                ver = self.verify_proposal(cand, ctx)
                if ver.get("approved"):
                    self.bus.publish(
                        topic="neuro_symbolic.gate.approved",
                        payload={"task": task_prompt, "round": round_idx, "gate": ver["gate"]},
                        organ_id="neuro_symbolic_bridge",
                        confidence=1.0,
                    )
                    return {
                        "approved": True,
                        "status": "NEURO_SYMBOLIC_CERTIFIED",
                        "rounds_taken": round_idx,
                        "rejected_count": len(rejected_history),
                        "rejected_history": rejected_history,
                        "verification": ver,
                        "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
                    }
                rej_record = {"round": round_idx, "gate": ver.get("gate"), "reason": ver.get("reason"), "counterexample": ver.get("counterexample")}
                rejected_history.append(rej_record)
                feedback.append(rej_record)
                self.bus.publish(
                    topic="neuro_symbolic.gate.rejected",
                    payload={"task": task_prompt, "round": round_idx, "gate": ver.get("gate")},
                    organ_id="neuro_symbolic_bridge",
                    confidence=0.0,
                )

        return {
            "approved": False,
            "status": "PROPOSAL_REJECTED_BY_FORMAL_GATE",
            "rounds_taken": max_rounds,
            "rejected_count": len(rejected_history),
            "rejected_history": rejected_history,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }


def _ast_eval_z3_proxy(node: Any, env: Dict[str, Any]) -> Any:
    from ..logic_symbolic.cegis_code_synthesizer import _ast_to_z3_bv64
    return _ast_to_z3_bv64(node, env, [])
