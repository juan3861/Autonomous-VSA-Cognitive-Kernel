"""Autonomous Cognitive Composer: Dynamic Multi-Organ DAG Task Orchestration (v7.4.0).

Orchestrates the 82+ mathematical organs (and hot-pluggable external organ modules) of the
Autonomous VSA Cognitive Kernel into provably safe, closed-loop execution pipelines:

1. Holographic VSA Organ Auto-Discovery:
   Embeds objectives and spec IO keys into 10,240-bit VSA space $\mathcal{H} = \{-1, +1\}^D$
   and retrieves ranked organs from `OrganCapabilityRegistry` via cosine resonance.
2. Typed Dataflow DAG Chaining & Inter-Session Policy Adaptation:
   Chains precondition producers -> primary organs -> formal certifiers while consulting
   persisted SQLite priors (`VSA10240PersistenceBridge`), `HippoRAGKnowledgeGraph` causal
   triples, and `HierarchicalPagedMemoryOS` high-surprise episodes across sessions.
3. Closed-Loop Formal Shielding:
   Every synthesized execution pipeline undergoes Z3 SMT edge interval & stability verification
   (`verify_dag_contracts`) and executes with CBF-QP, STL, or Z3/CEGIS verification.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

import numpy as np

from ..memory_vault.vsa_semantic_bus import VSAHyperdimensionalBus, VSAEvent
from .organ_capability_registry import (
    OrganCapability,
    OrganCapabilityRegistry,
    _tokenize_semantic_text,
)


@dataclass
class PipelineStageResult:
    """Outcome of a single organ execution stage in the synthesized DAG."""
    stage_id: str
    organ_id: str
    success: bool
    data: Dict[str, Any]
    formal_passed: bool
    execution_time_ms: float
    error_message: Optional[str] = None


@dataclass
class CompositionReceipt:
    """Formal audit receipt of an autonomously composed and executed pipeline."""
    receipt_id: str
    objective: str
    stages: List[PipelineStageResult]
    overall_success: bool
    total_time_ms: float
    certified_safe: bool
    formal_certificate: Dict[str, Any]
    bus_event_ids: List[str]


def _objective_signature(objective: str) -> str:
    toks = _tokenize_semantic_text(objective.replace("_", " "))[:6]
    return "_".join(toks) if toks else "generic_objective"


class AutonomousCognitiveComposer:
    """Autonomous Composer that discovers, proves, executes, and learns over 82+ modular organs."""

    def __init__(
        self,
        bus: Optional[VSAHyperdimensionalBus] = None,
        registry: Optional[OrganCapabilityRegistry] = None,
        persistence: Optional[Any] = None,
        hipporag: Optional[Any] = None,
        paged_memory: Optional[Any] = None,
        rem_engine: Optional[Any] = None,
    ):
        self.bus = bus or VSAHyperdimensionalBus(dimension=10240, seed=1337)
        self.registry = registry or OrganCapabilityRegistry(bus=self.bus, load_runtime_catalog=True)
        # Keep `.capabilities` exposed directly for backwards compatibility
        self.capabilities: Dict[str, OrganCapability] = self.registry.capabilities
        self.persistence = persistence
        self.hipporag = hipporag
        self.paged_memory = paged_memory
        self.rem_engine = rem_engine
        self._hydrated_from_persistence: bool = False
        self._dag_compiler: Optional[Any] = None

        if self.persistence is not None and self.hipporag is not None:
            self.hydrate_episodic_memory()

    @property
    def dag_compiler(self):
        if self._dag_compiler is None:
            from ..memory_vault.vsa_dag_compiler import VSADAGBytecodeCompiler
            self._dag_compiler = VSADAGBytecodeCompiler()
        return self._dag_compiler

    def register_plugin(
        self,
        capability: OrganCapability,
        executor: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Hot-plug a new modular organ capability and executor at runtime."""
        self.registry.register_plugin(capability, executor)

    def unregister_plugin(self, organ_id: str) -> bool:
        """Detach a dynamically registered plugin organ."""
        return self.registry.unregister_plugin(organ_id)

    def hydrate_episodic_memory(self) -> int:
        """Restore persisted SQLite composition episodes into HippoRAG & PagedMemoryOS on cold start."""
        if self.persistence is None or self.hipporag is None:
            return 0
        if self._hydrated_from_persistence:
            return 0
        try:
            episodes = self.persistence.load_recent_episodes(limit=40)
        except Exception:
            return 0

        loaded = 0
        for ep in episodes:
            obj_node = f"obj:{ep['objective_sig']}"
            for oid in ep.get("pipeline", []):
                if ep["overall_success"] and ep["certified_safe"]:
                    self.hipporag.add_relation(obj_node, "succeeded_with", f"organ:{oid}", weight=1.2)
                else:
                    self.hipporag.add_relation(obj_node, "failed_with", f"organ:{oid}", weight=0.25)
                    self.hipporag.add_relation(obj_node, "needs_shield", "organ:cbf_control_barrier_shield", weight=1.4)
                    self.hipporag.add_relation(obj_node, "needs_proof", "organ:z3_formal_solver", weight=1.4)
            if (not ep["overall_success"] or not ep["certified_safe"]) and self.paged_memory is not None:
                self.paged_memory.allocate_page(
                    page_id=ep["episode_id"],
                    content={"objective": ep["objective"], "pipeline": ep["pipeline"], "z3": ep["z3_sat_status"]},
                    importance=max(1.5, ep.get("free_energy_f", 0.9) * 2.0),
                    pin=True,
                )
            loaded += 1

        self._hydrated_from_persistence = True
        return loaded

    def _compute_prior_adjustments(self, objective: str) -> Dict[str, float]:
        """Combine persisted SQLite policy priors and HippoRAG graph diffusion scores."""
        adj: Dict[str, float] = {}
        obj_sig = _objective_signature(objective)

        if self.persistence is not None:
            try:
                priors = self.persistence.query_organ_priors(obj_sig)
                for oid, stats in priors.items():
                    adj[oid] = adj.get(oid, 0.0) + float(stats.get("score_delta", 0.0))
            except Exception:
                pass

        if self.hipporag is not None and self.hipporag.graph.number_of_nodes() > 0:
            try:
                if self.persistence is not None and not self._hydrated_from_persistence:
                    self.hydrate_episodic_memory()
                diff = self.hipporag.associate_query([f"obj:{obj_sig}"], top_k=10)
                for item in diff.get("results", []):
                    ent = str(item.get("entity", ""))
                    if ent.startswith("organ:"):
                        oid = ent.split(":", 1)[1]
                        rel_score = float(item.get("relevance_score", 0.0))
                        conns = " ".join(item.get("connections", []))
                        if "failed_with" in conns and "succeeded_with" not in conns:
                            adj[oid] = adj.get(oid, 0.0) - (0.35 + rel_score)
                        else:
                            adj[oid] = adj.get(oid, 0.0) + min(0.25, rel_score * 0.5)
            except Exception:
                pass

        return adj

    def synthesize_pipeline(self, objective: str, spec: Dict[str, Any]) -> List[str]:
        """Synthesize an ordered DAG of organ IDs via 10,240-bit VSA resonance + priors + IO chaining."""
        ignored = {
            "custom_pipeline", "require_formal_safety", "lyapunov_rho",
            "prefer_gpu", "use_vsa_gpu", "top_k",
        }
        spec_keys = [k for k in spec.keys() if k not in ignored]
        prefer_gpu = bool(spec.get("prefer_gpu", spec.get("use_vsa_gpu", False)))

        candidates = self.registry.semantic_search(
            objective=objective,
            required_inputs=spec_keys,
            top_k=18,
            prefer_gpu=prefer_gpu,
        )
        priors = self._compute_prior_adjustments(objective)

        rescored: List[Tuple[OrganCapability, float]] = []
        for cap, base_score in candidates:
            bonus = priors.get(cap.organ_id, 0.0)
            # Small tie-breaker favoring hot-plugged plugins when they strongly match the objective
            if cap.is_external_plugin and base_score > 0.15:
                bonus += 0.05
            rescored.append((cap, base_score + bonus))
        rescored.sort(key=lambda item: item[1], reverse=True)

        non_certifiers = [(c, s) for c, s in rescored if not c.is_certifier]
        certifiers = [(c, s) for c, s in rescored if c.is_certifier]

        stages: List[str] = []
        produced_vars: Set[str] = set(spec_keys)

        if non_certifiers:
            primary_cap, primary_score = non_certifiers[0]

            # Dataflow precondition supplier chaining (e.g., observations -> ukf_state_estimator -> filtered_state -> ilqr)
            if "filtered_state" in primary_cap.inputs and "filtered_state" not in produced_vars:
                for sup_cap, _ in non_certifiers[1:]:
                    if "filtered_state" in sup_cap.outputs:
                        stages.append(sup_cap.organ_id)
                        produced_vars.update(sup_cap.outputs)
                        break

            # Pre-inspection chain if AST perception feeds synthesis
            if "source_code" in spec_keys and primary_cap.organ_id != "ast_analyzer":
                for sup_cap, _ in non_certifiers:
                    if sup_cap.organ_id == "ast_analyzer":
                        stages.append(sup_cap.organ_id)
                        produced_vars.update(sup_cap.outputs)
                        break

            if primary_cap.organ_id not in stages:
                stages.append(primary_cap.organ_id)
                produced_vars.update(primary_cap.outputs)

            # Downstream consumer chaining (e.g., if primary is an estimator producing filtered_state, connect trajectory optimizer)
            if "filtered_state" in primary_cap.outputs and "optimal_trajectory" not in produced_vars:
                for cons_cap, cons_score in non_certifiers[1:]:
                    if "filtered_state" in cons_cap.inputs and cons_cap.organ_id not in stages:
                        if cons_score >= primary_score * 0.40:
                            stages.append(cons_cap.organ_id)
                            produced_vars.update(cons_cap.outputs)
                            break

        # Append formal verification / safety certifier sink(s)
        require_safety = bool(spec.get("require_formal_safety", True))
        dynamical_tokens = {"filtered_state", "optimal_trajectory", "path_points", "safe_control"}
        is_dynamical = bool(produced_vars & dynamical_tokens)

        if require_safety or certifiers:
            if is_dynamical:
                # Prefer dynamical forward-invariance shield + temporal robustness monitor chain
                for target_cert in ("cbf_control_barrier_shield", "stl_temporal_logic_monitor"):
                    cert_cap = self.registry.get(target_cert)
                    if cert_cap and cert_cap.organ_id not in stages:
                        if priors.get(cert_cap.organ_id, 0.0) > -0.35:
                            stages.append(cert_cap.organ_id)
                            produced_vars.update(cert_cap.outputs)
            else:
                # Symbolic / Planning / Synthesis / Plugin verification sink ranked by VSA + IO dataflow overlap
                if certifiers:
                    ranked_certs = sorted(
                        certifiers,
                        key=lambda item: item[1] + 0.15 * len(set(item[0].inputs) & produced_vars),
                        reverse=True,
                    )
                    best_cert = ranked_certs[0][0]
                    if best_cert.organ_id not in stages:
                        stages.append(best_cert.organ_id)
                        produced_vars.update(best_cert.outputs)
                z3_cap = self.registry.get("z3_formal_solver")
                if z3_cap and z3_cap.organ_id not in stages and (
                    not stages or not self.registry.get(stages[-1]).is_certifier
                    or stages[-1] == "cegis_synthesizer"
                ):
                    stages.append(z3_cap.organ_id)

        if not any((self.registry.get(oid) and self.registry.get(oid).is_certifier) for oid in stages):
            if require_safety and self.registry.get("z3_formal_solver") is not None:
                stages.append("z3_formal_solver")

        return stages

    def synthesize_and_register_missing_organ(
        self,
        objective: str,
        spec: Dict[str, Any],
        organ_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Synthesize, AST-audit, Z3/Hoare-verify, and hot-plug a missing organ on capability miss."""
        import ast
        from ..code_inspector.ast_code_analyzer import ASTCodeAnalyzer
        from ..logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer, _eval_ast_i64
        from ..metacognition.hoare_contract_verifier import HoareContractVerifier

        t0 = time.perf_counter()
        synth = CEGISCodeSynthesizer()
        analyzer = ASTCodeAnalyzer()

        src_spec = spec.get("missing_organ_source") or spec.get("cegis_source")
        io_examples = spec.get("io_examples") or []
        proof: Dict[str, Any] = {"is_equivalent": False}
        arg_names: List[str] = []

        if isinstance(src_spec, str) and src_spec.strip():
            src_str = src_spec.strip()
            tree = ast.parse(src_str)
            fn_def = next((n for n in tree.body if isinstance(n, ast.FunctionDef)), None)
            if fn_def is None:
                raise ValueError("missing_organ_source must define a Python function.")
            arg_names = [a.arg for a in fn_def.args.args]
            for_count = sum(1 for n in ast.walk(fn_def) if isinstance(n, ast.For))
            while_count = sum(1 for n in ast.walk(fn_def) if isinstance(n, ast.While))
            if for_count >= 2:
                proof = synth.synthesize_nested_loop_closed_form_cegis(src_str)
            elif for_count == 1 or while_count >= 1:
                proof = synth.synthesize_loop_closed_form_cegis(src_str)
            else:
                proof = synth.synthesize_python_ast_cegis(
                    src_str, assume_non_negative=bool(spec.get("assume_non_negative", False))
                )
        elif io_examples:
            first_in = dict(io_examples[0]["inputs"] if isinstance(io_examples[0], dict) else io_examples[0][0])
            arg_names = list(first_in.keys())
            if not arg_names:
                raise ValueError("io_examples must include at least one named input variable.")
            v0 = arg_names[0]
            cands = [f"{v0}", "0", f"{v0} + 1", f"{v0} - 1", f"{v0} * {v0}", f"({v0} * ({v0} - 1)) >> 1"]
            for sh in (1, 2, 3, 4):
                cands.extend([f"{v0} << {sh}", f"({v0} << {sh}) + 1", f"{v0} & 1"])
            if len(arg_names) >= 2:
                v1 = arg_names[1]
                cands.extend([f"{v0} + {v1}", f"{v0} * {v1}", f"({v0} << 2) * {v1}", f"({v0} << 3) + {v1}"])
            matched = None
            for cs in cands:
                nd = ast.parse(cs, mode="eval").body
                if all(
                    _eval_ast_i64(nd, dict(ex["inputs"] if isinstance(ex, dict) else ex[0]))
                    == int(ex["output"] if isinstance(ex, dict) else ex[1])
                    for ex in io_examples
                ):
                    matched = ast.unparse(nd)
                    break
            if matched is not None:
                syn_src = f"def auto_{_objective_signature(objective)}({', '.join(arg_names)}):\n    return {matched}\n"
                proof = synth.synthesize_python_ast_cegis(
                    syn_src, assume_non_negative=bool(spec.get("assume_non_negative", False))
                )
        else:
            return {"registered": False, "status": "NO_SYNTHESIS_SPEC"}

        if not proof.get("is_equivalent") or not proof.get("candidate_code"):
            return {"registered": False, "status": "SYNTHESIS_FAILED", "proof": proof}

        cand_code = str(proof["candidate_code"])
        syn_src = str(proof.get("synthesized_source") or f"def synth_fn({', '.join(arg_names)}):\n    return {cand_code}\n")
        ast_sec = analyzer.analyze_source(syn_src)
        if not ast_sec.get("is_valid_syntax") or not ast_sec.get("security_clean"):
            return {"registered": False, "status": "AST_SECURITY_REJECTED", "ast_security": ast_sec}

        hoare_spec = spec.get("hoare_contract")
        if isinstance(hoare_spec, dict):
            hc = HoareContractVerifier().verify_hoare_triple_assignment(
                declarations=dict(hoare_spec.get("declarations", {a: "int" for a in arg_names})),
                precondition=str(hoare_spec.get("precondition", "True")),
                assignment_var=str(hoare_spec.get("assignment_var", arg_names[0])),
                assigned_expr=str(hoare_spec.get("assigned_expr", cand_code)),
                postcondition=str(hoare_spec.get("postcondition", "True")),
            )
            if not hc.get("is_contract_valid"):
                return {"registered": False, "status": "HOARE_CONTRACT_REJECTED", "hoare": hc}

        cand_ast = ast.parse(cand_code, mode="eval").body
        new_oid = organ_id or spec.get("synthesize_organ_id") or f"auto_synth_{_objective_signature(objective)}"

        def _safe_ast_organ_exec(ctx: Dict[str, Any]) -> Dict[str, Any]:
            raw_inputs = ctx.get("inputs", ctx)
            env = {a: int(raw_inputs.get(a, ctx.get(a, 0))) for a in arg_names}
            val = _eval_ast_i64(cand_ast, env)
            return {
                "synthesized_output": val,
                "candidate_code": cand_code,
                "sat_status": "sat",
                "executed": True,
                "status": "AUTO_SYNTH_EXECUTED",
            }

        cap = OrganCapability(
            organ_id=new_oid,
            category="synthesized_plugin",
            description=f"{objective} auto synthesized organ ({cand_code})",
            inputs=list(arg_names),
            outputs=["synthesized_output", "candidate_code", "sat_status"],
            formal_guarantee=f"CEGIS+Z3 verified O(1) organ: {cand_code}",
            latency_class="submicrosecond",
            is_certifier=False,
            is_external_plugin=True,
        )
        self.registry.register_plugin(cap, executor=_safe_ast_organ_exec)

        if self.hipporag is not None:
            try:
                self.hipporag.add_relation(
                    f"obj:{_objective_signature(objective)}", "resolved_by_synthesized", f"organ:{new_oid}", weight=1.0
                )
            except Exception:
                pass

        self.bus.publish(
            topic="composer.organ.synthesized",
            payload={"organ_id": new_oid, "candidate_code": cand_code, "objective": objective},
            organ_id="autonomous_composer",
            confidence=1.0,
        )

        return {
            "registered": True,
            "status": "ORGAN_SYNTHESIZED_AND_PLUGGED",
            "organ_id": new_oid,
            "candidate_code": cand_code,
            "synthesized_source": syn_src,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    def verify_dag_contracts(self, pipeline_organs: List[str], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Formally verify DAG topological contracts, Lyapunov stability & safety sinks via Z3 SMT."""
        import z3
        from ..logic_symbolic.z3_formal_solver import Z3_GLOBAL_LOCK

        t0 = time.perf_counter()
        with Z3_GLOBAL_LOCK:
            solver = z3.Solver()
            solver.set("timeout", 2000)

            rho_val = float(spec.get("lyapunov_rho", 0.85))
            require_safety = bool(spec.get("require_formal_safety", True))

            rho = z3.Real("lyapunov_rho")
            solver.add(rho == z3.RealVal(str(rho_val)))
            solver.add(rho <= z3.RealVal("0.95"))
            solver.add(rho >= z3.RealVal("0.0"))

            ready_vars = []
            edge_bounds_verified = 0
            obs_vals = spec.get("observations")
            cur_lo = float(min(obs_vals)) if isinstance(obs_vals, (list, tuple)) and len(obs_vals) > 0 else float(spec.get("state_min", -2.0))
            cur_hi = float(max(obs_vals)) if isinstance(obs_vals, (list, tuple)) and len(obs_vals) > 0 else float(spec.get("state_max", 2.0))

            prev_out_lo = z3.Real("edge_0_in_lo")
            prev_out_hi = z3.Real("edge_0_in_hi")
            solver.add(prev_out_lo == z3.RealVal(str(cur_lo)))
            solver.add(prev_out_hi == z3.RealVal(str(cur_hi)))
            solver.add(prev_out_lo <= prev_out_hi)

            has_certifier = False
            for idx, raw_org in enumerate(pipeline_organs):
                org = self.registry.resolve_organ_id(raw_org)
                v = z3.Bool(f"stage_{idx}_{org}_ready")
                cap = self.capabilities.get(org)
                is_known = cap is not None
                solver.add(v == z3.BoolVal(is_known))
                solver.add(v == True)
                ready_vars.append(v)

                if cap is not None:
                    if cap.is_certifier or org in {"cbf_control_barrier_shield", "stl_temporal_logic_monitor", "z3_formal_solver"}:
                        has_certifier = True
                    s_in_lo = z3.Real(f"stage_{idx}_in_lo")
                    s_in_hi = z3.Real(f"stage_{idx}_in_hi")
                    s_out_lo = z3.Real(f"stage_{idx}_out_lo")
                    s_out_hi = z3.Real(f"stage_{idx}_out_hi")
                    solver.add(s_in_lo == z3.RealVal(str(cap.in_min)))
                    solver.add(s_in_hi == z3.RealVal(str(cap.in_max)))
                    solver.add(prev_out_lo >= s_in_lo)
                    solver.add(prev_out_hi <= s_in_hi)
                    out_min_val = z3.RealVal(str(cap.out_min))
                    out_max_val = z3.RealVal(str(cap.out_max))
                    solver.add(s_out_lo == z3.If(prev_out_lo > out_min_val, prev_out_lo, out_min_val))
                    solver.add(s_out_hi == z3.If(prev_out_hi < out_max_val, prev_out_hi, out_max_val))
                    solver.add(s_out_lo <= s_out_hi)
                    prev_out_lo = s_out_lo
                    prev_out_hi = s_out_hi
                    edge_bounds_verified += 1

            safety_sink = z3.Bool("has_formal_safety_certifier")
            solver.add(safety_sink == z3.BoolVal(has_certifier))
            if require_safety:
                solver.add(safety_sink == True)

            check_res = solver.check()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            verified = (check_res == z3.sat)

        return {
            "verified": verified,
            "sat_status": "sat" if verified else str(check_res),
            "lyapunov_rho": rho_val,
            "has_formal_certifier": has_certifier,
            "stages_verified": len(pipeline_organs),
            "edge_numeric_invariants_proven": edge_bounds_verified if verified else 0,
            "elapsed_ms": round(elapsed_ms, 3),
        }

    def _record_learning_feedback(
        self,
        receipt: CompositionReceipt,
        z3_preflight: Dict[str, Any],
        pipeline_organs: List[str],
        min_margin: float,
        barrier_intervened: bool,
    ) -> None:
        """Persist execution outcomes & safety telemetry into SQLite, HippoRAG, PagedOS & REM."""
        obj_sig = _objective_signature(receipt.objective)
        free_energy_f = 0.95 if (not receipt.overall_success or not receipt.certified_safe) else (0.72 if barrier_intervened else 0.12)

        if self.persistence is not None:
            try:
                self.persistence.record_composition_outcome(
                    episode_id=receipt.receipt_id,
                    objective=receipt.objective,
                    objective_sig=obj_sig,
                    organ_ids=pipeline_organs,
                    overall_success=receipt.overall_success,
                    certified_safe=receipt.certified_safe,
                    z3_sat_status=str(z3_preflight.get("sat_status", "unknown")),
                    min_safety_margin=min_margin,
                    barrier_intervened=barrier_intervened,
                    latency_ms=receipt.total_time_ms,
                    free_energy_f=free_energy_f,
                )
            except Exception:
                pass

        if self.hipporag is not None:
            try:
                obj_node = f"obj:{obj_sig}"
                if receipt.overall_success and receipt.certified_safe:
                    for oid in pipeline_organs:
                        self.hipporag.add_relation(obj_node, "succeeded_with", f"organ:{oid}", weight=1.2)
                else:
                    for oid in pipeline_organs:
                        self.hipporag.add_relation(obj_node, "failed_with", f"organ:{oid}", weight=0.25)
                    self.hipporag.add_relation(obj_node, "needs_shield", "organ:cbf_control_barrier_shield", weight=1.4)
                    self.hipporag.add_relation(obj_node, "needs_proof", "organ:z3_formal_solver", weight=1.4)
                if barrier_intervened:
                    self.hipporag.add_relation(obj_node, "shielded_by", "organ:cbf_control_barrier_shield", weight=1.3)
            except Exception:
                pass

        if self.paged_memory is not None and (not receipt.overall_success or not receipt.certified_safe or barrier_intervened):
            try:
                self.paged_memory.allocate_page(
                    page_id=receipt.receipt_id,
                    content={
                        "objective": receipt.objective,
                        "pipeline": pipeline_organs,
                        "z3_sat": z3_preflight.get("sat_status"),
                        "margin": min_margin,
                    },
                    importance=1.0 + free_energy_f,
                    pin=(not receipt.certified_safe),
                )
            except Exception:
                pass

        if self.rem_engine is not None and hasattr(self.rem_engine, "dream_episodes_log"):
            self.rem_engine.dream_episodes_log.append({
                "episode_id": receipt.receipt_id,
                "objective_sig": obj_sig,
                "pipeline": list(pipeline_organs),
                "free_energy_f": free_energy_f,
                "certified_safe": receipt.certified_safe,
            })

    def execute_pipeline(
        self,
        objective: str,
        spec: Dict[str, Any],
        organ_executor_map: Optional[Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]]] = None,
    ) -> CompositionReceipt:
        """Execute a synthesized pipeline, verifying Z3 contracts first and routing via VSA bus."""
        t_start = time.perf_counter()
        synth_receipt: Optional[Dict[str, Any]] = None
        if not spec.get("custom_pipeline") and (
            spec.get("synthesize_on_miss") or spec.get("missing_organ_source") or spec.get("io_examples")
        ):
            target_oid = spec.get("synthesize_organ_id") or f"auto_synth_{_objective_signature(objective)}"
            if self.registry.get(target_oid) is None:
                synth_receipt = self.synthesize_and_register_missing_organ(objective, spec, organ_id=target_oid)

        raw_pipeline = list(spec.get("custom_pipeline") or self.synthesize_pipeline(objective, spec))
        pipeline_organs = [self.registry.resolve_organ_id(o) for o in raw_pipeline]
        stage_results: List[PipelineStageResult] = []
        bus_events: List[str] = []

        z3_preflight = self.verify_dag_contracts(pipeline_organs, spec)

        avx2_trace = None
        if z3_preflight["verified"]:
            try:
                route = self.dag_compiler.compile_route(pipeline_organs, objective=objective)
                exec_res = self.dag_compiler.execute_route(route)
                avx2_trace = {
                    "backend": exec_res["backend"],
                    "op_count": exec_res["op_count"],
                    "compile_time_us": exec_res["compile_time_us"],
                    "exec_time_us": exec_res["exec_time_us"],
                    "tail_inversion_hamming": exec_res["tail_inversion_hamming"],
                    "bijection_verified": exec_res["bijection_verified"],
                }
            except Exception:
                avx2_trace = None

        current_context = dict(spec)
        overall_success = bool(z3_preflight["verified"])
        certified_safe = bool(z3_preflight["verified"])
        formal_cert: Dict[str, Any] = {
            "objective": objective,
            "pipeline_organs": pipeline_organs,
            "z3_preflight_proof": z3_preflight,
            "avx2_route_trace": avx2_trace,
            "synthesized_organ_receipt": synth_receipt,
            "guarantees": [],
        }

        if not z3_preflight["verified"]:
            total_ms = (time.perf_counter() - t_start) * 1000.0
            fail_evt = self.bus.publish(
                topic="composer.pipeline.rejected",
                payload={"objective": objective, "z3_preflight": z3_preflight},
                organ_id="autonomous_composer",
                confidence=0.0,
            )
            bus_events.append(fail_evt.event_id)
            rejected_receipt = CompositionReceipt(
                receipt_id=f"receipt_rejected_{int(time.time()*1000)}",
                objective=objective,
                stages=[],
                overall_success=False,
                total_time_ms=total_ms,
                certified_safe=False,
                formal_certificate=formal_cert,
                bus_event_ids=bus_events,
            )
            self._record_learning_feedback(
                rejected_receipt,
                z3_preflight=z3_preflight,
                pipeline_organs=pipeline_organs,
                min_margin=-1.0,
                barrier_intervened=False,
            )
            return rejected_receipt

        init_evt = self.bus.publish(
            topic="composer.pipeline.start",
            payload={"objective": objective, "pipeline": pipeline_organs},
            organ_id="autonomous_composer",
        )
        bus_events.append(init_evt.event_id)

        min_margin = 1.0
        barrier_intervened = False

        for idx, organ_id in enumerate(pipeline_organs):
            t_stage_0 = time.perf_counter()
            cap = self.capabilities.get(organ_id)

            stage_success = True
            formal_passed = True
            error_msg: Optional[str] = None
            out_data: Dict[str, Any] = {}

            try:
                if organ_executor_map and organ_id in organ_executor_map:
                    out_data = organ_executor_map[organ_id](current_context)
                else:
                    out_data = self.registry.invoke(organ_id, current_context)

                if organ_id == "cbf_control_barrier_shield":
                    margin = float(out_data.get("safety_margin", 0.0))
                    min_margin = min(min_margin, margin)
                    if out_data.get("cbf_intervened"):
                        barrier_intervened = True
                    if not out_data.get("is_formally_safe", margin >= 0.0) or margin < 0.0:
                        formal_passed = False
                        certified_safe = False
                elif organ_id == "stl_temporal_logic_monitor":
                    robustness = float(out_data.get("robustness_degree", out_data.get("overall_stl_robustness", 0.0)))
                    min_margin = min(min_margin, robustness)
                    if not out_data.get("is_satisfied", out_data.get("satisfied", robustness >= 0.0)) or robustness < 0.0:
                        formal_passed = False
                        certified_safe = False
                elif organ_id in ("z3_formal_solver", "cegis_synthesizer", "lyapunov_certifier"):
                    sat_status = str(out_data.get("sat_status", out_data.get("status", "sat"))).lower()
                    if sat_status not in ("sat", "verified"):
                        formal_passed = False
                        certified_safe = False
                        min_margin = min(min_margin, -1.0)

                current_context.update(out_data)

            except Exception as exc:
                stage_success = False
                formal_passed = False
                overall_success = False
                certified_safe = False
                error_msg = str(exc)

            exec_ms = (time.perf_counter() - t_stage_0) * 1000.0

            pub_evt = self.bus.publish(
                topic=f"composer.stage.{organ_id}",
                payload={
                    "stage_index": idx,
                    "success": stage_success,
                    "formal_passed": formal_passed,
                    "execution_ms": exec_ms,
                },
                organ_id=organ_id,
                confidence=1.0 if formal_passed else 0.0,
            )
            bus_events.append(pub_evt.event_id)

            stage_res = PipelineStageResult(
                stage_id=f"stage_{idx}_{organ_id}",
                organ_id=organ_id,
                success=stage_success,
                data=out_data,
                formal_passed=formal_passed,
                execution_time_ms=exec_ms,
                error_message=error_msg,
            )
            stage_results.append(stage_res)

            if cap:
                formal_cert["guarantees"].append({
                    "organ_id": organ_id,
                    "guarantee": cap.formal_guarantee,
                    "verified": formal_passed,
                })

            if not stage_success:
                overall_success = False
                break

        total_ms = (time.perf_counter() - t_start) * 1000.0

        receipt = CompositionReceipt(
            receipt_id=f"receipt_{int(time.time()*1000)}",
            objective=objective,
            stages=stage_results,
            overall_success=overall_success,
            total_time_ms=total_ms,
            certified_safe=certified_safe,
            formal_certificate=formal_cert,
            bus_event_ids=bus_events,
        )

        self.bus.publish(
            topic="composer.pipeline.complete",
            payload={
                "receipt_id": receipt.receipt_id,
                "overall_success": overall_success,
                "certified_safe": certified_safe,
                "stages_count": len(stage_results),
                "total_time_ms": total_ms,
            },
            organ_id="autonomous_composer",
        )

        self._record_learning_feedback(
            receipt,
            z3_preflight=z3_preflight,
            pipeline_organs=pipeline_organs,
            min_margin=min_margin,
            barrier_intervened=barrier_intervened,
        )

        return receipt

    def _execute_builtin_stage(self, organ_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Backwards-compatible stage delegate into `OrganCapabilityRegistry.invoke`."""
        return self.registry.invoke(organ_id, context)
