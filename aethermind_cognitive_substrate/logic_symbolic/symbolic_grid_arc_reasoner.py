"""Symbolic ARC-Style Abstract Spatial Grid Reasoner (VSA + CEGIS + Z3).

Area 09/10 Extension (v7.5.0): Encodes 2D integer grids holographically onto
10,240-bit VSA space and induces compositional 1-op / 2-op spatial transformation
programs verified pixel-for-pixel across few-shot demonstrations plus Z3 dimension
and non-zero occupancy invariants.
"""
from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
import z3

from ..memory_vault.vsa_semantic_bus import VSAHyperdimensionalBus


GridLike = Sequence[Sequence[int]]


def _op_rot90(g: np.ndarray) -> np.ndarray:
    return np.rot90(g, k=1)


def _op_rot180(g: np.ndarray) -> np.ndarray:
    return np.rot90(g, k=2)


def _op_rot270(g: np.ndarray) -> np.ndarray:
    return np.rot90(g, k=3)


def _op_flip_h(g: np.ndarray) -> np.ndarray:
    return np.fliplr(g)


def _op_flip_v(g: np.ndarray) -> np.ndarray:
    return np.flipud(g)


def _op_transpose(g: np.ndarray) -> np.ndarray:
    return g.T


def _op_crop_nonzero(g: np.ndarray) -> np.ndarray:
    nz = np.argwhere(g != 0)
    if nz.size == 0:
        return g.copy()
    r0, c0 = nz.min(axis=0)
    r1, c1 = nz.max(axis=0)
    return g[r0 : r1 + 1, c0 : c1 + 1]


def _op_gravity_down(g: np.ndarray) -> np.ndarray:
    out = np.zeros_like(g)
    h, w = g.shape
    for c in range(w):
        nz = g[:, c][g[:, c] != 0]
        if len(nz) > 0:
            out[h - len(nz) :, c] = nz
    return out


def _op_mirror_concat_h(g: np.ndarray) -> np.ndarray:
    return np.hstack([g, np.fliplr(g)])


def _op_mirror_concat_v(g: np.ndarray) -> np.ndarray:
    return np.vstack([g, np.flipud(g)])


def _op_gravity_left(g: np.ndarray) -> np.ndarray:
    out = np.zeros_like(g)
    h, _w = g.shape
    for r in range(h):
        nz = g[r, :][g[r, :] != 0]
        if len(nz) > 0:
            out[r, : len(nz)] = nz
    return out


def _op_tile_2x2(g: np.ndarray) -> np.ndarray:
    return np.tile(g, (2, 2))


def _op_fill_enclosed_zeros(g: np.ndarray) -> np.ndarray:
    """Fill 0-cells disconnected from grid boundary using the dominant non-zero color."""
    h, w = g.shape
    nz_vals = g[g != 0]
    if nz_vals.size == 0 or h < 3 or w < 3:
        return g.copy()
    vals, counts = np.unique(nz_vals, return_counts=True)
    fill_color = int(vals[int(np.argmax(counts))])

    visited = np.zeros((h, w), dtype=bool)
    queue: List[Tuple[int, int]] = []
    for r in range(h):
        for c in (0, w - 1):
            if g[r, c] == 0 and not visited[r, c]:
                visited[r, c] = True
                queue.append((r, c))
    for c in range(w):
        for r in (0, h - 1):
            if g[r, c] == 0 and not visited[r, c]:
                visited[r, c] = True
                queue.append((r, c))

    head = 0
    while head < len(queue):
        r, c = queue[head]
        head += 1
        for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
            if 0 <= nr < h and 0 <= nc < w and g[nr, nc] == 0 and not visited[nr, nc]:
                visited[nr, nc] = True
                queue.append((nr, nc))

    out = g.copy()
    out[(g == 0) & (~visited)] = fill_color
    return out


def _op_scale_2x(g: np.ndarray) -> np.ndarray:
    return np.kron(g, np.ones((2, 2), dtype=g.dtype))


def _op_invert_nonzero_color(g: np.ndarray) -> np.ndarray:
    mx = int(np.max(g))
    if mx <= 0:
        return g.copy()
    return np.where(g > 0, (mx + 1) - g, 0).astype(g.dtype)


def _op_outline_nonzero(g: np.ndarray) -> np.ndarray:
    h, w = g.shape
    out = np.zeros_like(g)
    for r in range(h):
        for c in range(w):
            if g[r, c] != 0:
                is_edge = (r == 0 or r == h - 1 or c == 0 or c == w - 1)
                if not is_edge:
                    nbrs = (g[r - 1, c], g[r + 1, c], g[r, c - 1], g[r, c + 1])
                    is_edge = any(n == 0 for n in nbrs)
                if is_edge:
                    out[r, c] = g[r, c]
    return out


_GRID_PRIMITIVES: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "rot90": _op_rot90,
    "rot180": _op_rot180,
    "rot270": _op_rot270,
    "flip_h": _op_flip_h,
    "flip_v": _op_flip_v,
    "transpose": _op_transpose,
    "crop_nonzero": _op_crop_nonzero,
    "gravity_down": _op_gravity_down,
    "gravity_left": _op_gravity_left,
    "mirror_concat_h": _op_mirror_concat_h,
    "mirror_concat_v": _op_mirror_concat_v,
    "tile_2x2": _op_tile_2x2,
    "scale_2x": _op_scale_2x,
    "invert_nonzero_color": _op_invert_nonzero_color,
    "outline_nonzero": _op_outline_nonzero,
    "fill_enclosed_zeros": _op_fill_enclosed_zeros,
}


class SymbolicGridARCReasoner:
    """Few-shot ARC-style abstract grid program synthesizer verified with Z3 + VSA."""

    def __init__(self, bus: Optional[VSAHyperdimensionalBus] = None):
        self.bus = bus or VSAHyperdimensionalBus(dimension=10240, seed=505)

    def encode_grid_vsa(self, grid: GridLike) -> np.ndarray:
        """Encode a 2D integer grid into a 10,240-bit holographic spatial hypervector."""
        arr = np.asarray(grid, dtype=np.int32)
        h, w = arr.shape
        vsa = self.bus.vsa
        bound_cells: List[np.ndarray] = []
        for r in range(h):
            r_vec = vsa.permute(vsa.register_symbol("arc_row"), shift=r + 1)
            for c in range(w):
                c_vec = vsa.permute(vsa.register_symbol("arc_col"), shift=(c + 1) * 17)
                val_vec = vsa.register_symbol(f"arc_color_{int(arr[r, c])}")
                bound_cells.append(vsa.bind(vsa.bind(r_vec, c_vec), val_vec))
        return vsa.bundle(bound_cells)

    def apply_program(self, program: List[str], grid: GridLike) -> np.ndarray:
        cur = np.asarray(grid, dtype=np.int32).copy()
        for op_name in program:
            if op_name.startswith("color_remap:"):
                raw_map = json.loads(op_name[len("color_remap:"):])
                cmap = {int(k): int(v) for k, v in raw_map.items()}
                nxt = cur.copy()
                for src_c, dst_c in cmap.items():
                    nxt[cur == src_c] = dst_c
                cur = nxt
                continue
            fn = _GRID_PRIMITIVES.get(op_name)
            if fn is None:
                raise KeyError(f"Unknown ARC grid primitive: {op_name}")
            cur = fn(cur)
        return np.ascontiguousarray(cur, dtype=np.int32)

    @staticmethod
    def _infer_consistent_color_map(pairs: List[Tuple[np.ndarray, np.ndarray]]) -> Optional[Dict[int, int]]:
        """Learn an exact per-color substitution map when all demo shapes already match."""
        cmap: Dict[int, int] = {}
        for m, out in pairs:
            if m.shape != out.shape:
                return None
            # Fast unique pair scan
            stacked = np.stack([m.ravel(), out.ravel()], axis=1)
            uniq_pairs = np.unique(stacked, axis=0)
            for s_val, d_val in uniq_pairs:
                si, di = int(s_val), int(d_val)
                if si in cmap and cmap[si] != di:
                    return None
                cmap[si] = di
        if not cmap or all(k == v for k, v in cmap.items()):
            return None
        return cmap

    def verify_program_z3(
        self,
        program: List[str],
        train_pairs: List[Tuple[np.ndarray, np.ndarray]],
    ) -> Dict[str, Any]:
        """Prove dimensional consistency and non-zero pixel invariants across all training demos in Z3."""
        solver = z3.Solver()
        all_exact = True
        for idx, (inp, exp_out) in enumerate(train_pairs):
            pred = self.apply_program(program, inp)
            if pred.shape != exp_out.shape or not np.array_equal(pred, exp_out):
                all_exact = False
                break
            h_p = z3.Int(f"demo_{idx}_pred_h")
            h_e = z3.Int(f"demo_{idx}_exp_h")
            w_p = z3.Int(f"demo_{idx}_pred_w")
            w_e = z3.Int(f"demo_{idx}_exp_w")
            nz_p = z3.Int(f"demo_{idx}_pred_nz")
            nz_e = z3.Int(f"demo_{idx}_exp_nz")
            solver.add(h_p == pred.shape[0], h_e == exp_out.shape[0], h_p == h_e)
            solver.add(w_p == pred.shape[1], w_e == exp_out.shape[1], w_p == w_e)
            solver.add(nz_p == int(np.count_nonzero(pred)), nz_e == int(np.count_nonzero(exp_out)), nz_p == nz_e)

        exact_bool = z3.Bool("all_train_pixels_exact")
        solver.add(exact_bool == z3.BoolVal(all_exact))
        solver.add(exact_bool == True)
        sat_ok = (solver.check() == z3.sat)
        return {"z3_verified": sat_ok, "sat_status": "sat" if sat_ok else "unsat", "program": program}

    def solve_arc_task(
        self,
        train_pairs: Sequence[Tuple[GridLike, GridLike]],
        test_input: GridLike,
        max_program_depth: int = 2,
        allow_color_remap: bool = True,
    ) -> Dict[str, Any]:
        """Induce minimal spatial transform program from demonstrations and predict test grid."""
        t0 = time.perf_counter()
        pairs = [(np.asarray(i, dtype=np.int32), np.asarray(o, dtype=np.int32)) for i, o in train_pairs]
        test_arr = np.asarray(test_input, dtype=np.int32)

        # Prioritization heuristic using shape & pixel count cues (remains exact via CEGIS test)
        same_shape_all = all(inp.shape == out.shape for inp, out in pairs)
        prim_names = list(_GRID_PRIMITIVES.keys())
        if not same_shape_all:
            # Prefer resizing operators first when shapes differ
            prim_names.sort(key=lambda n: 0 if n in ("crop_nonzero", "mirror_concat_h", "scale_2x", "rot90", "rot270", "transpose") else 1)

        chosen_prog: Optional[List[str]] = None
        programs_evaluated = 0

        # Depth 1 search
        for p1 in prim_names:
            programs_evaluated += 1
            if all(
                np.array_equal(self.apply_program([p1], inp), out)
                for inp, out in pairs
            ):
                chosen_prog = [p1]
                break

        # Depth 2 compositional search
        depth2_states: List[Tuple[str, str, List[Tuple[np.ndarray, np.ndarray]]]] = []
        if chosen_prog is None and max_program_depth >= 2:
            for p1 in prim_names:
                mid_pairs = []
                valid_mid = True
                for inp, out in pairs:
                    m = self.apply_program([p1], inp)
                    if m.size == 0:
                        valid_mid = False
                        break
                    mid_pairs.append((m, out))
                if not valid_mid:
                    continue
                for p2 in prim_names:
                    if p1 == p2 and p1 in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero"):
                        continue
                    programs_evaluated += 1
                    mid2_pairs = []
                    all_match_d2 = True
                    valid_m2 = True
                    for mid, out in mid_pairs:
                        m2 = _GRID_PRIMITIVES[p2](mid)
                        if m2.size == 0:
                            valid_m2 = False
                            all_match_d2 = False
                            break
                        if not np.array_equal(m2, out):
                            all_match_d2 = False
                        if max_program_depth >= 3:
                            mid2_pairs.append((m2, out))
                    if all_match_d2:
                        chosen_prog = [p1, p2]
                        break
                    if valid_m2 and max_program_depth >= 3:
                        depth2_states.append((p1, p2, mid2_pairs))
                if chosen_prog is not None:
                    break

        # Depth 3 shape-pruned compositional search
        depth3_states: List[Tuple[str, str, str, List[Tuple[np.ndarray, np.ndarray]]]] = []
        if chosen_prog is None and max_program_depth >= 3:
            def _shape_compatible(op_name: str, in_sh: Tuple[int, int], out_sh: Tuple[int, int]) -> bool:
                if op_name == "crop_nonzero":
                    return in_sh[0] >= out_sh[0] and in_sh[1] >= out_sh[1]
                if op_name in ("rot90", "rot270", "transpose"):
                    return (in_sh[1], in_sh[0]) == out_sh
                if op_name == "mirror_concat_h":
                    return (in_sh[0], in_sh[1] * 2) == out_sh
                if op_name == "mirror_concat_v":
                    return (in_sh[0] * 2, in_sh[1]) == out_sh
                if op_name in ("scale_2x", "tile_2x2"):
                    return (in_sh[0] * 2, in_sh[1] * 2) == out_sh
                return in_sh == out_sh

            for p1, p2, m2_pairs in depth2_states:
                m2_0, out_0 = m2_pairs[0]
                for p3 in prim_names:
                    if p2 == p3 and p2 in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero"):
                        continue
                    if max_program_depth == 3 and not _shape_compatible(p3, m2_0.shape, out_0.shape):
                        continue
                    programs_evaluated += 1
                    fn3 = _GRID_PRIMITIVES[p3]
                    m3_0 = fn3(m2_0)
                    if m3_0.size == 0:
                        continue
                    if _shape_compatible("identity_chk", m3_0.shape, out_0.shape) and np.array_equal(m3_0, out_0):
                        if all(np.array_equal(fn3(m2), out) for m2, out in m2_pairs[1:]):
                            chosen_prog = [p1, p2, p3]
                            break
                    if max_program_depth >= 4:
                        m3_pairs = [(m3_0, out_0)]
                        ok_m3 = True
                        for m2, out in m2_pairs[1:]:
                            mv = fn3(m2)
                            if mv.size == 0:
                                ok_m3 = False
                                break
                            m3_pairs.append((mv, out))
                        if ok_m3:
                            depth3_states.append((p1, p2, p3, m3_pairs))
                if chosen_prog is not None:
                    break

        # Depth 4 spatial composition &/or learned color-remap synthesis
        if chosen_prog is None and max_program_depth >= 4:
            # 1) Pure shape-compatible 4-op spatial pipeline
            for p1, p2, p3, m3_pairs in depth3_states:
                m3_0, out_0 = m3_pairs[0]
                for p4 in prim_names:
                    if p3 == p4 and p3 in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero"):
                        continue
                    if p4 == "crop_nonzero" and not (m3_0.shape[0] >= out_0.shape[0] and m3_0.shape[1] >= out_0.shape[1]):
                        continue
                    elif p4 in ("rot90", "rot270", "transpose") and (m3_0.shape[1], m3_0.shape[0]) != out_0.shape:
                        continue
                    elif p4 == "mirror_concat_h" and (m3_0.shape[0], m3_0.shape[1] * 2) != out_0.shape:
                        continue
                    elif p4 == "mirror_concat_v" and (m3_0.shape[0] * 2, m3_0.shape[1]) != out_0.shape:
                        continue
                    elif p4 in ("scale_2x", "tile_2x2") and (m3_0.shape[0] * 2, m3_0.shape[1] * 2) != out_0.shape:
                        continue
                    elif p4 not in ("crop_nonzero", "rot90", "rot270", "transpose", "mirror_concat_h", "mirror_concat_v", "scale_2x", "tile_2x2") and m3_0.shape != out_0.shape:
                        continue
                    programs_evaluated += 1
                    fn4 = _GRID_PRIMITIVES[p4]
                    if not np.array_equal(fn4(m3_0), out_0):
                        continue
                    if all(np.array_equal(fn4(m3), out) for m3, out in m3_pairs[1:]):
                        chosen_prog = [p1, p2, p3, p4]
                        break
                if chosen_prog is not None:
                    break

            # 2) Depth <=3 spatial transform + learned bijective/consistent palette remap
            if chosen_prog is None and allow_color_remap:
                candidates_for_remap: List[Tuple[List[str], List[Tuple[np.ndarray, np.ndarray]]]] = [
                    ([], pairs),
                ]
                for p1 in prim_names:
                    candidates_for_remap.append(([p1], [(self.apply_program([p1], i), o) for i, o in pairs]))
                for p1, p2, m2_pairs in depth2_states:
                    candidates_for_remap.append(([p1, p2], m2_pairs))
                for p1, p2, p3, m3_pairs in depth3_states:
                    candidates_for_remap.append(([p1, p2, p3], m3_pairs))

                for base_prog, cur_pairs in candidates_for_remap:
                    if not all(m.shape == o.shape for m, o in cur_pairs):
                        continue
                    programs_evaluated += 1
                    cmap = self._infer_consistent_color_map(cur_pairs)
                    if cmap is not None:
                        remap_op = f"color_remap:{json.dumps({str(k): v for k, v in sorted(cmap.items())}, separators=(',', ':'))}"
                        cand = [*base_prog, remap_op]
                        if all(np.array_equal(self.apply_program([remap_op], m), o) for m, o in cur_pairs):
                            chosen_prog = cand
                            break

        if chosen_prog is None:
            return {
                "solved": False,
                "status": "NO_PROGRAM_FOUND",
                "programs_evaluated": programs_evaluated,
                "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
            }

        z3_proof = self.verify_program_z3(chosen_prog, pairs)
        pred_test = self.apply_program(chosen_prog, test_arr)
        vsa_in_hv = self.encode_grid_vsa(test_arr)
        vsa_out_hv = self.encode_grid_vsa(pred_test)
        vsa_shift_sim = self.bus.vsa.cosine_similarity(vsa_in_hv, vsa_out_hv)

        self.bus.publish(
            topic="perception.arc_grid_synthesis",
            payload={
                "program": chosen_prog,
                "z3_verified": z3_proof["z3_verified"],
                "out_shape": list(pred_test.shape),
                "programs_evaluated": programs_evaluated,
            },
            organ_id="grid_arc_reasoner",
            confidence=1.0 if z3_proof["z3_verified"] else 0.0,
        )

        return {
            "solved": bool(z3_proof["z3_verified"]),
            "status": "ARC_PROGRAM_SYNTHESIZED",
            "synthesized_program": chosen_prog,
            "predicted_grid": pred_test.tolist(),
            "predicted_shape": list(pred_test.shape),
            "programs_evaluated": programs_evaluated,
            "z3_proof": z3_proof,
            "vsa_input_output_cosine": round(float(vsa_shift_sim), 4),
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    def evaluate_benchmark_batch(self, tasks: Sequence[Dict[str, Any]], max_program_depth: int = 2) -> Dict[str, Any]:
        """Evaluate a batch of held-out multi-step ARC puzzles against exact pixel ground truth."""
        t0 = time.perf_counter()
        results: List[Dict[str, Any]] = []
        solved_count = 0
        exact_test_matches = 0

        for task in tasks:
            res = self.solve_arc_task(
                train_pairs=task["train_pairs"],
                test_input=task["test_input"],
                max_program_depth=max_program_depth,
            )
            solved = bool(res.get("solved"))
            expected = task.get("expected_output")
            exact_match = False
            if solved and expected is not None:
                exact_match = np.array_equal(
                    np.asarray(res["predicted_grid"], dtype=np.int32),
                    np.asarray(expected, dtype=np.int32),
                )
            if solved:
                solved_count += 1
            if exact_match:
                exact_test_matches += 1
            results.append({
                "task_id": task.get("task_id", f"arc_{len(results)}"),
                "solved": solved,
                "exact_test_match": exact_match,
                "program": res.get("synthesized_program"),
                "elapsed_ms": res.get("elapsed_ms", 0.0),
            })

        total = len(tasks)
        return {
            "total_tasks": total,
            "solved_count": solved_count,
            "exact_test_matches": exact_test_matches,
            "accuracy": round(exact_test_matches / max(1, total), 4),
            "total_elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
            "task_results": results,
        }
