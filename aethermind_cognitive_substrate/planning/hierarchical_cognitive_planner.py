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

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .autonomous_cognitive_composer import AutonomousCognitiveComposer, CompositionReceipt
from .dag_task_decomposer import DAGTaskDecomposer


@dataclass
class SubGoalSpec:
    """Single node in a hierarchical multi-level mission graph."""
    subgoal_id: str
    objective: str
    spec: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    estimated_ms: float = 10.0


class HierarchicalCognitivePlanner:
    """Macro -> Meso -> Micro Multi-Level Planner over Modular Organs & AVX2 JIT."""

    def __init__(self, composer: Optional[AutonomousCognitiveComposer] = None):
        self.composer = composer or AutonomousCognitiveComposer()

    def execute_hierarchical_mission(
        self,
        mission_name: str,
        subgoals: List[SubGoalSpec],
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Decompose composite goal into topological sub-missions, prove, execute, and JIT-fuse."""
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
        shared_context: Dict[str, Any] = dict(initial_context or {})
        sub_receipts: Dict[str, CompositionReceipt] = {}
        route_vectors_u64: List[np.ndarray] = []

        all_ok = True
        all_safe = True

        for sg_id in topo_order:
            sg = subgoal_map[sg_id]
            merged_spec = dict(shared_context)
            merged_spec.update(sg.spec)
            receipt = self.composer.execute_pipeline(sg.objective, merged_spec)
            sub_receipts[sg_id] = receipt

            if not receipt.overall_success:
                all_ok = False
            if not receipt.certified_safe:
                all_safe = False

            # Propagate stage outputs into shared hierarchical context for downstream dependent subgoals
            for st in receipt.stages:
                shared_context.update(st.data)

            # Compile subgoal DAG route into AVX2 L1 signature vector
            pipeline_orgs = [st.organ_id for st in receipt.stages] or list(
                receipt.formal_certificate.get("pipeline_organs", [])
            )
            compiled = self.composer.dag_compiler.compile_route(pipeline_orgs, objective=sg.objective)
            exec_res = self.composer.dag_compiler.execute_route(compiled)
            route_vectors_u64.append(exec_res["route_signature_u64"])

            if not all_ok:
                break

        # Micro-level fusion across all subgoal route vectors using native x86_64 AVX2 W^X JIT
        fused_sig, jit_mode = self.composer.dag_compiler.jit_bind_hierarchical_path(route_vectors_u64)

        self.composer.bus.publish(
            topic="composer.hierarchical.complete",
            payload={
                "mission_name": mission_name,
                "subgoals_executed": len(sub_receipts),
                "overall_success": all_ok,
                "certified_safe": all_safe,
                "avx2_jit_mode": jit_mode,
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
                "parallel_generations": dag_plan.get("parallel_stages", []),
                "critical_path": dag_plan.get("critical_path", []),
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
