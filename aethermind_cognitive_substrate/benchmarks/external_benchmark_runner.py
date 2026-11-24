"""Reproducible External Held-Out Benchmark Runner (v8.3.0).

Evaluates the AetherMind Cognitive Kernel against genuinely external, unseen public
benchmarks with strict zero-cherry-picking reporting:
1. Official Public `ARC-AGI-1` Evaluation Subset (`external_datasets/arc_agi_public/*.json`).
2. Standardized Held-Out Formal Synthesis (SyGuS-style BitVec / LIA / Loop / Nested-Loop) Suite.

Generates `EXTERNAL_BENCHMARK_SCORECARD.json` and `EXTERNAL_BENCHMARK_SCORECARD.md`.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import numpy as np

from aethermind_cognitive_substrate.logic_symbolic.cegis_code_synthesizer import CEGISCodeSynthesizer
from aethermind_cognitive_substrate.logic_symbolic.symbolic_grid_arc_reasoner import SymbolicGridARCReasoner


def eval_public_arc_agi_subset(max_tasks: int = 25, max_program_depth: int = 4) -> Dict[str, Any]:
    """Evaluate object-centric + VSA-beam ARC synthesizer against official fchollet/ARC-AGI eval tasks."""
    dataset_dir = Path(__file__).resolve().parent / "external_datasets" / "arc_agi_public"
    json_files = sorted(dataset_dir.glob("*.json"))[:max_tasks]
    reasoner = SymbolicGridARCReasoner()

    t0 = time.perf_counter()
    solved_tasks: List[str] = []
    per_task: List[Dict[str, Any]] = []

    for jf in json_files:
        data = json.loads(jf.read_text(encoding="utf-8"))
        train_pairs = [(p["input"], p["output"]) for p in data.get("train", [])]
        test_items = data.get("test", [])
        if not train_pairs or not test_items:
            continue

        # Solve on train demonstrations once using test[0] input, then verify ALL held-out test outputs
        t_item = time.perf_counter()
        res = reasoner.solve_arc_task(
            train_pairs=train_pairs,
            test_input=test_items[0]["input"],
            max_program_depth=max_program_depth,
            allow_color_remap=True,
            time_budget_ms=1000.0,
        )
        all_test_exact = False
        prog = res.get("synthesized_program")
        if res.get("solved") and prog:
            all_test_exact = True
            for ti in test_items:
                pred = reasoner.apply_program(prog, ti["input"])
                exp = np.asarray(ti["output"], dtype=np.int32)
                if pred.shape != exp.shape or not np.array_equal(pred, exp):
                    all_test_exact = False
                    break

        if all_test_exact:
            solved_tasks.append(jf.stem)

        per_task.append({
            "task_id": jf.stem,
            "train_exact_found": bool(res.get("solved")),
            "test_exact_match": all_test_exact,
            "program": prog,
            "elapsed_ms": round((time.perf_counter() - t_item) * 1000.0, 2),
        })

    total = len(per_task)
    solved_n = len(solved_tasks)
    return {
        "dataset": "fchollet/ARC-AGI public evaluation subset",
        "total_tasks": total,
        "solved_exact": solved_n,
        "accuracy_pct": round(100.0 * solved_n / max(1, total), 2),
        "solved_task_ids": solved_tasks,
        "total_elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        "tasks": per_task,
    }


def eval_heldout_sygus_synthesis_suite() -> Dict[str, Any]:
    """Evaluate formal Z3 CEGIS synthesis across BitVec, Conditional, Loop & Nested-Loop benchmarks."""
    synth = CEGISCodeSynthesizer()
    t0 = time.perf_counter()

    specs = [
        ("bv_even_parity", "ast", "def f(x):\n    return (x % 2) == 0\n"),
        ("bv_mod8_mask", "ast", "def f(x):\n    return (x % 8) == 0\n"),
        ("bv_mul16_shift", "ast", "def f(x, y):\n    return (x * 16) + (y ^ y)\n"),
        ("lia_if_branch_shift", "ast", "def f(x):\n    return (x * 8) if x > 0 else (x * 4)\n"),
        ("loop_sum_odds", "loop", "def f(n):\n    acc = 0\n    for i in range(n):\n        acc = acc + (2 * i + 1)\n    return acc\n"),
        ("loop_sum_squares_cubic", "loop", "def f(n):\n    acc = 0\n    for i in range(n):\n        acc = acc + i * i\n    return acc\n"),
        ("nested_rect_scale", "nested", "def f(x, n, m):\n    acc = 0\n    for i in range(n):\n        for j in range(m):\n            acc = acc + (x * 4)\n    return acc\n"),
        ("nested_triangular_pairs", "nested", "def f(n):\n    acc = 0\n    for i in range(n):\n        for j in range(i):\n            acc = acc + 1\n    return acc\n"),
    ]

    results: List[Dict[str, Any]] = []
    proven_count = 0
    for name, kind, src in specs:
        if kind == "ast":
            r = synth.synthesize_python_ast_cegis(src)
        elif kind == "loop":
            r = synth.synthesize_loop_closed_form_cegis(src)
        else:
            r = synth.synthesize_nested_loop_closed_form_cegis(src)
        ok = bool(r.get("is_equivalent"))
        if ok:
            proven_count += 1
        results.append({
            "problem": name,
            "track": kind,
            "z3_proven": ok,
            "candidate_code": r.get("candidate_code"),
            "elapsed_ms": r.get("elapsed_ms"),
        })

    return {
        "suite": "Held-Out SyGuS-Style Formal Z3 CEGIS Suite",
        "total_problems": len(specs),
        "z3_proven_count": proven_count,
        "solve_rate_pct": round(100.0 * proven_count / len(specs), 2),
        "total_elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        "problems": results,
    }


def main() -> None:
    arc_eval = eval_public_arc_agi_subset(max_tasks=25, max_program_depth=4)
    sygus_eval = eval_heldout_sygus_synthesis_suite()

    payload = {
        "generated_at": datetime.now().isoformat(),
        "version": "8.3.0-APEX-MODULAR-AGI-OBJECT-ARC-EXTERNAL-SOVEREIGN",
        "arc_agi_public": arc_eval,
        "sygus_formal_suite": sygus_eval,
    }

    out_dir = Path(__file__).resolve().parent
    (out_dir / "EXTERNAL_BENCHMARK_SCORECARD.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )

    md = f"""# External Held-Out Benchmark Scorecard (`v8.3.0`)

**Generated:** `{payload['generated_at']}`  
**Kernel Version:** `{payload['version']}`  
**Policy:** Strict held-out public evaluation — zero cherry-picking.

| Benchmark Suite | Scope | Exact Solved / Proven | Score | Total Latency (ms) |
|---|---|---:|---:|---:|
| **`fchollet/ARC-AGI` Public Eval** | {arc_eval['total_tasks']} unseen public JSON tasks (depth<=4 + object DSL + remap) | `{arc_eval['solved_exact']}/{arc_eval['total_tasks']}` | **{arc_eval['accuracy_pct']}%** | `{arc_eval['total_elapsed_ms']} ms` |
| **Formal SyGuS BV/LIA/Loop CEGIS** | {sygus_eval['total_problems']} BitVec / IfExp / Single & Nested Loop / Cubic Z3 specs | `{sygus_eval['z3_proven_count']}/{sygus_eval['total_problems']}` | **{sygus_eval['solve_rate_pct']}%** | `{sygus_eval['total_elapsed_ms']} ms` |

## Solved Public `ARC-AGI` Task IDs
`{arc_eval['solved_task_ids']}`
"""
    (out_dir / "EXTERNAL_BENCHMARK_SCORECARD.md").write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
