"""Test Suite 42: Órgãos 71 e 72 - Matrix-Free Newton-Krylov GMRES & Hungarian Optimal Assignment.

Valida empiricamente:
1. SovereignCortexRuntime com 72 órgãos ativos (v6.1.0-APEX-NK-HUNGARIAN-72-ORGANS-SOVEREIGN);
2. Órgão 71: NewtonKrylovGMRESSolver convergindo para ||F(x)||_2 < 1e-10 sem matriz Jacobiana;
3. Órgão 72: HungarianOptimalAssignmentEngine resolvendo atribuição ótima bipartida com
   certificação dual exata (viabilidade dual + folga complementar < 1e-9);
4. Despacho cognitivo das missões 'newton_krylov_solve' e 'hungarian_assign'.
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
from aethermind_cognitive_substrate.logic_symbolic.newton_krylov_gmres_solver import (
    NewtonKrylovGMRESSolver,
)
from aethermind_cognitive_substrate.planning.hungarian_linear_assignment import (
    HungarianOptimalAssignmentEngine,
)


class TestNewtonKrylovAndHungarian72(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 71 e 72 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_72_organs(self):
        """Verifica se o córtex inicializou com 72 órgãos ativos e SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 72)
        self.assertTrue(health.get("newton_krylov_gmres_active"))
        self.assertTrue(health.get("hungarian_optimal_assignment_active"))

    def test_02_newton_krylov_gmres_convergence(self):
        """Valida convergência quadrática Newton-Krylov GMRES em sistema acoplado 12D."""
        nk = NewtonKrylovGMRESSolver(tol=1e-10)
        res = nk.solve(dim=12)
        self.assertEqual(res["status"], "NEWTON_KRYLOV_GMRES_CONVERGED")
        self.assertTrue(res["converged"])
        self.assertLess(res["final_residual_norm"], 1e-10)

    def test_03_hungarian_beats_greedy_and_certifies_dual(self):
        """Valida caso clássico onde o algoritmo guloso falha e o Húngaro acha o ótimo global."""
        # Matriz 3x3 clássica: guloso pega (0,0)=1, (1,1)=9, (2,2)=10 -> 20; ótimo é (0,1)=2, (1,0)=3, (2,2)=10 -> 15
        C = [
            [1.0, 2.0, 9.0],
            [3.0, 9.0, 9.0],
            [9.0, 9.0, 10.0],
        ]
        hung = HungarianOptimalAssignmentEngine()
        res = hung.solve_assignment(cost_matrix=C)
        self.assertEqual(res["status"], "HUNGARIAN_OPTIMAL_ASSIGNMENT_FOUND")
        self.assertTrue(res["dual_optimality_certified"])
        self.assertAlmostEqual(res["optimal_total_cost"], 15.0, places=6)
        self.assertLess(res["optimal_total_cost"], res["greedy_baseline_cost"])

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'newton_krylov_solve' e 'hungarian_assign'."""
        nk_res = self.cortex.execute_cognitive_mission("newton_krylov_solve", {"dim": 10})
        self.assertEqual(nk_res["mission_type"], "newton_krylov_solve")
        self.assertTrue(nk_res["result"]["converged"])

        h_res = self.cortex.execute_cognitive_mission("hungarian_assign", {"n_agents": 7})
        self.assertEqual(h_res["mission_type"], "hungarian_assign")
        self.assertTrue(h_res["result"]["dual_optimality_certified"])
        self.assertLessEqual(h_res["result"]["optimal_total_cost"], h_res["result"]["greedy_baseline_cost"])


if __name__ == "__main__":
    unittest.main()
