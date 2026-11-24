"""Hierarchical Multi-Level Cognitive Planner & AVX2 Route Fusion Engine (v7.5.0).

Coordinates three coupled levels of Modular AGI autonomy:
  1. Macro-Level: Schedules dependent sub-missions via `DAGTaskDecomposer`
     (topological sort, parallel generations, critical-path detection).
  2. Meso-Level: Dispatches each sub-mission to `AutonomousCognitiveComposer`
     with holographic VSA discovery, Z3 edge verification, and prior propagation.
  3. Micro-Level: Fuses sub-mission 10,240-bit route signatures via native x86_64
     AVX2 W^X JIT machine code (`VSADAGBytecodeCompiler.jit_bind_hierarchical_path`).
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .autonomous_cognitive_composer import AutonomousCognitiveComposer, CompositionReceipt
from .dag_task_decomposer import DAGTaskDecomposer


@dataclass
class SubGoalSpec:
    """Single node in a hierarchical multi-level mission graph with typed edge bindings."""
    subgoal_id: str
    objective: str
    spec: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_ms: float = 10.0
    input_bindings: Dict[str, Tuple[str, str]] = field(default_factory=dict)


class HierarchicalCognitivePlanner:
    """Macro -> Meso -> Micro Multi-Level Planner over Modular Organs & AVX2 JIT."""

    def __init__(self, composer: Optional[AutonomousCognitiveComposer] = None):
        self.composer = composer or AutonomousCognitiveComposer()
        self._route_lock = threading.Lock()

    def execute_hierarchical_mission(
        self,
        mission_name: str,
        subgoals: List[SubGoalSpec],
        initial_context: Optional[Dict[str, Any]] = None,
        parallel_waves: bool = True,
    ) -> Dict[str, Any]:
        """Decompose composite goal into parallel topological waves, resolve typed edges, prove, and JIT-fuse."""
        t0 = time.perf_counter()
        decomposer = DAGTaskDecomposer()
        subgoal_map: Dict[str, SubGoalSpec] = {sg.subgoal_id: sg for sg in subgoals}

        for sg in subgoals:
            decomposer.add_task(
                task_id=sg.subgoal_id,
                description=sg.objective,
                dependencies=sg.dependencies,
                duration_ms=sg.estimated_ms,
            )

        dag_plan = decomposer.validate_and_schedule()
        if not dag_plan.get("is_valid"):
            return {
                "mission_name": mission_name,
                "overall_success": False,
                "certified_safe": False,
                "status": "HIERARCHICAL_DAG_INVALID",
                "dag_error": dag_plan,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
            }

        topo_order: List[str] = dag_plan["topological_sequence"]
        parallel_generations: List[List[str]] = dag_plan.get("parallel_stages", [[s] for s in topo_order])
        base_context: Dict[str, Any] = dict(initial_context or {})
        subgoal_outputs: Dict[str, Dict[str, Any]] = {}
        sub_receipts: Dict[str, CompositionReceipt] = {}
        route_vectors_u64: Dict[str, np.ndarray] = {}

        all_ok = True
        all_safe = True
        typed_bindings_resolved = 0
        parallel_execution_used = False
        max_wave_width = max((len(w) for w in parallel_generations), default=1)

        def _build_node_spec(sg: SubGoalSpec) -> Tuple[Dict[str, Any], int]:
            merged = dict(base_context)
            # Propagate dependency outputs deterministically without sibling race leakage
            for dep_id in sg.dependencies:
                if dep_id in subgoal_outputs:
                    merged.update(subgoal_outputs[dep_id])
            merged.update(sg.spec)
            bound_cnt = 0
            for target_key, (src_sg, src_key) in sg.input_bindings.items():
                src_out = subgoal_outputs.get(src_sg, {})
                if src_key in src_out:
                    merged[target_key] = src_out[src_key]
                    bound_cnt += 1
            return merged, bound_cnt

        def _run_subgoal(sg_id: str) -> Tuple[str, CompositionReceipt, Dict[str, Any], np.ndarray, int]:
            sg = subgoal_map[sg_id]
            node_spec, bound_cnt = _build_node_spec(sg)
            receipt = self.composer.execute_pipeline(sg.objective, node_spec)
            agg_out: Dict[str, Any] = {}
            for st in receipt.stages:
                agg_out.update(st.data)
            pipeline_orgs = [st.organ_id for st in receipt.stages] or list(
                receipt.formal_certificate.get("pipeline_organs", [])
            )
            with self._route_lock:
                compiled = self.composer.dag_compiler.compile_route(pipeline_orgs, objective=sg.objective)
                exec_res = self.composer.dag_compiler.execute_route(compiled)
            return sg_id, receipt, agg_out, exec_res["route_signature_u64"], bound_cnt

        for wave in parallel_generations:
            if parallel_waves and len(wave) > 1:
                parallel_execution_used = True
                with ThreadPoolExecutor(max_workers=min(4, len(wave))) as pool:
                    wave_results = list(pool.map(_run_subgoal, wave))
            else:
                wave_results = [_run_subgoal(sg_id) for sg_id in wave]

            for sg_id, receipt, agg_out, route_vec, bound_cnt in wave_results:
                sub_receipts[sg_id] = receipt
                subgoal_outputs[sg_id] = agg_out
                route_vectors_u64[sg_id] = route_vec
                typed_bindings_resolved += bound_cnt
                if not receipt.overall_success:
                    all_ok = False
                if not receipt.certified_safe:
                    all_safe = False

            if not all_ok:
                break

        ordered_route_vecs = [route_vectors_u64[sg_id] for sg_id in topo_order if sg_id in route_vectors_u64]
        fused_sig, jit_mode = self.composer.dag_compiler.jit_bind_hierarchical_path(ordered_route_vecs)

        self.composer.bus.publish(
            topic="composer.hierarchical.complete",
            payload={
                "mission_name": mission_name,
                "subgoals_executed": len(sub_receipts),
                "overall_success": all_ok,
                "certified_safe": all_safe,
                "avx2_jit_mode": jit_mode,
                "waves_executed": len(parallel_generations),
                "parallel_execution_used": parallel_execution_used,
            },
            organ_id="hierarchical_planner",
            confidence=1.0 if (all_ok and all_safe) else 0.0,
        )

        return {
            "mission_name": mission_name,
            "overall_success": all_ok,
            "certified_safe": all_safe,
            "status": "HIERARCHICAL_MISSION_CERTIFIED" if (all_ok and all_safe) else "HIERARCHICAL_MISSION_FAILED",
            "macro_schedule": {
                "execution_order": topo_order,
                "parallel_generations": parallel_generations,
                "critical_path": dag_plan.get("critical_path", []),
                "waves_executed": len(parallel_generations),
                "max_wave_width": max_wave_width,
                "parallel_execution_used": parallel_execution_used,
                "typed_bindings_resolved": typed_bindings_resolved,
            },
            "subgoals_executed": len(sub_receipts),
            "subgoal_receipts": {
                k: {
                    "overall_success": r.overall_success,
                    "certified_safe": r.certified_safe,
                    "stages": [s.organ_id for s in r.stages],
                    "avx2_route_trace": r.formal_certificate.get("avx2_route_trace"),
                }
                for k, r in sub_receipts.items()
            },
            "micro_fused_signature_popcount": int(sum(int(w).bit_count() for w in fused_sig)),
            "avx2_wx_jit_mode": jit_mode,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }
