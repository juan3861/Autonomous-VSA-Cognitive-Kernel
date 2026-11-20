"""Test Suite 45: Órgãos 77 e 78 - Chebyshev Spectral BVP Solver & Zero-Sum Nash Minimax Solver.

Valida empiricamente:
1. SovereignCortexRuntime com 78 órgãos ativos (v6.4.0-APEX-CHEB-BVP-NASH-78-ORGANS-SOVEREIGN);
2. Órgão 77: ChebyshevSpectralBVPSolver atingindo precisão espectral (erro L_inf < 1e-10)
   com apenas N=16 nós de Chebyshev-Gauss-Lobatto;
3. Órgão 78: ZeroSumNashEquilibriumSolver (Regret Matching+) certificando o Teorema
   Minimax com gap de explorabilidade < 5e-3 e valor exato do jogo;
4. Despacho cognitivo das missões 'cheb_bvp_solve' e 'nash_minimax_solve'.
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
from aethermind_cognitive_substrate.logic_symbolic.chebyshev_collocation_bvp import (
    ChebyshevSpectralBVPSolver,
)
from aethermind_cognitive_substrate.planning.nash_minimax_equilibrium import (
    ZeroSumNashEquilibriumSolver,
)


class TestChebBVPAndNash78(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 77 e 78 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_78_organs(self):
        """Verifica se o córtex inicializou com 78 órgãos ativos e SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 78)
        self.assertTrue(health.get("chebyshev_spectral_bvp_active"))
        self.assertTrue(health.get("zero_sum_nash_minimax_active"))

    def test_02_chebyshev_spectral_bvp_exponential_precision(self):
        """Valida precisão espectral L_inf < 1e-10 com apenas 16 nós de Chebyshev."""
        bvp = ChebyshevSpectralBVPSolver(n_nodes=16)
        res = bvp.solve_bvp()
        self.assertEqual(res["status"], "CHEBYSHEV_SPECTRAL_BVP_SOLVED")
        self.assertTrue(res["spectral_precision_achieved"])
        self.assertLess(res["l_inf_error_vs_exact"], 1e-10)
        self.assertAlmostEqual(res["u_center_value"], 1.0, places=6)

    def test_03_nash_minimax_rock_paper_scissors_and_asymmetric(self):
        """Valida Teorema Minimax em RPS clássico (v*=0) e jogo assimétrico."""
        nash = ZeroSumNashEquilibriumSolver(n_iters=2500)
        # RPS clássico: estratégia ótima [1/3, 1/3, 1/3], v*=0
        A_rps = [[0, -1, 1], [1, 0, -1], [-1, 1, 0]]
        res_rps = nash.solve_minimax(payoff_matrix=A_rps)
        self.assertEqual(res_rps["status"], "NASH_MINIMAX_EQUILIBRIUM_CONVERGED")
        self.assertTrue(res_rps["minimax_certified"])
        self.assertAlmostEqual(res_rps["game_value"], 0.0, places=3)
        self.assertTrue(np.allclose(res_rps["row_player_strategy"], [1/3, 1/3, 1/3], atol=0.02))

        # Jogo assimétrico padrão
        res_asym = nash.solve_minimax()
        self.assertTrue(res_asym["minimax_certified"])
        self.assertLess(res_asym["exploitability_gap"], 5e-3)

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'cheb_bvp_solve' e 'nash_minimax_solve'."""
        b_res = self.cortex.execute_cognitive_mission("cheb_bvp_solve", {"n_nodes": 18})
        self.assertEqual(b_res["mission_type"], "cheb_bvp_solve")
        self.assertTrue(b_res["result"]["spectral_precision_achieved"])

        n_res = self.cortex.execute_cognitive_mission("nash_minimax_solve", {})
        self.assertEqual(n_res["mission_type"], "nash_minimax_solve")
        self.assertTrue(n_res["result"]["minimax_certified"])


if __name__ == "__main__":
    unittest.main()
