"""D* Lite Incremental Dynamic Heuristic Replanning Engine.

Organ 74 do Substrato Cognitivo Nao-LLM (AetherCOS v6.2).
Algoritmo D* Lite (Koenig & Likhachev, AAAI 2002) para replanejamento incremental de caminho
minimo em ambientes dinamicos com obstaculos descobertos em tempo real:
- Mantem valores g(s) e one-step lookahead rhs(s) com busca reversa do destino ao inicio;
- Utiliza fila de prioridade com chave lexicografica (k1, k2) e deslocamento incremental k_m;
- Quando novos obstaculos surgem no mapa durante a navegacao, atualiza apenas os nos afetados
  (propagacao local) sem recalcular o grafo inteiro do zero;
- Verifica otimalidade do caminho replanejado contra A* completo e mede economia de expansoes.
"""
from __future__ import annotations

import heapq
import time
from typing import Dict, Any, List, Optional, Set, Tuple


GridPos = Tuple[int, int]
INF = float("inf")


class DStarLiteDynamicPlanner:
    """
    Planejador Incremental Dinamico D* Lite (Koenig & Likhachev).
    """

    def __init__(self, rows: int = 12, cols: int = 12):
        self.rows = int(rows)
        self.cols = int(cols)

    @staticmethod
    def _heuristic(a: GridPos, b: GridPos) -> float:
        """Distancia Manhattan admissivel."""
        return float(abs(a[0] - b[0]) + abs(a[1] - b[1]))

    def _neighbors(self, s: GridPos, rows: int, cols: int) -> List[GridPos]:
        res = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = s[0] + dr, s[1] + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                res.append((nr, nc))
        return res

    @staticmethod
    def _astar_length(
        start: GridPos,
        goal: GridPos,
        obstacles: Set[GridPos],
        rows: int,
        cols: int,
    ) -> Optional[int]:
        """A* completo de referencia para certificar otimalidade do caminho replanejado."""
        pq: List[Tuple[float, int, GridPos]] = [(abs(start[0] - goal[0]) + abs(start[1] - goal[1]), 0, start)]
        best_g: Dict[GridPos, int] = {start: 0}
        while pq:
            _, g, u = heapq.heappop(pq)
            if u == goal:
                return g
            if g > best_g.get(u, 10 ** 9):
                continue
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                v = (u[0] + dr, u[1] + dc)
                if 0 <= v[0] < rows and 0 <= v[1] < cols and v not in obstacles:
                    ng = g + 1
                    if ng < best_g.get(v, 10 ** 9):
                        best_g[v] = ng
                        h = abs(v[0] - goal[0]) + abs(v[1] - goal[1])
                        heapq.heappush(pq, (ng + h, ng, v))
        return None

    def plan_with_dynamic_obstacles(
        self,
        rows: Optional[int] = None,
        cols: Optional[int] = None,
        start: GridPos = (0, 0),
        goal: Optional[GridPos] = None,
        initial_obstacles: Optional[List[GridPos]] = None,
        dynamic_obstacles: Optional[List[GridPos]] = None,
    ) -> Dict[str, Any]:
        """
        Planeja caminho inicial start -> goal, injeta obstaculos dinamicos no meio do trajeto
        e replaneja incrementalmente via D* Lite.
        """
        t0 = time.perf_counter()

        R = int(rows if rows is not None else self.rows)
        C = int(cols if cols is not None else self.cols)
        s_start = tuple(start)
        s_goal = tuple(goal if goal is not None else (R - 1, C - 1))

        obs: Set[GridPos] = set(tuple(p) for p in (initial_obstacles or [(3, r) for r in range(1, R - 2)]))
        if dynamic_obstacles is None:
            dyn_obs: List[GridPos] = [(1, 1), (1, 2), (2, 2), (5, 5), (5, 6), (6, 5)]
        else:
            dyn_obs = [tuple(p) for p in dynamic_obstacles]
        # Nunca bloquear start ou goal
        obs.discard(s_start)
        obs.discard(s_goal)
        dyn_obs = [p for p in dyn_obs if p != s_start and p != s_goal]

        g: Dict[GridPos, float] = {}
        rhs: Dict[GridPos, float] = {}
        for r in range(R):
            for c in range(C):
                g[(r, c)] = INF
                rhs[(r, c)] = INF
        rhs[s_goal] = 0.0

        k_m = 0.0
        s_curr = s_start
        pq: List[Tuple[Tuple[float, float], GridPos]] = []
        in_pq: Dict[GridPos, Tuple[float, float]] = {}

        def calc_key(s: GridPos) -> Tuple[float, float]:
            m = min(g[s], rhs[s])
            return (m + self._heuristic(s_curr, s) + k_m, m)

        def push_pq(s: GridPos, key: Tuple[float, float]):
            in_pq[s] = key
            heapq.heappush(pq, (key, s))

        def pop_valid() -> Optional[Tuple[Tuple[float, float], GridPos]]:
            while pq:
                k, s = heapq.heappop(pq)
                if in_pq.get(s) == k:
                    del in_pq[s]
                    return k, s
            return None

        def peek_key() -> Tuple[float, float]:
            while pq:
                k, s = pq[0]
                if in_pq.get(s) == k:
                    return k
                heapq.heappop(pq)
            return (INF, INF)

        def edge_cost(u: GridPos, v: GridPos) -> float:
            if u in obs or v in obs:
                return INF
            return 1.0

        def update_vertex(u: GridPos):
            if u != s_goal:
                if u in obs:
                    rhs[u] = INF
                else:
                    rhs[u] = min(edge_cost(u, s_p) + g[s_p] for s_p in self._neighbors(u, R, C))
            if u in in_pq:
                del in_pq[u]
            if abs(g[u] - rhs[u]) > 1e-12:
                push_pq(u, calc_key(u))

        def compute_shortest_path() -> int:
            expansions = 0
            while peek_key() < calc_key(s_curr) or abs(rhs[s_curr] - g[s_curr]) > 1e-12:
                k_old = peek_key()
                popped = pop_valid()
                if popped is None:
                    break
                _, u = popped
                expansions += 1
                k_new = calc_key(u)
                if k_old < k_new:
                    push_pq(u, k_new)
                elif g[u] > rhs[u]:
                    g[u] = rhs[u]
                    for s_p in self._neighbors(u, R, C):
                        update_vertex(s_p)
                else:
                    g[u] = INF
                    update_vertex(u)
                    for s_p in self._neighbors(u, R, C):
                        update_vertex(s_p)
            return expansions

        push_pq(s_goal, calc_key(s_goal))
        init_expansions = compute_shortest_path()
        init_cost = g[s_start]

        # Simula 2 passos do agente e descoberta de obstaculos dinamicos
        s_last = s_curr
        steps_moved = 0
        for _ in range(2):
            if s_curr == s_goal or g[s_curr] == INF:
                break
            nbrs = self._neighbors(s_curr, R, C)
            s_next = min(nbrs, key=lambda v: edge_cost(s_curr, v) + g[v])
            if edge_cost(s_curr, s_next) + g[s_next] >= INF:
                break
            s_curr = s_next
            steps_moved += 1

        # Injeta obstaculos dinamicos e atualiza vertices afetados
        k_m += self._heuristic(s_last, s_curr)
        s_last = s_curr
        changed = False
        for d_obs in dyn_obs:
            if d_obs != s_curr and d_obs not in obs:
                obs.add(d_obs)
                changed = True
                update_vertex(d_obs)
                for nbr in self._neighbors(d_obs, R, C):
                    update_vertex(nbr)

        replan_expansions = compute_shortest_path() if changed else 0

        # Extrai caminho restante de s_curr ate s_goal
        path: List[GridPos] = [s_curr]
        walker = s_curr
        for _ in range(R * C):
            if walker == s_goal:
                break
            nbrs = self._neighbors(walker, R, C)
            nxt = min(nbrs, key=lambda v: edge_cost(walker, v) + g[v])
            if edge_cost(walker, nxt) + g[nxt] >= INF or nxt in path:
                break
            path.append(nxt)
            walker = nxt

        reached_goal = (path[-1] == s_goal)
        replan_len = len(path) - 1 if reached_goal else None
        astar_ref_len = self._astar_length(s_curr, s_goal, obs, R, C)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "DSTAR_LITE_REPLAN_CONVERGED" if reached_goal else "DSTAR_LITE_BLOCKED",
            "grid_shape": [R, C],
            "initial_path_cost": init_cost if init_cost < INF else None,
            "initial_expansions": init_expansions,
            "steps_moved_before_replan": steps_moved,
            "dynamic_obstacles_added": len(dyn_obs),
            "replan_expansions": replan_expansions,
            "replanned_remaining_length": replan_len,
            "astar_reference_length": astar_ref_len,
            "optimal_match_verified": (replan_len == astar_ref_len) and (replan_len is not None),
            "elapsed_us": round(elapsed_us, 2),
        }
