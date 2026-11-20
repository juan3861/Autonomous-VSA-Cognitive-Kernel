"""Test Suite 46: Órgãos 79 e 80 - FEM P1 Galerkin PDE Solver & CFR+ Imperfect-Info Game Solver.

Valida empiricamente:
1. SovereignCortexRuntime com >= 80 órgãos ativos;
2. Órgão 79: FiniteElementGalerkinSolver com convergência O(h^2) em malha refinada (32 -> 64 -> 128)
   e erro L2 < 1e-3;
3. Órgão 80: CounterfactualRegretCFRPlusSolver convergindo em Kuhn Poker para valor teórico
   -1/18 (-0.055556) com explorabilidade < 5e-3;
4. Despacho cognitivo das missões 'fem_galerkin_solve' e 'cfr_plus_kuhn'.
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
from aethermind_cognitive_substrate.logic_symbolic.fem_poisson_galerkin import (
    FiniteElementGalerkinSolver,
)
from aethermind_cognitive_substrate.planning.cfr_incomplete_info_solver import (
    CounterfactualRegretCFRPlusSolver,
)


class TestFEMAndCFRPlus80(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 79 e 80 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_80_organs(self):
        """Verifica se o córtex inicializou com >= 80 órgãos ativos."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 80)
        self.assertTrue(health.get("fem_galerkin_solver_active"))
        self.assertTrue(health.get("cfr_plus_imperfect_info_active"))

    def test_02_fem_p1_galerkin_quadratic_convergence(self):
        """Valida erro L2 < 1e-3 e taxa de convergência quadrática O(h^2) ao dobrar a malha."""
        fem = FiniteElementGalerkinSolver()
        r32 = fem.solve_elliptic_poisson(n_elements=32)
        r64 = fem.solve_elliptic_poisson(n_elements=64)
        self.assertEqual(r64["status"], "FEM_GALERKIN_P1_SOLVED")
        self.assertTrue(r64["galerkin_converged"])
        self.assertLess(r64["l2_error"], 1e-3)
        # Ao dobrar elementos (h -> h/2), erro L2 em P1 cai ~4x
        ratio = r32["l2_error"] / max(r64["l2_error"], 1e-15)
        self.assertGreater(ratio, 3.5)

    def test_03_cfr_plus_kuhn_poker_nash_convergence(self):
        """Valida CFR+ em Kuhn Poker convergindo para EV = -1/18 com baixa explorabilidade."""
        cfr = CounterfactualRegretCFRPlusSolver(n_iters=1500)
        res = cfr.solve_kuhn_poker()
        self.assertEqual(res["status"], "CFR_PLUS_EXTENSIVE_NASH_CONVERGED")
        self.assertTrue(res["nash_converged"])
        self.assertLess(res["exploitability"], 5e-3)
        self.assertLess(res["value_error_vs_exact"], 0.01)

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'fem_galerkin_solve' e 'cfr_plus_kuhn'."""
        f_res = self.cortex.execute_cognitive_mission("fem_galerkin_solve", {"n_elements": 64})
        self.assertEqual(f_res["mission_type"], "fem_galerkin_solve")
        self.assertTrue(f_res["result"]["galerkin_converged"])

        c_res = self.cortex.execute_cognitive_mission("cfr_plus_kuhn", {"n_iters": 1200})
        self.assertEqual(c_res["mission_type"], "cfr_plus_kuhn")
        self.assertTrue(c_res["result"]["nash_converged"])


if __name__ == "__main__":
    unittest.main()
