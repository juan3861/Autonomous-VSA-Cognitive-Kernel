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
from .z3_formal_solver import Z3_GLOBAL_LOCK


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


def extract_connected_objects(g: np.ndarray, connectivity: int = 4) -> List[Dict[str, Any]]:
    """Segment non-zero connected components into structured object descriptors."""
    arr = np.asarray(g, dtype=np.int32)
    h, w = arr.shape
    visited = np.zeros((h, w), dtype=bool)
    nbrs = ((-1, 0), (1, 0), (0, -1), (0, 1)) if connectivity == 4 else (
        (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)
    )
    objects: List[Dict[str, Any]] = []
    for r in range(h):
        for c in range(w):
            color = int(arr[r, c])
            if color == 0 or visited[r, c]:
                continue
            q = [(r, c)]
            visited[r, c] = True
            cells: List[Tuple[int, int]] = []
            head = 0
            while head < len(q):
                cr, cc = q[head]
                head += 1
                cells.append((cr, cc))
                for dr, dc in nbrs:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and not visited[nr, nc] and int(arr[nr, nc]) == color:
                        visited[nr, nc] = True
                        q.append((nr, nc))
            rs = [p[0] for p in cells]
            cs = [p[1] for p in cells]
            r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
            sub = np.zeros((r1 - r0 + 1, c1 - c0 + 1), dtype=arr.dtype)
            for cr, cc in cells:
                sub[cr - r0, cc - c0] = color
            objects.append({
                "color": color,
                "area": len(cells),
                "bbox": (r0, c0, r1, c1),
                "cells": cells,
                "subgrid": sub,
            })
    return objects


def _op_extract_largest_object(g: np.ndarray) -> np.ndarray:
    objs = extract_connected_objects(g, connectivity=4)
    if not objs:
        return g.copy()
    best = max(objs, key=lambda o: (o["area"], -o["bbox"][0], -o["bbox"][1]))
    return best["subgrid"]


def _op_extract_smallest_object(g: np.ndarray) -> np.ndarray:
    objs = extract_connected_objects(g, connectivity=4)
    if not objs:
        return g.copy()
    best = min(objs, key=lambda o: (o["area"], o["bbox"][0], o["bbox"][1]))
    return best["subgrid"]


def _op_keep_largest_object(g: np.ndarray) -> np.ndarray:
    objs = extract_connected_objects(g, connectivity=4)
    if not objs:
        return g.copy()
    best = max(objs, key=lambda o: (o["area"], -o["bbox"][0], -o["bbox"][1]))
    out = np.zeros_like(g)
    for r, c in best["cells"]:
        out[r, c] = best["color"]
    return out


def _op_filter_dominant_color(g: np.ndarray) -> np.ndarray:
    nz = g[g != 0]
    if nz.size == 0:
        return g.copy()
    vals, cnts = np.unique(nz, return_counts=True)
    dom = int(vals[int(np.argmax(cnts))])
    return np.where(g == dom, g, 0).astype(g.dtype)


def _op_complete_4way_symmetry(g: np.ndarray) -> np.ndarray:
    out = g.copy()
    fh = np.fliplr(g)
    fv = np.flipud(g)
    fhv = np.flipud(fh)
    for layer in (fh, fv, fhv):
        mask = (out == 0) & (layer != 0)
        out[mask] = layer[mask]
    return out


def _op_bridge_same_color_aligned(g: np.ndarray) -> np.ndarray:
    h, w = g.shape
    out = g.copy()
    for r in range(h):
        cols_by_color: Dict[int, List[int]] = {}
        for c in range(w):
            v = int(g[r, c])
            if v != 0:
                cols_by_color.setdefault(v, []).append(c)
        for v, cs in cols_by_color.items():
            if len(cs) >= 2:
                for c in range(cs[0], cs[-1] + 1):
                    if out[r, c] == 0:
                        out[r, c] = v
    for c in range(w):
        rows_by_color: Dict[int, List[int]] = {}
        for r in range(h):
            v = int(g[r, c])
            if v != 0:
                rows_by_color.setdefault(v, []).append(r)
        for v, rs in rows_by_color.items():
            if len(rs) >= 2:
                for r in range(rs[0], rs[-1] + 1):
                    if out[r, c] == 0:
                        out[r, c] = v
    return out


def _op_hollow_interior(g: np.ndarray) -> np.ndarray:
    return _op_outline_nonzero(g)


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
    "extract_largest_object": _op_extract_largest_object,
    "extract_smallest_object": _op_extract_smallest_object,
    "keep_largest_object": _op_keep_largest_object,
    "filter_dominant_color": _op_filter_dominant_color,
    "complete_4way_symmetry": _op_complete_4way_symmetry,
    "bridge_same_color_aligned": _op_bridge_same_color_aligned,
    "hollow_interior": _op_hollow_interior,
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
        with Z3_GLOBAL_LOCK:
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

    @staticmethod
    def _shape_compatible(op_name: str, in_sh: Tuple[int, int], out_sh: Tuple[int, int]) -> bool:
        if op_name in ("crop_nonzero", "extract_largest_object", "extract_smallest_object"):
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

    def solve_arc_task(
        self,
        train_pairs: Sequence[Tuple[GridLike, GridLike]],
        test_input: GridLike,
        max_program_depth: int = 2,
        allow_color_remap: bool = True,
        beam_width: int = 24,
        time_budget_ms: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Induce minimal spatial transform program from demonstrations and predict test grid."""
        t0 = time.perf_counter()
        deadline = (t0 + time_budget_ms / 1000.0) if time_budget_ms is not None else None
        pairs = [(np.asarray(i, dtype=np.int32), np.asarray(o, dtype=np.int32)) for i, o in train_pairs]
        test_arr = np.asarray(test_input, dtype=np.int32)

        def _timed_out() -> bool:
            return deadline is not None and time.perf_counter() > deadline

        def _grid_sig(st_pairs: List[Tuple[np.ndarray, np.ndarray]]) -> bytes:
            return b"|".join(f"{m.shape}:".encode() + m.tobytes() for m, _ in st_pairs)

        # Prioritization heuristic using shape & pixel count cues (remains exact via CEGIS test)
        same_shape_all = all(inp.shape == out.shape for inp, out in pairs)
        prim_names = list(_GRID_PRIMITIVES.keys())
        if not same_shape_all:
            # Prefer resizing operators first when shapes differ
            prim_names.sort(key=lambda n: 0 if n in ("crop_nonzero", "extract_largest_object", "extract_smallest_object", "mirror_concat_h", "scale_2x", "rot90", "rot270", "transpose") else 1)

        chosen_prog: Optional[List[str]] = None
        programs_evaluated = 0

        # Depth 1 search (with unique-state deduplication)
        depth1_states: List[Tuple[str, List[Tuple[np.ndarray, np.ndarray]]]] = []
        seen_d1: set[bytes] = set()
        for p1 in prim_names:
            programs_evaluated += 1
            m1_pairs: List[Tuple[np.ndarray, np.ndarray]] = []
            valid_1 = True
            exact_1 = True
            for inp, out in pairs:
                m = self.apply_program([p1], inp)
                if m.size == 0:
                    valid_1 = False
                    exact_1 = False
                    break
                if not np.array_equal(m, out):
                    exact_1 = False
                m1_pairs.append((m, out))
            if exact_1:
                chosen_prog = [p1]
                break
            if valid_1 and max_program_depth >= 2:
                sig1 = _grid_sig(m1_pairs)
                if sig1 not in seen_d1:
                    seen_d1.add(sig1)
                    depth1_states.append((p1, m1_pairs))

        # Depth 2 compositional search (deduplicated)
        depth2_states: List[Tuple[str, str, List[Tuple[np.ndarray, np.ndarray]]]] = []
        seen_d2: set[bytes] = set(seen_d1)
        if chosen_prog is None and max_program_depth >= 2:
            for p1, mid_pairs in depth1_states:
                if _timed_out():
                    break
                m1_0, out_0 = mid_pairs[0]
                for p2 in prim_names:
                    if p1 == p2 and p1 in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero", "extract_largest_object", "extract_smallest_object", "keep_largest_object"):
                        continue
                    programs_evaluated += 1
                    fn2 = _GRID_PRIMITIVES[p2]
                    m2_0 = fn2(m1_0)
                    if m2_0.size == 0:
                        continue
                    if m2_0.shape == out_0.shape and np.array_equal(m2_0, out_0):
                        if all(np.array_equal(fn2(m), o) for m, o in mid_pairs[1:]):
                            chosen_prog = [p1, p2]
                            break
                    if max_program_depth >= 3:
                        mid2_pairs = [(m2_0, out_0)]
                        valid_m2 = True
                        for m, o in mid_pairs[1:]:
                            mv = fn2(m)
                            if mv.size == 0:
                                valid_m2 = False
                                break
                            mid2_pairs.append((mv, o))
                        if valid_m2:
                            sig2 = _grid_sig(mid2_pairs)
                            if sig2 not in seen_d2:
                                seen_d2.add(sig2)
                                depth2_states.append((p1, p2, mid2_pairs))
                if chosen_prog is not None:
                    break

        # Depth 3 shape-pruned & deduplicated compositional search
        depth3_states: List[Tuple[str, str, str, List[Tuple[np.ndarray, np.ndarray]]]] = []
        seen_d3: set[bytes] = set(seen_d2)
        if chosen_prog is None and max_program_depth >= 3 and not _timed_out():
            for p1, p2, m2_pairs in depth2_states:
                if _timed_out():
                    break
                m2_0, out_0 = m2_pairs[0]
                for p3 in prim_names:
                    if p2 == p3 and p2 in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero", "extract_largest_object", "extract_smallest_object", "keep_largest_object"):
                        continue
                    if max_program_depth == 3 and not self._shape_compatible(p3, m2_0.shape, out_0.shape):
                        continue
                    programs_evaluated += 1
                    fn3 = _GRID_PRIMITIVES[p3]
                    m3_0 = fn3(m2_0)
                    if m3_0.size == 0:
                        continue
                    if m3_0.shape == out_0.shape and np.array_equal(m3_0, out_0):
                        if all(np.array_equal(fn3(m2), out) for m2, out in m2_pairs[1:]):
                            chosen_prog = [p1, p2, p3]
                            break
                    if max_program_depth >= 4:
                        if max_program_depth == 4 and not any(self._shape_compatible(p4, m3_0.shape, out_0.shape) for p4 in prim_names):
                            continue
                        m3_pairs = [(m3_0, out_0)]
                        ok_m3 = True
                        for m2, out in m2_pairs[1:]:
                            mv = fn3(m2)
                            if mv.size == 0:
                                ok_m3 = False
                                break
                            m3_pairs.append((mv, out))
                        if ok_m3:
                            sig3 = _grid_sig(m3_pairs)
                            if sig3 not in seen_d3:
                                seen_d3.add(sig3)
                                depth3_states.append((p1, p2, p3, m3_pairs))
                if chosen_prog is not None:
                    break

        # Depth 4 spatial composition &/or learned color-remap synthesis
        if chosen_prog is None and max_program_depth >= 4 and not _timed_out():
            # 1) Pure shape-compatible 4-op spatial pipeline
            for p1, p2, p3, m3_pairs in depth3_states:
                if _timed_out():
                    break
                m3_0, out_0 = m3_pairs[0]
                for p4 in prim_names:
                    if p3 == p4 and p3 in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero", "extract_largest_object", "extract_smallest_object", "keep_largest_object"):
                        continue
                    if not self._shape_compatible(p4, m3_0.shape, out_0.shape):
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
            if chosen_prog is None and allow_color_remap and not _timed_out():
                candidates_for_remap: List[Tuple[List[str], List[Tuple[np.ndarray, np.ndarray]]]] = [
                    ([], pairs),
                ]
                for p1, m1_pairs in depth1_states:
                    candidates_for_remap.append(([p1], m1_pairs))
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

        # Depth 5..6 VSA/Structural Beam Search (v8.3.0)
        if chosen_prog is None and max_program_depth >= 5 and depth3_states:
            target_hvs = [self.encode_grid_vsa(out) for _inp, out in pairs]

            def _beam_score(st_pairs: List[Tuple[np.ndarray, np.ndarray]]) -> float:
                score = 0.0
                for idx_p, (m, out) in enumerate(st_pairs):
                    if m.shape == out.shape:
                        score += 1.0 + float(np.mean(m == out))
                    elif abs(m.shape[0] - out.shape[0]) <= 2 and abs(m.shape[1] - out.shape[1]) <= 2:
                        score += 0.35
                    m_hv = self.encode_grid_vsa(m)
                    score += 0.25 * float(self.bus.vsa.cosine_similarity(m_hv, target_hvs[idx_p]))
                return score / max(1, len(st_pairs))

            # Seed beam with unique depth-3 states expanded by 1 shape-compatible or top-beam op
            scored_d3 = sorted(
                ((_beam_score(m3p), [p1, p2, p3], m3p) for p1, p2, p3, m3p in depth3_states),
                key=lambda x: x[0],
                reverse=True,
            )[:max(8, beam_width)]

            frontier: List[Tuple[List[str], List[Tuple[np.ndarray, np.ndarray]]]] = [
                (prog, m3p) for _sc, prog, m3p in scored_d3
            ]
            for depth in range(4, min(max_program_depth, 6) + 1):
                next_beam: List[Tuple[float, List[str], List[Tuple[np.ndarray, np.ndarray]]]] = []
                seen_sigs: set[bytes] = set()
                for prog, cur_pairs in frontier:
                    last_op = prog[-1]
                    for nxt_op in prim_names:
                        if nxt_op == last_op and nxt_op in ("flip_h", "flip_v", "transpose", "rot180", "crop_nonzero", "extract_largest_object", "keep_largest_object"):
                            continue
                        if depth == max_program_depth and not self._shape_compatible(nxt_op, cur_pairs[0][0].shape, cur_pairs[0][1].shape):
                            continue
                        programs_evaluated += 1
                        fn_n = _GRID_PRIMITIVES[nxt_op]
                        nxt_pairs = []
                        exact_all = True
                        valid_n = True
                        for m, out in cur_pairs:
                            nm = fn_n(m)
                            if nm.size == 0:
                                valid_n = False
                                break
                            if not np.array_equal(nm, out):
                                exact_all = False
                            nxt_pairs.append((nm, out))
                        if not valid_n:
                            continue
                        if exact_all:
                            chosen_prog = [*prog, nxt_op]
                            break
                        if allow_color_remap and all(nm.shape == out.shape for nm, out in nxt_pairs):
                            cmap = self._infer_consistent_color_map(nxt_pairs)
                            if cmap is not None:
                                remap_op = f"color_remap:{json.dumps({str(k): v for k, v in sorted(cmap.items())}, separators=(',', ':'))}"
                                if all(np.array_equal(self.apply_program([remap_op], nm), out) for nm, out in nxt_pairs):
                                    chosen_prog = [*prog, nxt_op, remap_op]
                                    break
                        sig = nxt_pairs[0][0].tobytes() + str(nxt_pairs[0][0].shape).encode()
                        if sig not in seen_sigs:
                            seen_sigs.add(sig)
                            next_beam.append((_beam_score(nxt_pairs), [*prog, nxt_op], nxt_pairs))
                    if chosen_prog is not None:
                        break
                if chosen_prog is not None or not next_beam:
                    break
                next_beam.sort(key=lambda x: x[0], reverse=True)
                frontier = [(p, pr) for _sc, p, pr in next_beam[:beam_width]]

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
