"""Test Suite 44: Órgãos 75 e 76 - Augmented Lagrangian (ALM) & RRT* Optimal Motion Planner.

Valida empiricamente:
1. SovereignCortexRuntime com 76 órgãos ativos (v6.3.0-APEX-ALM-RRTSTAR-76-ORGANS-SOVEREIGN);
2. Órgão 75: AugmentedLagrangianConstrainedSolver resolvendo otimização não-linear restrita
   com violação primal < 1e-6 e ótimo exato x*=[1.0, 1.0], f*=2.0;
3. Órgão 76: RRTStarOptimalMotionPlanner encontrando caminho livre de colisões em R^2
   com melhoria de custo via rewiring;
4. Despacho cognitivo das missões 'alm_constrained_opt' e 'rrt_star_motion'.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
import numpy as np

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime
from aethermind_cognitive_substrate.logic_symbolic.lagrangian_augmented_constrained_opt import (
    AugmentedLagrangianConstrainedSolver,
)
from aethermind_cognitive_substrate.planning.voronoi_rrt_star_motion_planner import (
    RRTStarOptimalMotionPlanner,
)


class TestALMAndRRTStar76(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 75 e 76 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_76_organs(self):
        """Verifica se o córtex inicializou com 76 órgãos ativos e SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 76)
        self.assertTrue(health.get("augmented_lagrangian_alm_active"))
        self.assertTrue(health.get("rrt_star_motion_planner_active"))

    def test_02_alm_constrained_exact_optimum(self):
        """Valida ALM com restrições de igualdade e desigualdade atingindo ótimo exato."""
        alm = AugmentedLagrangianConstrainedSolver(tol=1e-6, max_outer_iters=20)
        res = alm.solve_constrained()
        self.assertEqual(res["status"], "ALM_CONSTRAINED_OPTIMAL_CONVERGED")
        self.assertTrue(res["feasible"])
        self.assertLess(res["equality_violation"], 1e-6)
        self.assertLess(res["inequality_violation"], 1e-6)
        self.assertTrue(np.allclose(res["optimal_x"], [1.0, 1.0], atol=1e-4))
        self.assertAlmostEqual(res["optimal_objective"], 2.0, places=4)

    def test_03_rrt_star_collision_free_and_rewiring(self):
        """Valida planejamento contínuo RRT* livre de colisões com rewiring."""
        rrt = RRTStarOptimalMotionPlanner(step_size=0.8, neighbor_radius=1.8, seed=202676)
        res = rrt.plan_motion(max_iters=450)
        self.assertEqual(res["status"], "RRT_STAR_OPTIMAL_PATH_FOUND")
        self.assertTrue(res["collision_free_verified"])
        self.assertGreater(res["rewires"], 0)
        self.assertGreaterEqual(res["final_path_cost"], res["euclidean_lower_bound"])
        self.assertLessEqual(res["final_path_cost"], res["first_solution_cost"] + 1e-4)

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'alm_constrained_opt' e 'rrt_star_motion'."""
        a_res = self.cortex.execute_cognitive_mission("alm_constrained_opt", {})
        self.assertEqual(a_res["mission_type"], "alm_constrained_opt")
        self.assertTrue(a_res["result"]["feasible"])

        r_res = self.cortex.execute_cognitive_mission("rrt_star_motion", {"max_iters": 450})
        self.assertEqual(r_res["mission_type"], "rrt_star_motion")
        self.assertEqual(r_res["result"]["status"], "RRT_STAR_OPTIMAL_PATH_FOUND")
        self.assertTrue(r_res["result"]["collision_free_verified"])


if __name__ == "__main__":
    unittest.main()
