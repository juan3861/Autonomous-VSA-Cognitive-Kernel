"""Test Suite 43: Órgãos 73 e 74 - Levenberg-Marquardt NLLS & D* Lite Dynamic Replanner.

Valida empiricamente:
1. SovereignCortexRuntime com 74 órgãos ativos (v6.2.0-APEX-LM-DSTAR-74-ORGANS-SOVEREIGN);
2. Órgão 73: LevenbergMarquardtNLLSSolver recuperando parâmetros não-lineares com erro < 0.05;
3. Órgão 74: DStarLiteDynamicPlanner replanejando incrementalmente após obstáculos dinâmicos
   com comprimento idêntico ao A* de referência (optimal_match_verified=True);
4. Despacho cognitivo das missões 'lm_nlls_fit' e 'dstar_lite_replan'.
"""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

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
from aethermind_cognitive_substrate.logic_symbolic.gauss_newton_bundle_adjustment import (
    LevenbergMarquardtNLLSSolver,
)
from aethermind_cognitive_substrate.planning.a_star_anytime_dstar_lite import (
    DStarLiteDynamicPlanner,
)


class TestLMAndDStarLite74(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 73 e 74 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_74_organs(self):
        """Verifica se o córtex inicializou com 74 órgãos ativos e SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 74)
        self.assertTrue(health.get("levenberg_marquardt_nlls_active"))
        self.assertTrue(health.get("dstar_lite_dynamic_planner_active"))

    def test_02_levenberg_marquardt_nlls_recovery(self):
        """Valida recuperação de parâmetros exponenciais não-lineares com Levenberg-Marquardt."""
        lm = LevenbergMarquardtNLLSSolver(tol=1e-10, max_iters=50, seed=202673)
        res = lm.fit_nonlinear()
        self.assertEqual(res["status"], "LEVENBERG_MARQUARDT_NLLS_CONVERGED")
        self.assertGreater(res["cost_reduction_ratio"], 50.0)
        self.assertLess(res["param_error_vs_true"], 0.05)

    def test_03_dstar_lite_dynamic_replanning_matches_astar(self):
        """Valida que o D* Lite replaneja com otimalidade idêntica ao A* após novos obstáculos."""
        ds = DStarLiteDynamicPlanner(rows=12, cols=12)
        res = ds.plan_with_dynamic_obstacles()
        self.assertEqual(res["status"], "DSTAR_LITE_REPLAN_CONVERGED")
        self.assertTrue(res["optimal_match_verified"])
        self.assertEqual(res["replanned_remaining_length"], res["astar_reference_length"])

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'lm_nlls_fit' e 'dstar_lite_replan'."""
        l_res = self.cortex.execute_cognitive_mission("lm_nlls_fit", {})
        self.assertEqual(l_res["mission_type"], "lm_nlls_fit")
        self.assertEqual(l_res["result"]["status"], "LEVENBERG_MARQUARDT_NLLS_CONVERGED")
        self.assertLess(l_res["result"]["param_error_vs_true"], 0.05)

        d_res = self.cortex.execute_cognitive_mission("dstar_lite_replan", {"rows": 14, "cols": 14})
        self.assertEqual(d_res["mission_type"], "dstar_lite_replan")
        self.assertTrue(d_res["result"]["optimal_match_verified"])


if __name__ == "__main__":
    unittest.main()
