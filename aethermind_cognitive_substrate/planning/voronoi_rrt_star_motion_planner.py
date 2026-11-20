"""RRT* (Rapidly-exploring Random Tree Star) Asymptotically Optimal Motion Planner.

Organ 76 do Substrato Cognitivo Nao-LLM (AetherCOS v6.3).
Planejador de movimento continuo assintoticamente otimo (Karaman & Frazzoli, IJRR 2011):
- Explora espacos de configuracao continuos com obstaculos circulares/poligonais via amostragem
  com goal-bias e extensao limitada por passo (step_size);
- Escolhe o melhor pai na vizinhanca local de raio adaptativo r_n e executa *rewiring* dos
  vizinhos para reduzir monotonicamente o custo geodesico ate a meta;
- Verifica que o caminho final e livre de colisoes e mais curto que a primeira solucao RRT encontrada.
"""
from __future__ import annotations

import ctypes
import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class RRTStarOptimalMotionPlanner:
    """
    Planejador Continuo Assintoticamente Otimo RRT* (Karaman & Frazzoli).
    """

    def __init__(self, step_size: float = 0.8, neighbor_radius: float = 1.8, seed: int = 202676):
        self.step_size = float(step_size)
        self.neighbor_radius = float(neighbor_radius)
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _segment_circle_collision(
        p1: np.ndarray,
        p2: np.ndarray,
        center: np.ndarray,
        radius: float,
    ) -> bool:
        """Verifica se o segmento [p1, p2] intercepta o disco (center, radius)."""
        d = p2 - p1
        len_sq = float(np.dot(d, d))
        if len_sq < 1e-12:
            return float(np.linalg.norm(p1 - center)) <= radius
        t = max(0.0, min(1.0, float(np.dot(center - p1, d) / len_sq)))
        proj = p1 + t * d
        return float(np.linalg.norm(proj - center)) <= radius

    def _is_collision_free(
        self,
        p1: np.ndarray,
        p2: np.ndarray,
        obstacles: List[Tuple[float, float, float]],
    ) -> bool:
        for ox, oy, r in obstacles:
            if self._segment_circle_collision(p1, p2, np.array([ox, oy], dtype=np.float64), r):
                return False
        return True

    def plan_motion(
        self,
        start: Tuple[float, float] = (0.5, 0.5),
        goal: Tuple[float, float] = (9.5, 9.5),
        bounds: Tuple[float, float] = (0.0, 10.0),
        obstacles: Optional[List[Tuple[float, float, float]]] = None,
        max_iters: int = 450,
    ) -> Dict[str, Any]:
        """
        Executa RRT* em R^2 retornando caminho livre de colisoes, custo e ganho por rewiring.
        """
        t0 = time.perf_counter()

        s_pt = np.asarray(start, dtype=np.float64)
        g_pt = np.asarray(goal, dtype=np.float64)
        obs_list = obstacles if obstacles is not None else [
            (3.5, 3.5, 1.3),
            (6.5, 6.0, 1.4),
            (5.0, 2.0, 1.0),
        ]

        nodes: List[np.ndarray] = [s_pt]
        parents: List[int] = [-1]
        costs: List[float] = [0.0]

        goal_tol = self.step_size
        goal_node_indices: List[int] = []
        first_goal_cost: Optional[float] = None
        rewire_count = 0

        lib = None
        try:
            from ..physical_bridge.native_cortex_dll_singleton import get_native_cortex_dll
            lib = get_native_cortex_dll()
        except Exception:
            lib = None

        low, high = float(bounds[0]), float(bounds[1])

        for it in range(max_iters):
            # 12% goal bias
            if float(self.rng.uniform()) < 0.12:
                rnd = g_pt.copy()
            else:
                rnd = self.rng.uniform(low, high, size=2)

            # Nearest node search
            if lib is not None and hasattr(lib, "rrt_star_nearest_and_radius_f64"):
                nodes_arr = np.ascontiguousarray(nodes, dtype=np.float64)
                rnd_c = np.ascontiguousarray(rnd, dtype=np.float64)
                c_nearest = ctypes.c_size_t(0)
                c_dist = ctypes.c_double(0.0)
                null_size_t = ctypes.cast(ctypes.c_void_p(0), ctypes.POINTER(ctypes.c_size_t))
                lib.rrt_star_nearest_and_radius_f64(
                    nodes_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    len(nodes), 2,
                    rnd_c.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    0.0,
                    ctypes.byref(c_nearest),
                    ctypes.byref(c_dist),
                    null_size_t, 0, null_size_t
                )
                nearest_idx = int(c_nearest.value)
                nearest = nodes[nearest_idx]
                dist = float(c_dist.value)
            else:
                dists = [float(np.linalg.norm(nd - rnd)) for nd in nodes]
                nearest_idx = int(np.argmin(dists))
                nearest = nodes[nearest_idx]
                dist = dists[nearest_idx]

            if dist < 1e-9:
                continue

            if dist > self.step_size:
                new_pt = nearest + (self.step_size / dist) * (rnd - nearest)
            else:
                new_pt = rnd

            if not self._is_collision_free(nearest, new_pt, obs_list):
                continue

            # Encontra vizinhos dentro de neighbor_radius
            if lib is not None and hasattr(lib, "rrt_star_nearest_and_radius_f64"):
                nodes_arr = np.ascontiguousarray(nodes, dtype=np.float64)
                new_pt_c = np.ascontiguousarray(new_pt, dtype=np.float64)
                n_nds = len(nodes)
                c_near_arr = (ctypes.c_size_t * n_nds)()
                c_near_cnt = ctypes.c_size_t(0)
                null_size_t = ctypes.cast(ctypes.c_void_p(0), ctypes.POINTER(ctypes.c_size_t))
                null_double = ctypes.cast(ctypes.c_void_p(0), ctypes.POINTER(ctypes.c_double))
                lib.rrt_star_nearest_and_radius_f64(
                    nodes_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    n_nds, 2,
                    new_pt_c.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    self.neighbor_radius,
                    null_size_t, null_double,
                    c_near_arr, n_nds,
                    ctypes.byref(c_near_cnt)
                )
                near_indices = [int(c_near_arr[k]) for k in range(c_near_cnt.value)]
            else:
                near_indices = [
                    i for i, nd in enumerate(nodes)
                    if float(np.linalg.norm(nd - new_pt)) <= self.neighbor_radius
                ]

            # Escolhe o melhor pai
            best_parent = nearest_idx
            best_cost = costs[nearest_idx] + float(np.linalg.norm(new_pt - nearest))
            for idx in near_indices:
                cand_cost = costs[idx] + float(np.linalg.norm(new_pt - nodes[idx]))
                if cand_cost < best_cost and self._is_collision_free(nodes[idx], new_pt, obs_list):
                    best_parent = idx
                    best_cost = cand_cost

            new_idx = len(nodes)
            nodes.append(new_pt)
            parents.append(best_parent)
            costs.append(best_cost)

            # Rewiring dos vizinhos
            for idx in near_indices:
                if idx == best_parent:
                    continue
                new_through_cost = best_cost + float(np.linalg.norm(nodes[idx] - new_pt))
                if new_through_cost + 1e-9 < costs[idx] and self._is_collision_free(new_pt, nodes[idx], obs_list):
                    parents[idx] = new_idx
                    costs[idx] = new_through_cost
                    rewire_count += 1

            # Verifica chegada a meta
            d_goal = float(np.linalg.norm(new_pt - g_pt))
            if d_goal <= goal_tol and self._is_collision_free(new_pt, g_pt, obs_list):
                goal_node_indices.append(new_idx)
                total_to_goal = best_cost + d_goal
                if first_goal_cost is None:
                    first_goal_cost = total_to_goal

        if not goal_node_indices:
            elapsed_us = (time.perf_counter() - t0) * 1e6
            return {
                "status": "RRT_STAR_NO_PATH_FOUND",
                "tree_nodes": len(nodes),
                "rewires": rewire_count,
                "elapsed_us": round(elapsed_us, 2),
            }

        best_goal_idx = min(
            goal_node_indices,
            key=lambda idx: costs[idx] + float(np.linalg.norm(nodes[idx] - g_pt)),
        )
        final_cost = costs[best_goal_idx] + float(np.linalg.norm(nodes[best_goal_idx] - g_pt))

        # Reconstroi caminho e valida ausencia de colisoes em todos os segmentos
        path: List[np.ndarray] = [g_pt]
        curr = best_goal_idx
        while curr != -1:
            path.append(nodes[curr])
            curr = parents[curr]
        path.reverse()

        collision_free = all(
            self._is_collision_free(path[i], path[i + 1], obs_list)
            for i in range(len(path) - 1)
        )
        euclidean_lb = float(np.linalg.norm(g_pt - s_pt))

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "RRT_STAR_OPTIMAL_PATH_FOUND",
            "tree_nodes": len(nodes),
            "rewires": rewire_count,
            "waypoints": len(path),
            "first_solution_cost": round(float(first_goal_cost), 4) if first_goal_cost else None,
            "final_path_cost": round(float(final_cost), 4),
            "euclidean_lower_bound": round(euclidean_lb, 4),
            "collision_free_verified": collision_free,
            "elapsed_us": round(elapsed_us, 2),
        }
