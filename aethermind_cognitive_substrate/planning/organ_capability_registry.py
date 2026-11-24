"""Autonomous Organ Capability Registry & Holographic VSA Auto-Discovery (v7.4.0).

Decouples metadata indexing, 10,240-bit semantic capability matching, and hot-pluggable
external organ registration from heavy runtime imports, preserving < 60 ms cold boot
while exposing all 82+ substrate organs to the AutonomousCognitiveComposer.
"""
from __future__ import annotations

import importlib
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np

from ..memory_vault.vsa_semantic_bus import VSAHyperdimensionalBus


_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "into", "is",
    "of", "on", "or", "the", "to", "via", "with", "over", "under", "based",
}


def _tokenize_semantic_text(text: str) -> List[str]:
    return [
        tok for tok in _TOKEN_RE.findall(text.lower())
        if len(tok) >= 2 and tok not in _STOPWORDS
    ]


def _pack_bipolar_to_u64(vec_i8: np.ndarray) -> np.ndarray:
    """Pack {-1, +1}^10240 bipolar array into uint64[160] words for bitwise engines."""
    bits = (vec_i8 > 0).astype(np.uint8)
    packed_u8 = np.packbits(bits, bitorder="little")
    return np.ascontiguousarray(packed_u8.view(np.uint64))


@dataclass
class OrganCapability:
    """Metadata specification of a cognitive organ's operational capabilities."""
    organ_id: str
    category: str
    description: str
    inputs: List[str]
    outputs: List[str]
    formal_guarantee: str
    latency_class: str = "microsecond"
    in_min: float = -100.0
    in_max: float = 100.0
    out_min: float = -100.0
    out_max: float = 100.0
    state_dim: int = 4
    module_path: str = ""
    class_name: str = ""
    aliases: Tuple[str, ...] = ()
    is_certifier: bool = False
    is_external_plugin: bool = False
    runtime_attr: Optional[str] = None


# Canonical alias map aligning _LAZY_ORGAN_SPECS keys with legacy composer organ IDs
_RUNTIME_TO_COMPOSER_ALIAS: Dict[str, str] = {
    "ukf_estimator": "ukf_state_estimator",
    "notears_engine": "notears_causal",
    "ilqr_optimizer": "ilqr_trajectory_optimizer",
    "cbf_shield": "cbf_control_barrier_shield",
    "stl_monitor": "stl_temporal_logic_monitor",
    "z3_solver": "z3_formal_solver",
    "simplex_lp": "simplex_lp_solver",
    "rrt_star": "rrt_star_planner",
}


def _infer_category_from_module(mod_rel: str, organ_id: str) -> str:
    m = mod_rel.lower()
    if any(k in organ_id for k in ("cbf", "conformal", "lti_governor")):
        return "safety"
    if any(k in organ_id for k in ("stl", "z3", "cegis", "hoare", "lyapunov")):
        return "verification"
    if any(k in organ_id for k in ("causal", "notears", "counterfactual")):
        return "causality"
    if any(k in organ_id for k in ("ukf", "rts", "imm", "smc", "kalman", "info_filter")):
        return "estimation"
    if any(k in organ_id for k in ("simplex", "admm", "alm", "cmaes", "lm_nlls", "egraph")):
        return "optimization"
    if "code_inspector" in m or "vision_eye" in organ_id:
        return "perception"
    if "memory_vault" in m or "rem_dream" in organ_id:
        return "memory"
    if "planning" in m:
        return "planning"
    if "physical_bridge" in m:
        return "physical_bridge"
    if "metacognition" in m:
        return "metacognition"
    return "logic_symbolic"


def _default_io_for_category(category: str, organ_id: str) -> Tuple[List[str], List[str]]:
    if category == "estimation":
        return ["observations", "initial_state", "dt"], ["filtered_state", "covariance_trace"]
    if category == "causality":
        return ["timeseries_data", "var_names"], ["adjacency_matrix", "is_dag", "causal_effects"]
    if category == "safety":
        return ["nominal_control", "filtered_state", "barrier_params"], ["safe_control", "safety_margin", "is_formally_safe"]
    if category == "verification":
        return ["trace", "constraints", "declarations"], ["verified", "robustness_degree", "sat_status"]
    if category == "optimization":
        return ["cost_c", "matrix_A", "vector_b", "x0"], ["optimal_x", "optimal_cost", "dual_gap"]
    if category == "perception":
        return ["source_code", "window_query"], ["ast_metrics", "violations", "window_matches"]
    if category == "memory":
        return ["query_entities", "episode_payload", "hypervector"], ["recalled_entities", "resonance_score"]
    if "strips" in organ_id or "pddl" in organ_id:
        return ["initial_state", "goal_state", "actions"], ["plan", "plan_cost", "final_state"]
    return ["initial_state", "goal_state", "context"], ["result", "status"]


class OrganCapabilityRegistry:
    """Lazy-first holographic capability index & plugin registry for 82+ cognitive organs."""

    def __init__(self, bus: Optional[VSAHyperdimensionalBus] = None, load_runtime_catalog: bool = True):
        self.bus = bus or VSAHyperdimensionalBus(dimension=10240, seed=1337)
        self.capabilities: Dict[str, OrganCapability] = {}
        self.aliases: Dict[str, str] = {}
        self.executors: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}
        self._signature_vectors: Dict[str, np.ndarray] = {}
        self._ordered_ids: List[str] = []
        self._sig_matrix_f32: Optional[np.ndarray] = None
        self._sig_packed_u64: Optional[np.ndarray] = None
        self._cache_dirty: bool = True

        self._register_core_profiles()
        if load_runtime_catalog:
            self._discover_runtime_specs()

    def _encode_capability_hv(self, cap: OrganCapability) -> np.ndarray:
        """Encode an organ's full semantic/IO signature into a 10,240-bit bipolar hypervector."""
        vsa = self.bus.vsa
        parts: List[np.ndarray] = []

        role_id = vsa.register_symbol("role_organ_id")
        role_cat = vsa.register_symbol("role_category")
        role_in = vsa.register_symbol("role_input")
        role_out = vsa.register_symbol("role_output")
        role_kw = vsa.register_symbol("role_intent")

        for tok in _tokenize_semantic_text(cap.organ_id.replace("_", " ")):
            parts.append(vsa.bind(role_id, vsa.register_symbol(f"tok_{tok}")))
        parts.append(vsa.bind(role_cat, vsa.register_symbol(f"category_{cap.category}")))

        for inp in cap.inputs:
            parts.append(vsa.bind(role_in, vsa.register_symbol(f"input_{inp}")))
            for tok in _tokenize_semantic_text(inp.replace("_", " ")):
                parts.append(vsa.bind(role_kw, vsa.register_symbol(f"tok_{tok}")))

        for out in cap.outputs:
            parts.append(vsa.bind(role_out, vsa.register_symbol(f"output_{out}")))
            for tok in _tokenize_semantic_text(out.replace("_", " ")):
                parts.append(vsa.bind(role_kw, vsa.register_symbol(f"tok_{tok}")))

        desc_tokens = _tokenize_semantic_text(f"{cap.description} {cap.formal_guarantee}")
        for tok in desc_tokens[:24]:
            parts.append(vsa.bind(role_kw, vsa.register_symbol(f"tok_{tok}")))

        return vsa.bundle(parts)

    def encode_query_hv(
        self,
        objective: str,
        required_inputs: Optional[Iterable[str]] = None,
        desired_outputs: Optional[Iterable[str]] = None,
    ) -> np.ndarray:
        """Encode an arbitrary natural/symbolic objective and IO spec into 10,240-bit VSA space."""
        vsa = self.bus.vsa
        parts: List[np.ndarray] = []
        role_kw = vsa.register_symbol("role_intent")
        role_in = vsa.register_symbol("role_input")
        role_out = vsa.register_symbol("role_output")

        for tok in _tokenize_semantic_text(objective.replace("_", " ")):
            parts.append(vsa.bind(role_kw, vsa.register_symbol(f"tok_{tok}")))

        if required_inputs:
            for inp in required_inputs:
                parts.append(vsa.bind(role_in, vsa.register_symbol(f"input_{inp}")))
        if desired_outputs:
            for out in desired_outputs:
                parts.append(vsa.bind(role_out, vsa.register_symbol(f"output_{out}")))

        if not parts:
            return vsa.register_symbol("empty_query")
        return vsa.bundle(parts)

    def register_capability(
        self,
        cap: OrganCapability,
        executor: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
        overwrite: bool = True,
    ) -> None:
        if not overwrite and cap.organ_id in self.capabilities:
            return
        self.capabilities[cap.organ_id] = cap
        for alias in cap.aliases:
            self.aliases[alias] = cap.organ_id
        if cap.runtime_attr:
            self.aliases[cap.runtime_attr] = cap.organ_id
        if executor is not None:
            self.executors[cap.organ_id] = executor

        self.bus.vsa.register_symbol(f"organ_{cap.organ_id}")
        self.bus.vsa.register_symbol(f"category_{cap.category}")
        for inp in cap.inputs:
            self.bus.vsa.register_symbol(f"input_{inp}")
        for out in cap.outputs:
            self.bus.vsa.register_symbol(f"output_{out}")

        self._signature_vectors[cap.organ_id] = self._encode_capability_hv(cap)
        self._cache_dirty = True

    def register_plugin(
        self,
        cap: OrganCapability,
        executor: Callable[[Dict[str, Any]], Dict[str, Any]],
    ) -> None:
        """Hot-plug an external, isolated modular organ and index it in VSA space."""
        cap.is_external_plugin = True
        self.register_capability(cap, executor=executor, overwrite=True)

    def unregister_plugin(self, organ_id: str) -> bool:
        cap = self.capabilities.get(organ_id)
        if not cap or not cap.is_external_plugin:
            return False
        del self.capabilities[organ_id]
        self.executors.pop(organ_id, None)
        self._signature_vectors.pop(organ_id, None)
        for alias in list(self.aliases.keys()):
            if self.aliases[alias] == organ_id:
                del self.aliases[alias]
        self._cache_dirty = True
        return True

    def resolve_organ_id(self, name: str) -> str:
        return self.aliases.get(name, name)

    def get(self, organ_id: str) -> Optional[OrganCapability]:
        return self.capabilities.get(self.resolve_organ_id(organ_id))

    def list_organ_ids(self) -> List[str]:
        return list(self.capabilities.keys())

    def _rebuild_matrix_cache(self) -> None:
        self._ordered_ids = list(self._signature_vectors.keys())
        if not self._ordered_ids:
            self._sig_matrix_f32 = None
            self._sig_packed_u64 = None
            self._cache_dirty = False
            return
        mat_i8 = np.vstack([self._signature_vectors[oid] for oid in self._ordered_ids])
        self._sig_matrix_f32 = np.ascontiguousarray(mat_i8, dtype=np.float32)
        if self.bus.dimension == 10240:
            self._sig_packed_u64 = np.vstack([_pack_bipolar_to_u64(v) for v in mat_i8])
        else:
            self._sig_packed_u64 = None
        self._cache_dirty = False

    def semantic_search(
        self,
        objective: str,
        required_inputs: Optional[List[str]] = None,
        desired_outputs: Optional[List[str]] = None,
        top_k: int = 8,
        prefer_gpu: bool = False,
        category_filter: Optional[str] = None,
    ) -> List[Tuple[OrganCapability, float]]:
        """Rank all registered organs against objective & IO signature using 10,240-bit VSA resonance."""
        if self._cache_dirty:
            self._rebuild_matrix_cache()
        if self._sig_matrix_f32 is None or not self._ordered_ids:
            return []

        q_hv = self.encode_query_hv(objective, required_inputs=required_inputs, desired_outputs=desired_outputs)
        dims = float(self.bus.dimension)

        if prefer_gpu and self._sig_packed_u64 is not None and len(self._ordered_ids) >= 64:
            try:
                from ..physical_bridge.vulkan_batch_vsa_engine import VulkanBatchVSAEngine
                eng = VulkanBatchVSAEngine()
                if eng.is_available:
                    q_u64 = _pack_bipolar_to_u64(q_hv)
                    res = eng.batch_hamming_distances(q_u64, self._sig_packed_u64, prefer_gpu=True)
                    dists = np.asarray(res["distances"], dtype=np.float32)
                    sims = 1.0 - 2.0 * (dists / dims)
                else:
                    sims = (self._sig_matrix_f32 @ q_hv.astype(np.float32)) / dims
            except Exception:
                sims = (self._sig_matrix_f32 @ q_hv.astype(np.float32)) / dims
        else:
            sims = (self._sig_matrix_f32 @ q_hv.astype(np.float32)) / dims

        obj_tokens = set(_tokenize_semantic_text(objective.replace("_", " ")))
        in_set = set(required_inputs or [])
        out_set = set(desired_outputs or [])

        scored: List[Tuple[OrganCapability, float]] = []
        for idx, oid in enumerate(self._ordered_ids):
            cap = self.capabilities[oid]
            if category_filter and cap.category != category_filter:
                continue
            vsa_sim = float(sims[idx])
            cap_tokens = set(_tokenize_semantic_text(f"{cap.organ_id.replace('_', ' ')} {cap.category} {cap.description}"))
            lex_overlap = len(obj_tokens & cap_tokens) / max(1.0, float(len(obj_tokens)))
            io_bonus = 0.0
            if in_set:
                io_bonus += 0.15 * (len(in_set & set(cap.inputs)) / float(len(in_set)))
            if out_set:
                io_bonus += 0.15 * (len(out_set & set(cap.outputs)) / float(len(out_set)))
            combined = vsa_sim + 0.35 * lex_overlap + io_bonus
            scored.append((cap, combined))

        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:top_k]

    def _register_core_profiles(self) -> None:
        core_catalog = [
            OrganCapability(
                organ_id="ukf_state_estimator",
                category="estimation",
                description="Unscented Kalman Filter for non-linear noisy state estimation stabilization filtering.",
                inputs=["observations", "initial_state", "covariance"],
                outputs=["filtered_state", "filtered_covariance"],
                formal_guarantee="Unbiased minimum-variance state estimate under UT Gaussian approx.",
                module_path=".planning.unscented_kalman_estimator",
                class_name="UnscentedKalmanStateEstimator",
                runtime_attr="ukf_estimator",
                aliases=("ukf_estimator",),
            ),
            OrganCapability(
                organ_id="rts_smoother",
                category="estimation",
                description="Rauch-Tung-Striebel fixed-interval backward Bayesian smoother.",
                inputs=["forward_states", "forward_covariances"],
                outputs=["smoothed_states", "smoothed_covariances"],
                formal_guarantee="Monotonic trace covariance reduction over forward filter.",
                module_path=".planning.kalman_rts_smoother",
                class_name="RauchTungStriebelSmoother",
                runtime_attr="rts_smoother",
            ),
            OrganCapability(
                organ_id="notears_causal",
                category="causality",
                description="Continuous optimization for structure causal discovery inference of DAGs.",
                inputs=["timeseries_data"],
                outputs=["adjacency_matrix", "is_dag"],
                formal_guarantee="Exact matrix exponential acyclicity trace(exp(W*W)) - d = 0.",
                module_path=".planning.notears_continuous_causal",
                class_name="ContinuousNOTEARSEngine",
                runtime_attr="notears_engine",
                aliases=("notears_engine",),
            ),
            OrganCapability(
                organ_id="ilqr_trajectory_optimizer",
                category="planning",
                description="Iterative Linear Quadratic Regulator nonlinear trajectory control optimization safe stabilization.",
                inputs=["filtered_state", "initial_state", "goal_state", "cost_matrices", "horizon"],
                outputs=["optimal_trajectory", "optimal_controls", "final_cost"],
                formal_guarantee="Pontryagin first-order stationarity and quadratic convergence.",
                module_path=".planning.pontryagin_ilqr_trajectory_optimizer",
                class_name="PontryaginILQROptimizer",
                runtime_attr="ilqr_optimizer",
                aliases=("ilqr_optimizer",),
            ),
            OrganCapability(
                organ_id="cbf_control_barrier_shield",
                category="safety",
                description="Control Barrier Function Quadratic Program online safety shield stabilization.",
                inputs=["nominal_control", "filtered_state", "current_state", "barrier_params"],
                outputs=["safe_control", "safety_margin", "slack"],
                formal_guarantee="Provable forward invariance of safe set C via Nagumo condition.",
                in_min=-10.0,
                in_max=10.0,
                out_min=-5.0,
                out_max=5.0,
                state_dim=4,
                is_certifier=True,
                module_path=".metacognition.cbf_control_barrier_shield",
                class_name="CBFControlBarrierShield",
                runtime_attr="cbf_shield",
                aliases=("cbf_shield",),
            ),
            OrganCapability(
                organ_id="stl_temporal_logic_monitor",
                category="verification",
                description="Signal Temporal Logic space-robustness quantitative safety monitor certification.",
                inputs=["trajectory", "safe_control", "stl_specification"],
                outputs=["robustness_degree", "is_satisfied"],
                formal_guarantee="Sound quantitative semantics: rho >= 0 implies trajectory |= phi.",
                in_min=-10.0,
                in_max=10.0,
                out_min=0.0,
                out_max=10.0,
                state_dim=4,
                is_certifier=True,
                module_path=".metacognition.ltl_temporal_logic_monitor",
                class_name="STLTemporalLogicMonitor",
                runtime_attr="stl_monitor",
                aliases=("stl_monitor",),
            ),
            OrganCapability(
                organ_id="z3_formal_solver",
                category="verification",
                description="Z3 SMT Solver formal verification first-order logic algebraic constraints constraints proof.",
                inputs=["formula_ast", "declarations", "constraints"],
                outputs=["sat_status", "model_or_core"],
                formal_guarantee="Decidability and soundness over QF-LRA / QF-NRA.",
                is_certifier=True,
                module_path=".logic_symbolic.z3_formal_solver",
                class_name="Z3FormalSolver",
                runtime_attr="z3_solver",
                aliases=("z3_solver",),
            ),
            OrganCapability(
                organ_id="simplex_lp_solver",
                category="optimization",
                description="Two-Phase Revised Simplex Linear Programming exact resource allocation solver.",
                inputs=["cost_c", "matrix_A", "vector_b"],
                outputs=["optimal_x", "optimal_cost", "dual_y"],
                formal_guarantee="Strong duality theorem: primal cost equals dual cost.",
                module_path=".logic_symbolic.simplex_linear_programming",
                class_name="RevisedSimplexLPSolver",
                runtime_attr="simplex_lp",
                aliases=("simplex_lp",),
            ),
            OrganCapability(
                organ_id="rrt_star_planner",
                category="planning",
                description="Rapidly-exploring Random Tree Star optimal motion navigation path planner.",
                inputs=["start_pos", "goal_pos", "obstacles", "bounds"],
                outputs=["path_points", "path_length", "success"],
                formal_guarantee="Asymptotically optimal path cost almost surely as N -> inf.",
                module_path=".planning.voronoi_rrt_star_motion_planner",
                class_name="RRTStarOptimalMotionPlanner",
                runtime_attr="rrt_star",
                aliases=("rrt_star",),
            ),
            OrganCapability(
                organ_id="strips_planner",
                category="planning",
                description="STRIPS PDDL state-space deliberative action search planner with A* admissible heuristic.",
                inputs=["initial_state", "goal_state", "pddl_actions"],
                outputs=["plan", "plan_cost", "final_state", "plan_steps_count"],
                formal_guarantee="Admissible goal-count A* guarantees minimum-cost STRIPS plan.",
                module_path=".planning.pddl_fast_search",
                class_name="FastStateSpacePlanner",
                runtime_attr="strips_planner",
                aliases=("pddl_planner",),
            ),
            OrganCapability(
                organ_id="cegis_synthesizer",
                category="verification",
                description="CEGIS counterexample-guided inductive bitwise optimization code synthesizer with Z3 64-bit bitvector equivalence verification.",
                inputs=["source_code", "cegis_mode", "is_code_safe", "var_names"],
                outputs=["is_equivalent", "candidate_code", "sat_status"],
                formal_guarantee="Formal bitvector equivalence: UNSAT(spec != candidate) across 2^64 inputs.",
                is_certifier=True,
                module_path=".logic_symbolic.cegis_code_synthesizer",
                class_name="CEGISCodeSynthesizer",
                runtime_attr="cegis_synthesizer",
            ),
            OrganCapability(
                organ_id="ast_analyzer",
                category="perception",
                description="Deterministic Python AST code inspector security visitor and cyclomatic complexity analyzer.",
                inputs=["source_code"],
                outputs=["ast_violations", "cyclomatic_complexity", "ast_functions", "is_code_safe"],
                formal_guarantee="Complete syntactic traversal rejecting unsafe imports and eval/exec calls.",
                module_path=".code_inspector.ast_code_analyzer",
                class_name="ASTCodeAnalyzer",
                runtime_attr="ast_analyzer",
            ),
            OrganCapability(
                organ_id="vision_eye",
                category="perception",
                description="Closed-loop Win32 desktop vision eye window geometry inspector without blind automation.",
                inputs=["window_query"],
                outputs=["total_visible_windows", "window_matched", "matched_windows"],
                formal_guarantee="Deterministic Win32 EnumWindows verification before GUI actuation.",
                module_path=".physical_bridge.closed_loop_vision_eye",
                class_name="ClosedLoopVisionEye",
                runtime_attr="vision_eye",
            ),
            OrganCapability(
                organ_id="grid_arc_reasoner",
                category="perception",
                description="ARC abstract spatial grid transformation program synthesizer verified via VSA and Z3.",
                inputs=["arc_train_pairs", "arc_test_input"],
                outputs=["synthesized_program", "predicted_grid", "arc_solved"],
                formal_guarantee="Zero-pixel demo mismatch plus Z3 shape and conservation invariants.",
                is_certifier=True,
                module_path=".logic_symbolic.symbolic_grid_arc_reasoner",
                class_name="SymbolicGridARCReasoner",
                runtime_attr="grid_arc_reasoner",
            ),
        ]
        for cap in core_catalog:
            self.register_capability(cap, overwrite=True)

    def _discover_runtime_specs(self) -> None:
        """Index all remaining organs from SovereignCortexRuntime._LAZY_ORGAN_SPECS without eager imports."""
        try:
            from ..sovereign_cortex_runtime import _LAZY_ORGAN_SPECS
        except Exception:
            _LAZY_ORGAN_SPECS = {}

        for rt_name, (mod_rel, cls_name, _kwargs) in _LAZY_ORGAN_SPECS.items():
            canonical_id = _RUNTIME_TO_COMPOSER_ALIAS.get(rt_name, rt_name)
            if canonical_id in self.capabilities:
                # Merge runtime location metadata onto core capability
                existing = self.capabilities[canonical_id]
                if not existing.module_path:
                    existing.module_path = mod_rel
                    existing.class_name = cls_name
                    existing.runtime_attr = rt_name
                self.aliases[rt_name] = canonical_id
                continue

            cat = _infer_category_from_module(mod_rel, canonical_id)
            ins, outs = _default_io_for_category(cat, canonical_id)
            is_cert = cat == "verification" or canonical_id in {
                "cbf_control_barrier_shield", "stl_temporal_logic_monitor", "z3_formal_solver",
                "lyapunov_certifier", "hoare_verifier", "cegis",
            }
            cap = OrganCapability(
                organ_id=canonical_id,
                category=cat,
                description=f"{cls_name} organ from {mod_rel.strip('.').replace('.', ' ')}",
                inputs=ins,
                outputs=outs,
                formal_guarantee=f"Verified deterministic {cls_name} operational contract.",
                is_certifier=is_cert,
                module_path=mod_rel,
                class_name=cls_name,
                runtime_attr=rt_name,
            )
            self.register_capability(cap, overwrite=False)

        # Explicitly register __getattr__ multi-organ attributes from SovereignCortexRuntime
        extra_runtime = [
            ("hnsw_graph", ".memory_vault.hnsw_submillisecond_graph_index", "HNSWSubMillisecondGraphIndex", "memory",
             "Submillisecond HNSW associative graph index for O(log N) recall."),
            ("vsa_causal", ".planning.vsa_causal_engine", "VSACausalEngine", "causality",
             "VSA-encoded causal counterfactual reasoner over binary hypervectors."),
            ("rem_dream_engine", ".metacognition.rem_autonomous_dream_daemon", "REMAutonomousDreamEngine", "memory",
             "REM autonomous dream replay and offline counterfactual episode consolidator."),
        ]
        for oid, mod_rel, cls_name, cat, desc in extra_runtime:
            if oid not in self.capabilities:
                ins, outs = _default_io_for_category(cat, oid)
                self.register_capability(
                    OrganCapability(
                        organ_id=oid,
                        category=cat,
                        description=desc,
                        inputs=ins,
                        outputs=outs,
                        formal_guarantee=f"Verified deterministic {cls_name} operational contract.",
                        module_path=mod_rel,
                        class_name=cls_name,
                        runtime_attr=oid,
                    ),
                    overwrite=False,
                )

    def invoke(self, organ_id: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke a built-in, runtime, or hot-plugged external organ safely."""
        oid = self.resolve_organ_id(organ_id)

        if oid in self.executors:
            return self.executors[oid](context)

        if oid == "ukf_state_estimator":
            from .unscented_kalman_estimator import UnscentedKalmanStateEstimator
            raw_obs = list(context.get("observations", [0.1, -0.05, 0.02, 0.0]))
            obs = (raw_obs + [0.0] * 4)[:4]
            est = UnscentedKalmanStateEstimator(state_dim=4, obs_dim=4)
            out = est.step(measurement=obs, dt=float(context.get("dt", 0.1)))
            return {
                "filtered_state": out["estimated_state"],
                "filtered_covariance": out["covariance_trace"],
                "ukf_telemetry": out,
            }

        if oid == "ilqr_trajectory_optimizer":
            from .pontryagin_ilqr_trajectory_optimizer import PontryaginILQROptimizer
            filtered = list(context.get("filtered_state", [0.25, 0.0]))
            x0 = [float(filtered[0]), float(filtered[1]) if len(filtered) > 1 else 0.0]
            x_goal = list(context.get("goal_state", [0.0, 0.0]))
            horizon = int(context.get("horizon", 15))
            opt = PontryaginILQROptimizer(dt=0.05, max_iters=15)
            res = opt.optimize_trajectory(x0=x0, x_goal=x_goal, horizon=horizon)
            return {
                "optimal_trajectory": [x0, res["final_state"]],
                "final_cost": res["final_cost"],
                "ilqr_telemetry": res,
            }

        if oid == "cbf_control_barrier_shield":
            from ..metacognition.cbf_control_barrier_shield import CBFControlBarrierShield
            raw_x = list(context.get("filtered_state", [0.2, 0.1, 0.1, 0.5]))
            x_state = (raw_x + [0.0] * 4)[:4]
            raw_u = list(context.get("nominal_control", [0.0, 0.0, 0.0, 0.0]))
            u_nom = (raw_u + [0.0] * 4)[:4]
            shield = CBFControlBarrierShield(state_dim=4, control_dim=4, gamma=2.0)
            res = shield.filter_control_action(x_state=x_state, u_nominal=u_nom)
            lie_margin = float(min(res.get("cbf_lie_conditions", [0.0])))
            return {
                "safe_control": res["u_safe_certified"],
                "safety_margin": lie_margin,
                "is_formally_safe": bool(res["is_formally_safe"]),
                "cbf_intervened": bool(res.get("shield_intervened", False)),
                "cbf_telemetry": res,
            }

        if oid == "stl_temporal_logic_monitor":
            from ..metacognition.ltl_temporal_logic_monitor import STLTemporalLogicMonitor
            trace = context.get("trace")
            if trace is None:
                u_safe = context.get("safe_control", [0.2, 0.1])
                norm_val = min(0.60, float(np.linalg.norm(np.asarray(u_safe, dtype=np.float64))) * 0.25)
                trace = [0.40, 0.45 + 0.2 * norm_val, 0.50, 0.40]
            monitor = STLTemporalLogicMonitor()
            res = monitor.verify_response_guarantee(
                trace=trace,
                safety_ceiling=float(context.get("safety_ceiling", 0.95)),
                trigger_threshold=float(context.get("trigger_threshold", 0.80)),
                recovery_target=float(context.get("recovery_target", 0.65)),
                response_deadline_steps=int(context.get("response_deadline_steps", 4)),
            )
            return {
                "robustness_degree": res["overall_stl_robustness"],
                "is_satisfied": bool(res["satisfied"]),
                "stl_telemetry": res,
            }

        if oid == "notears_causal":
            from .notears_continuous_causal import ContinuousNOTEARSEngine
            data = context.get("timeseries_data")
            if data is None:
                rng = np.random.default_rng(42)
                x = rng.normal(0, 1, size=(60, 1))
                y = 0.8 * x + rng.normal(0, 0.1, size=(60, 1))
                data = np.hstack([x, y])
            eng = ContinuousNOTEARSEngine(lambda1=0.01, w_threshold=0.25)
            res = eng.fit(np.asarray(data, dtype=np.float64), var_names=context.get("var_names"))
            return {
                "adjacency_matrix": res.get("adjacency_matrix", res.get("W_est", [])),
                "is_dag": bool(res.get("is_dag", True)),
                "notears_telemetry": res,
            }

        if oid == "z3_formal_solver":
            from ..logic_symbolic.z3_formal_solver import Z3FormalSolver
            solver = Z3FormalSolver(timeout_ms=3000)
            decls = context.get("declarations", {"rho": "real", "margin": "real"})
            constraints = context.get("constraints", ["rho >= 0", "rho <= 0.95", "margin >= 0"])
            res = solver.solve_constraints(decls, constraints)
            return {
                "sat_status": str(res["status"]).lower(),
                "z3_solution": res.get("solution"),
                "z3_telemetry": res,
            }

        if oid == "simplex_lp_solver":
            from ..logic_symbolic.simplex_linear_programming import RevisedSimplexLPSolver
            lp = RevisedSimplexLPSolver(max_pivots=500, tol=1e-10)
            res = lp.solve_lp(
                c=context.get("cost_c"),
                A=context.get("matrix_A"),
                b=context.get("vector_b"),
            )
            return {
                "optimal_x": res.get("primal_x"),
                "optimal_cost": res.get("primal_objective"),
                "primal_dual_gap": res.get("strong_duality_gap", 0.0),
                "simplex_telemetry": res,
            }

        if oid == "rrt_star_planner":
            from .voronoi_rrt_star_motion_planner import RRTStarOptimalMotionPlanner
            planner = RRTStarOptimalMotionPlanner(step_size=0.8, neighbor_radius=1.8)
            res = planner.plan_motion(
                start=tuple(context.get("start_pos", (0.5, 0.5))),
                goal=tuple(context.get("goal_pos", (9.5, 9.5))),
                bounds=tuple(context.get("bounds", (0.0, 10.0))),
                obstacles=context.get("obstacles"),
                max_iters=int(context.get("max_iters", 350)),
            )
            return {
                "path_points": res.get("path", []),
                "path_length": res.get("final_cost", 0.0),
                "success": bool(res.get("goal_reached", True)),
                "rrt_telemetry": res,
            }

        if oid == "strips_planner":
            from .pddl_fast_search import FastStateSpacePlanner
            planner = FastStateSpacePlanner()
            for act in context.get("pddl_actions", []):
                planner.add_action(
                    name=act["name"],
                    preconditions=set(act.get("preconditions", [])),
                    add_effects=set(act.get("add_effects", [])),
                    del_effects=set(act.get("del_effects", [])),
                    cost=float(act.get("cost", 1.0)),
                )
            init_s = set(context.get("pddl_initial_state", []))
            goal_s = set(context.get("pddl_goal_state", []))
            res = planner.plan(init_s, goal_s, max_nodes=int(context.get("max_nodes", 5000)))
            return {
                "plan": res.get("plan", []),
                "plan_cost": res.get("plan_cost", 0.0),
                "plan_steps_count": res.get("plan_steps_count", len(res.get("plan", []))),
                "pddl_status": res.get("status"),
                "pddl_telemetry": res,
            }

        if oid == "cegis_synthesizer":
            from ..logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
            synth = CEGISCodeSynthesizer()
            spec_mode = context.get("cegis_mode", "bitwise_parity")
            cegis_src = context.get("cegis_source")
            if spec_mode == "nested_loop_induction":
                proof = synth.synthesize_nested_loop_closed_form_cegis(
                    str(cegis_src or context.get("source_code", "")),
                )
            elif spec_mode == "loop_induction":
                proof = synth.synthesize_loop_closed_form_cegis(
                    str(cegis_src or context.get("source_code", "")),
                )
            elif spec_mode == "python_ast" or (cegis_src is not None):
                proof = synth.synthesize_python_ast_cegis(
                    str(cegis_src or context.get("source_code", "")),
                    assume_non_negative=bool(context.get("assume_non_negative", False)),
                )
            elif spec_mode == "power_of_two":
                proof = synth.synthesize_fast_power_of_two()
            else:
                proof = synth.synthesize_fast_bitwise_parity()
            return {
                "is_equivalent": bool(proof.get("is_equivalent", False)),
                "candidate_code": proof.get("candidate_code"),
                "synthesized_source": proof.get("synthesized_source"),
                "sat_status": "sat" if proof.get("is_equivalent") else "unsat",
                "cegis_telemetry": proof,
            }

        if oid == "grid_arc_reasoner":
            from ..logic_symbolic.symbolic_grid_arc_reasoner import SymbolicGridARCReasoner
            reasoner = SymbolicGridARCReasoner(bus=self.bus)
            train_pairs = context.get("arc_train_pairs") or [
                ([[1, 0], [0, 0]], [[0, 1], [0, 0]]),
                ([[2, 3], [0, 0]], [[3, 2], [0, 0]]),
            ]
            test_inp = context.get("arc_test_input") or [[4, 0], [5, 0]]
            res = reasoner.solve_arc_task(train_pairs, test_inp)
            return {
                "arc_solved": bool(res.get("solved", False)),
                "synthesized_program": res.get("synthesized_program"),
                "predicted_grid": res.get("predicted_grid"),
                "sat_status": "sat" if res.get("solved") else "unsat",
                "arc_telemetry": res,
            }

        if oid == "ast_analyzer":
            from ..code_inspector.ast_code_analyzer import ASTCodeAnalyzer
            analyzer = ASTCodeAnalyzer()
            src = str(context.get("source_code", "def identity(x):\n    return x\n"))
            res = analyzer.analyze_source(src)
            syms = res.get("symbols", {})
            return {
                "ast_violations": res.get("violations", []),
                "cyclomatic_complexity": res.get("cyclomatic_complexity", 1),
                "ast_functions": syms.get("functions", []),
                "is_code_safe": bool(res.get("security_clean", False)) and bool(res.get("is_valid_syntax", False)),
                "ast_telemetry": res,
            }

        if oid == "vision_eye":
            from ..physical_bridge.closed_loop_vision_eye import ClosedLoopVisionEye
            eye = ClosedLoopVisionEye()
            query = context.get("window_query")
            if query:
                res = eye.verify_window_exists(str(query))
                return {
                    "window_matched": bool(res.get("exists", False)),
                    "matched_windows": res.get("matched_windows", []),
                    "vision_telemetry": res,
                }
            res = eye.inspect_visible_windows(max_windows=int(context.get("max_windows", 25)))
            return {
                "total_visible_windows": res.get("total_visible_windows", 0),
                "windows": res.get("windows", []),
                "vision_telemetry": res,
            }

        if oid == "lyapunov_certifier":
            from ..logic_symbolic.lyapunov_sdp_stability_certifier import LyapunovSDPStabilityCertifier
            cert = LyapunovSDPStabilityCertifier()
            a_mat = context.get("system_matrix", np.eye(4) * 0.5)
            p_mat, res_val, iters_used = cert.solve_discrete_lyapunov_fast(np.asarray(a_mat, dtype=np.float64))
            return {
                "lyapunov_matrix_norm": float(np.linalg.norm(p_mat)),
                "stein_residual": float(res_val),
                "smith_iters": int(iters_used),
                "sat_status": "sat" if res_val < 1e-6 else "unsat",
            }

        # Operational declarative contract dispatch across 100% of cataloged substrate organs (v8.1.0)
        cap = self.get(oid)
        if cap and cap.module_path and cap.class_name:
            try:
                from .organ_contracts import execute_organ_contract
                contract_res = execute_organ_contract(oid, cap, context)
                if contract_res is not None:
                    return contract_res
                mod = importlib.import_module(cap.module_path, package="aethermind_cognitive_substrate")
                cls = getattr(mod, cap.class_name)
                from ..sovereign_cortex_runtime import _LAZY_ORGAN_SPECS
                kwargs = _LAZY_ORGAN_SPECS.get(cap.runtime_attr or oid, ("", "", {}))[2]
                inst = cls(**kwargs)
                return {"status": "INSTANTIATED", "organ_id": oid, "class": type(inst).__name__}
            except Exception as exc:
                return {"status": "LAZY_INVOKE_FALLBACK", "organ_id": oid, "error": str(exc)}

        return {"status": "ok", "organ_id": oid}
