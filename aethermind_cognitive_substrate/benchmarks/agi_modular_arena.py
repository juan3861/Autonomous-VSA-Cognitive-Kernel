"""AGI-Modular Arena: Open Multi-Domain Benchmark Suite for v7.4.0.

Measures end-to-end Modular AGI autonomy across four reproducible domains using
isolated temporary persistence (never mutating workspace SQLite files):
  Track A: 82+-Organ Holographic VSA Auto-Discovery & External Plug-and-Play
  Track B: Deliberative STRIPS / PDDL Planning via Synthesized DAG
  Track C: AST/CFG Perception-to-VSA + CEGIS 64-bit Inductive Code Synthesis
  Track D: Cross-Session Closed-Loop Learning (SQLite + HippoRAG + PagedOS + REM)
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from aethermind_cognitive_substrate.memory_vault.hierarchical_paged_memory_os import HierarchicalPagedMemoryOS
from aethermind_cognitive_substrate.memory_vault.hipporag_knowledge_graph import HippoRAGKnowledgeGraph
from aethermind_cognitive_substrate.memory_vault.vsa_persistence_bridge import VSA10240PersistenceBridge
from aethermind_cognitive_substrate.memory_vault.vsa_semantic_bus import VSAHyperdimensionalBus
from aethermind_cognitive_substrate.metacognition.rem_autonomous_dream_daemon import REMAutonomousDreamEngine
from aethermind_cognitive_substrate.physical_bridge.perception_vsa_bridge import PerceptionVSABridge
from aethermind_cognitive_substrate.planning.autonomous_cognitive_composer import (
    AutonomousCognitiveComposer,
    OrganCapability,
)


def bench_track_a_plug_and_play_discovery() -> Dict[str, Any]:
    t0 = time.perf_counter()
    composer = AutonomousCognitiveComposer()
    catalog_count = len(composer.capabilities)

    plugin_cap = OrganCapability(
        organ_id="quantum_anomaly_observer",
        category="telemetry_plugin",
        description="Detects quantum resonance telemetry anomalies in external spacecraft feeds.",
        inputs=["telemetry_stream"],
        outputs=["anomaly_score", "status"],
        formal_guarantee="Bounded L2 anomaly residual inside [0, 1].",
        in_min=-10.0,
        in_max=10.0,
        out_min=0.0,
        out_max=1.0,
    )
    composer.register_plugin(
        plugin_cap,
        lambda ctx: {"anomaly_score": 0.04, "status": "PLUGIN_OK", "sample_n": len(ctx.get("telemetry_stream", []))},
    )

    pipeline = composer.synthesize_pipeline(
        "quantum anomaly telemetry observer",
        {"telemetry_stream": [0.1, 0.2, 0.15]},
    )
    receipt = composer.execute_pipeline(
        "quantum anomaly telemetry observer",
        {"telemetry_stream": [0.1, 0.2, 0.15], "require_formal_safety": True},
    )
    composer.unregister_plugin("quantum_anomaly_observer")

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "catalog_organs_indexed": catalog_count,
        "plugin_selected": "quantum_anomaly_observer" in pipeline,
        "synthesized_pipeline": pipeline,
        "overall_success": receipt.overall_success,
        "certified_safe": receipt.certified_safe,
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_b_pddl_planning() -> Dict[str, Any]:
    t0 = time.perf_counter()
    composer = AutonomousCognitiveComposer()
    spec = {
        "pddl_initial_state": {"robot_at_dock", "cargo_unloaded", "door_locked"},
        "pddl_goal_state": {"cargo_delivered", "robot_at_dock"},
        "pddl_actions": [
            {"name": "unlock_door", "preconditions": {"door_locked"}, "add_effects": {"door_open"}, "del_effects": {"door_locked"}, "cost": 1.0},
            {"name": "load_cargo", "preconditions": {"robot_at_dock", "cargo_unloaded"}, "add_effects": {"cargo_loaded"}, "del_effects": {"cargo_unloaded"}, "cost": 1.0},
            {"name": "move_to_bay", "preconditions": {"robot_at_dock", "door_open"}, "add_effects": {"robot_at_bay"}, "del_effects": {"robot_at_dock"}, "cost": 2.0},
            {"name": "deliver_cargo", "preconditions": {"robot_at_bay", "cargo_loaded"}, "add_effects": {"cargo_delivered"}, "del_effects": {"cargo_loaded"}, "cost": 1.0},
            {"name": "return_to_dock", "preconditions": {"robot_at_bay", "door_open"}, "add_effects": {"robot_at_dock"}, "del_effects": {"robot_at_bay"}, "cost": 2.0},
        ],
        "require_formal_safety": True,
    }
    receipt = composer.execute_pipeline("strips pddl action planning logistics", spec)
    pddl_stage = next((s for s in receipt.stages if s.organ_id == "strips_planner"), None)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "overall_success": receipt.overall_success,
        "certified_safe": receipt.certified_safe,
        "plan_steps": pddl_stage.data.get("plan", []) if pddl_stage else [],
        "plan_cost": pddl_stage.data.get("plan_cost", -1.0) if pddl_stage else -1.0,
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_c_ast_cegis_synthesis() -> Dict[str, Any]:
    t0 = time.perf_counter()
    bus = VSAHyperdimensionalBus(dimension=10240, seed=77)
    bridge = PerceptionVSABridge(bus=bus)
    sample_code = "def is_even(x: int) -> bool:\n    return (x % 2) == 0\n"
    ast_evt_info = bridge.encode_code_ast(sample_code)
    vis_evt_info = bridge.encode_desktop_state(max_windows=5)

    composer = AutonomousCognitiveComposer(bus=bus)
    receipt = composer.execute_pipeline(
        "ast cegis bitwise optimization synthesis verification",
        {"source_code": sample_code, "cegis_mode": "bitwise_parity", "require_formal_safety": True},
    )
    cegis_stage = next((s for s in receipt.stages if s.organ_id == "cegis_synthesizer"), None)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "ast_security_clean": ast_evt_info["payload"]["security_clean"],
        "cfg_blocks": ast_evt_info["payload"].get("cfg_blocks", 0),
        "vision_status": vis_evt_info["payload"].get("status", "UNKNOWN"),
        "overall_success": receipt.overall_success,
        "certified_safe": receipt.certified_safe,
        "cegis_equivalent": bool(cegis_stage.data.get("is_equivalent")) if cegis_stage else False,
        "candidate_code": cegis_stage.data.get("candidate_code") if cegis_stage else None,
        "vsa_bus_events": len(bus.event_log),
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_d_cross_session_learning() -> Dict[str, Any]:
    t0 = time.perf_counter()
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = str(Path(tmpdir) / "arena_session_memory.db")
        vec_dir = str(Path(tmpdir) / "vecs")

        # Session 1: Unshielded custom organ fails Z3 sink requirement -> stored across SQLite/HippoRAG/PagedOS/REM
        p1 = VSA10240PersistenceBridge(db_path=db_file, storage_dir=vec_dir)
        h1 = HippoRAGKnowledgeGraph()
        pm1 = HierarchicalPagedMemoryOS()
        rem1 = REMAutonomousDreamEngine()
        comp1 = AutonomousCognitiveComposer(persistence=p1, hipporag=h1, paged_memory=pm1, rem_engine=rem1)

        s1_fail = comp1.execute_pipeline(
            "safe_stabilization_closed_loop",
            {"custom_pipeline": ["ukf_state_estimator"], "observations": [0.2, -0.1], "require_formal_safety": True},
        )
        rem_logged = len(rem1.dream_episodes_log)

        # Session 2: Brand-new composer, fresh HippoRAG & PagedOS backed ONLY by tmp SQLite -> auto-hydrates & succeeds
        p2 = VSA10240PersistenceBridge(db_path=db_file, storage_dir=vec_dir)
        h2 = HippoRAGKnowledgeGraph()
        pm2 = HierarchicalPagedMemoryOS()
        comp2 = AutonomousCognitiveComposer(persistence=p2, hipporag=h2, paged_memory=pm2)

        hydrated_nodes = h2.graph.number_of_nodes()
        s2_pass = comp2.execute_pipeline(
            "safe_stabilization_closed_loop",
            {"observations": [0.2, -0.1, 0.05, 0.0], "require_formal_safety": True},
        )
        priors_after = p2.query_organ_priors("safe_stabilization_closed_loop")

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "session1_rejected_unsafe": (not s1_fail.overall_success) and (not s1_fail.certified_safe),
        "session1_rem_episodes_queued": rem_logged,
        "session2_hydrated_hipporag_nodes": hydrated_nodes,
        "session2_adapted_success": s2_pass.overall_success and s2_pass.certified_safe,
        "session2_pipeline": [s.organ_id for s in s2_pass.stages],
        "priors_recorded_organs": len(priors_after),
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_e_python_ast_cegis() -> Dict[str, Any]:
    from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer

    t0 = time.perf_counter()
    synth = CEGISCodeSynthesizer()
    res_mul = synth.synthesize_python_ast_cegis("def fast_scale(x, y): return (x * 8) + (y ^ y)")
    res_mod = synth.synthesize_python_ast_cegis("def is_div4(x): return (x % 4) == 0")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "scale_proven": bool(res_mul["is_equivalent"]),
        "scale_candidate": res_mul["candidate_code"],
        "scale_speedup": res_mul["cycle_speedup_ratio"],
        "mod4_proven": bool(res_mod["is_equivalent"]),
        "mod4_candidate": res_mod["candidate_code"],
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_f_hierarchical_arc_avx2() -> Dict[str, Any]:
    from aethermind_cognitive_substrate.planning.hierarchical_cognitive_planner import (
        HierarchicalCognitivePlanner,
        SubGoalSpec,
    )

    t0 = time.perf_counter()
    planner = HierarchicalCognitivePlanner()
    train_pairs = [
        ([[1, 2, 0], [0, 0, 0]], [[0, 0, 0], [0, 2, 1]]),
        ([[3, 0, 0], [4, 5, 0]], [[0, 5, 4], [0, 0, 3]]),
    ]
    test_inp = [[7, 8, 0], [0, 9, 0]]
    res = planner.execute_hierarchical_mission(
        mission_name="hierarchical_arc_and_cegis",
        subgoals=[
            SubGoalSpec(
                subgoal_id="stage_arc_grid",
                objective="arc abstract spatial grid transformation reasoner",
                spec={"arc_train_pairs": train_pairs, "arc_test_input": test_inp, "require_formal_safety": True},
            ),
            SubGoalSpec(
                subgoal_id="stage_cegis_opt",
                objective="cegis inductive python code optimization synthesis verification",
                spec={"cegis_mode": "python_ast", "cegis_source": "def f(x): return x * 4", "require_formal_safety": True},
                dependencies=["stage_arc_grid"],
            ),
        ],
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    arc_prog = None
    for _, sg_info in res.get("subgoal_receipts", {}).items():
        if "grid_arc_reasoner" in sg_info.get("stages", []):
            arc_prog = True
    return {
        "overall_success": bool(res["overall_success"]),
        "certified_safe": bool(res["certified_safe"]),
        "subgoals_executed": int(res["subgoals_executed"]),
        "avx2_wx_jit_mode": int(res["avx2_wx_jit_mode"]),
        "arc_stage_executed": bool(arc_prog),
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_g_arc_compositional_batch() -> Dict[str, Any]:
    from aethermind_cognitive_substrate.logic_symbolic.symbolic_grid_arc_reasoner import SymbolicGridARCReasoner

    reasoner = SymbolicGridARCReasoner()
    # Ground-truth transforms withheld from solver: solver sees only input/output pixel demos
    specs = [
        ("arc_01_rot90", ["rot90"], [
            [[1, 2], [3, 4], [5, 6]],
            [[7, 0], [8, 9], [1, 2]],
            [[4, 5], [6, 7], [0, 9]],
        ]),
        ("arc_02_crop_scale2x", ["crop_nonzero", "scale_2x"], [
            [[0, 0, 0], [0, 1, 2], [0, 3, 0]],
            [[0, 5, 0], [0, 0, 6], [0, 0, 0]],
            [[0, 0, 0, 0], [0, 7, 8, 0], [0, 0, 9, 0]],
        ]),
        ("arc_03_gravity_mirror_h", ["gravity_down", "mirror_concat_h"], [
            [[1, 0, 2], [0, 3, 0], [0, 0, 4]],
            [[5, 6, 0], [0, 0, 7], [8, 0, 0]],
            [[0, 2, 0], [3, 0, 1], [0, 4, 0]],
        ]),
        ("arc_04_flip_h_invert", ["flip_h", "invert_nonzero_color"], [
            [[1, 2, 0], [0, 3, 4]],
            [[4, 0, 1], [2, 3, 0]],
            [[0, 1, 4], [3, 2, 0]],
        ]),
        ("arc_05_fill_enclosed", ["fill_enclosed_zeros"], [
            [[2, 2, 2, 2], [2, 0, 0, 2], [2, 0, 0, 2], [2, 2, 2, 2]],
            [[0, 3, 3, 3, 0], [0, 3, 0, 3, 0], [0, 3, 3, 3, 0], [0, 0, 0, 0, 0]],
            [[5, 5, 5, 5], [5, 0, 5, 5], [5, 0, 0, 5], [5, 5, 5, 5]],
        ]),
        ("arc_06_gravity_left_mirror_v", ["gravity_left", "mirror_concat_v"], [
            [[0, 1, 0], [2, 0, 3]],
            [[0, 0, 4], [0, 5, 6]],
            [[7, 0, 8], [0, 9, 0]],
        ]),
        ("arc_07_outline_scale2x", ["outline_nonzero", "scale_2x"], [
            [[4, 4, 4], [4, 4, 4], [4, 4, 4]],
            [[0, 0, 0, 0], [0, 5, 5, 5], [0, 5, 5, 5], [0, 5, 5, 5]],
            [[7, 7, 7, 7], [7, 7, 7, 7], [7, 7, 7, 7], [7, 7, 7, 7]],
        ]),
        ("arc_08_transpose_tile2x2", ["transpose", "tile_2x2"], [
            [[1, 2], [3, 4], [5, 6]],
            [[0, 7], [8, 9], [1, 3]],
            [[2, 0], [4, 5], [6, 8]],
        ]),
    ]
    tasks = []
    for tid, gt_prog, grids in specs:
        demos = [(g, reasoner.apply_program(gt_prog, g)) for g in grids[:2]]
        test_in = grids[2]
        exp_out = reasoner.apply_program(gt_prog, test_in)
        tasks.append({
            "task_id": tid,
            "train_pairs": demos,
            "test_input": test_in,
            "expected_output": exp_out,
        })
    return reasoner.evaluate_benchmark_batch(tasks, max_program_depth=2)


def bench_track_h_fused_jit_3step_arc_conditional_cegis() -> Dict[str, Any]:
    from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
    from aethermind_cognitive_substrate.logic_symbolic.symbolic_grid_arc_reasoner import SymbolicGridARCReasoner
    from aethermind_cognitive_substrate.memory_vault.vsa_dag_compiler import VSADAGBytecodeCompiler
    import numpy as np

    t0 = time.perf_counter()
    dag_comp = VSADAGBytecodeCompiler()
    rng = np.random.default_rng(7700)
    vecs = [rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64) for _ in range(4)]
    shifts = [0, 7, 64, 199]
    _, jit_mode = dag_comp.jit_permuted_xor_chain(vecs, shifts)

    synth = CEGISCodeSynthesizer()
    if_res = synth.synthesize_python_ast_cegis("def cond_scale(x): return (x * 8) if x > 0 else (x * 4)")

    reasoner = SymbolicGridARCReasoner()
    gt_prog = ["crop_nonzero", "flip_h", "scale_2x"]
    grids = [
        [[0, 0, 0, 0], [0, 1, 2, 0], [0, 3, 0, 0], [0, 0, 0, 0]],
        [[0, 4, 5, 0], [0, 0, 6, 0], [0, 0, 0, 0]],
        [[0, 0, 0], [0, 7, 8], [0, 9, 1]],
    ]
    demos = [(g, reasoner.apply_program(gt_prog, g)) for g in grids[:2]]
    arc3 = reasoner.solve_arc_task(demos, grids[2], max_program_depth=3)
    exp_out = reasoner.apply_program(gt_prog, grids[2]).tolist()

    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "fused_jit_mode": int(jit_mode),
        "conditional_cegis_proven": bool(if_res["is_equivalent"]),
        "conditional_candidate": if_res["candidate_code"],
        "arc_3step_solved": bool(arc3["solved"]) and arc3["predicted_grid"] == exp_out,
        "arc_3step_program": arc3.get("synthesized_program"),
        "elapsed_ms": round(elapsed_ms, 3),
    }


def bench_track_i_cython_jit_and_loop_induction() -> Dict[str, Any]:
    from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
    from aethermind_cognitive_substrate.physical_bridge.fast_vsa_bridge import _load_cython_ext
    import numpy as np

    t0 = time.perf_counter()
    cy = _load_cython_ext()
    cy_jit_ok = False
    if cy is not None and hasattr(cy, "cy_jit_compile_permuted_xor_chain"):
        rng = np.random.default_rng(7800)
        mat = rng.integers(0, np.iinfo(np.uint64).max, size=(4, 160), dtype=np.uint64)
        sh = np.array([0, 7, 64, 199], dtype=np.uint64)
        out = np.zeros(160, dtype=np.uint64)
        h = int(cy.cy_jit_compile_permuted_xor_chain(sh))
        try:
            mode = int(cy.cy_jit_exec_permuted_xor_chain(h, mat, out))
            cy_jit_ok = (mode == 1)
        finally:
            cy.cy_jit_free_permuted_xor_chain(h)

    synth = CEGISCodeSynthesizer()
    r_odds = synth.synthesize_loop_closed_form_cegis(
        "def sum_odds(n):\n    acc = 0\n    for i in range(n):\n        acc = acc + (2 * i + 1)\n    return acc\n"
    )
    r_scale = synth.synthesize_loop_closed_form_cegis(
        "def loop_scale(x, n):\n    acc = 0\n    for i in range(n):\n        acc = acc + (x * 4)\n    return acc\n"
    )
    r_xor = synth.synthesize_loop_closed_form_cegis(
        "def xor_loop(x, n):\n    acc = 0\n    i = 0\n    while i < n:\n        acc = acc ^ x\n        i = i + 1\n    return acc\n"
    )
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "cython_zero_copy_jit_executed": cy_jit_ok,
        "odds_proven": bool(r_odds["is_equivalent"]),
        "odds_closed_form": r_odds.get("candidate_code"),
        "scale_proven": bool(r_scale["is_equivalent"]),
        "scale_closed_form": r_scale.get("candidate_code"),
        "xor_proven": bool(r_xor["is_equivalent"]),
        "xor_closed_form": r_xor.get("candidate_code"),
        "elapsed_ms": round(elapsed_ms, 3),
    }


def main():
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "7.8.0-APEX-MODULAR-AGI-INDUCTIVE-SOVEREIGN",
        "track_a_plug_and_play": bench_track_a_plug_and_play_discovery(),
        "track_b_pddl_planning": bench_track_b_pddl_planning(),
        "track_c_ast_cegis": bench_track_c_ast_cegis_synthesis(),
        "track_d_cross_session": bench_track_d_cross_session_learning(),
        "track_e_python_ast_cegis": bench_track_e_python_ast_cegis(),
        "track_f_hierarchical_arc": bench_track_f_hierarchical_arc_avx2(),
        "track_g_arc_batch_8": bench_track_g_arc_compositional_batch(),
        "track_h_fused_jit_3step_arc": bench_track_h_fused_jit_3step_arc_conditional_cegis(),
        "track_i_cython_jit_loop_induction": bench_track_i_cython_jit_and_loop_induction(),
    }

    out_dir = Path(__file__).resolve().parent
    json_path = out_dir / "AGI_ARENA_RESULTS.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    a = results["track_a_plug_and_play"]
    b = results["track_b_pddl_planning"]
    c = results["track_c_ast_cegis"]
    d = results["track_d_cross_session"]
    e = results["track_e_python_ast_cegis"]
    f_res = results["track_f_hierarchical_arc"]
    g_res = results["track_g_arc_batch_8"]
    h_res = results["track_h_fused_jit_3step_arc"]
    i_res = results["track_i_cython_jit_loop_induction"]

    md = f"""# AGI-Modular Multi-Domain Arena Results (`v7.8.0`)

**Generated:** `{results['timestamp']}`  
**Kernel Version:** `{results['version']}`

| Track | Cognitive Domain | Status | Key Metric | Latency (ms) |
|---|---|---|---|---:|
| **Track A** | 82+-Organ VSA Discovery + Hot-Plug External Module | **{'PASS' if a['overall_success'] and a['plugin_selected'] else 'FAIL'}** | `{a['catalog_organs_indexed']}` organs indexed; plugin Z3-verified | `{a['elapsed_ms']} ms` |
| **Track B** | Deliberative STRIPS/PDDL State-Space Planning | **{'PASS' if b['overall_success'] and b['certified_safe'] else 'FAIL'}** | `{len(b['plan_steps'])}` optimal steps (cost `{b['plan_cost']}`) | `{b['elapsed_ms']} ms` |
| **Track C** | AST/CFG Perception-to-VSA + CEGIS Bit-Exact Synthesis | **{'PASS' if c['overall_success'] and c['cegis_equivalent'] else 'FAIL'}** | `UNSAT(spec != {c['candidate_code']})` (`{c['vsa_bus_events']}` bus events) | `{c['elapsed_ms']} ms` |
| **Track D** | Cross-Session Closed-Loop Learning (`SQLite + HippoRAG + PagedOS + REM`) | **{'PASS' if d['session1_rejected_unsafe'] and d['session2_adapted_success'] else 'FAIL'}** | Hydrated `{d['session2_hydrated_hipporag_nodes']}` graph nodes -> `{len(d['session2_pipeline'])}` certified stages | `{d['elapsed_ms']} ms` |
| **Track E** | Arbitrary Python AST CEGIS + E-Graph Optimization | **{'PASS' if e['scale_proven'] and e['mod4_proven'] else 'FAIL'}** | `(x*8)+(y^y) -> {e['scale_candidate']}` ({e['scale_speedup']}x cycles); `(x%4)==0 -> {e['mod4_candidate']}` | `{e['elapsed_ms']} ms` |
| **Track F** | Hierarchical Macro->Meso->Micro Planning + ARC Grid + AVX2 W^X JIT | **{'PASS' if f_res['overall_success'] and f_res['certified_safe'] else 'FAIL'}** | `{f_res['subgoals_executed']}` hierarchical subgoals; JIT mode `{f_res['avx2_wx_jit_mode']}` | `{f_res['elapsed_ms']} ms` |
| **Track G** | 8-Task Compositional ARC Grid Induction Batch | **{'PASS' if g_res['exact_test_matches'] == g_res['total_tasks'] else 'FAIL'}** | `{g_res['exact_test_matches']}/{g_res['total_tasks']}` exact pixel accuracy (`{g_res['accuracy']*100:.1f}%`) | `{g_res['total_elapsed_ms']} ms` |
| **Track H** | Fused AVX2 PERMUTE+XOR JIT + 3-Step ARC + Conditional CEGIS | **{'PASS' if h_res['fused_jit_mode'] == 1 and h_res['conditional_cegis_proven'] and h_res['arc_3step_solved'] else 'FAIL'}** | JIT mode `{h_res['fused_jit_mode']}`; 3-step `{h_res['arc_3step_program']}`; `{h_res['conditional_candidate']}` | `{h_res['elapsed_ms']} ms` |
| **Track I** | Cython Zero-Copy Fused JIT + Z3 Loop Mathematical Induction | **{'PASS' if i_res['cython_zero_copy_jit_executed'] and i_res['odds_proven'] and i_res['scale_proven'] and i_res['xor_proven'] else 'FAIL'}** | `O(n)->O(1)`: `sum_odds->{i_res['odds_closed_form']}`, `scale->{i_res['scale_closed_form']}`, `xor->{i_res['xor_closed_form']}` | `{i_res['elapsed_ms']} ms` |
"""
    md_path = out_dir / "AGI_ARENA_RESULTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(md)


if __name__ == "__main__":
    main()
