"""Test Suite 39: Órgãos 65 e 66 - HJB Value Iteration MDP Solver & Hamiltonian Monte Carlo (HMC).

Valida empiricamente:
1. SovereignCortexRuntime com 66 órgãos ativos (v5.8.0-APEX-HJB-HMC-66-ORGANS-SOVEREIGN);
2. Órgão 65: HJBValueIterationMDPEngine com contração estrita de Banach ||V_{k+1}-V_k|| <= gamma ||V_k-V_{k-1}||
   e resíduo de Bellman < 1e-7;
3. Órgão 66: HamiltonianMonteCarloSampler com integrador simplético Leapfrog, taxa de aceitação >= 0.70
   e recuperação da média da gaussiana correlacionada (rho=0.85);
4. Despacho cognitivo das missões 'hjb_solve_mdp' e 'hmc_sample_posterior'.
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
from aethermind_cognitive_substrate.logic_symbolic.hjb_value_iteration_mdp import (
    HJBValueIterationMDPEngine,
)
from aethermind_cognitive_substrate.planning.hamiltonian_hmc_sampler import (
    HamiltonianMonteCarloSampler,
)


class TestHJBAndHMC66(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 65 e 66 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_66_organs(self):
        """Verifica se o córtex inicializou com 66 órgãos ativos e status SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 66)
        self.assertTrue(health.get("hjb_value_iteration_mdp_active"))
        self.assertTrue(health.get("hamiltonian_hmc_sampler_active"))

    def test_02_hjb_value_iteration_banach_contraction(self):
        """Valida convergência da equação de Bellman e contração de Banach no Gridworld 4x4."""
        hjb = HJBValueIterationMDPEngine(gamma=0.95, tol=1e-8)
        res = hjb.solve_mdp()
        self.assertEqual(res["status"], "HJB_MDP_OPTIMAL_VALUE_CONVERGED")
        self.assertTrue(res["banach_contraction_verified"])
        self.assertLess(res["bellman_residual"], 1e-7)
        self.assertGreater(res["v_start"], 4.0)
        self.assertEqual(len(res["optimal_policy"]), 16)

    def test_03_hjb_custom_2_state_analytical_mdp(self):
        """Valida valor exato em MDP analítico de 2 estados."""
        # Estado 0 -> Ação 0 fica em 0 (r=1), Ação 1 vai para 1 (r=5); Estado 1 é absorvente (r=0)
        P = np.zeros((2, 2, 2), dtype=np.float64)
        P[0, 0, 0] = 1.0
        P[0, 1, 1] = 1.0
        P[1, :, 1] = 1.0
        R = np.array([[1.0, 5.0], [0.0, 0.0]], dtype=np.float64)

        hjb = HJBValueIterationMDPEngine(gamma=0.9, tol=1e-10)
        res = hjb.solve_mdp(transitions=P, rewards=R)
        # V*(0) = max(1/(1-0.9)=10, 5) = 10 -> ação ótima em 0 é 0
        self.assertEqual(res["optimal_policy"][0], 0)
        self.assertAlmostEqual(res["v_start"], 10.0, places=5)

    def test_04_hmc_symplectic_correlated_gaussian(self):
        """Valida amostragem HMC em gaussiana correlacionada (rho=0.85) com alta aceitação."""
        hmc = HamiltonianMonteCarloSampler(step_size=0.12, n_leapfrog=12, seed=202666)
        res = hmc.sample_posterior(n_samples=400, burn_in=80)
        self.assertEqual(res["status"], "HMC_SYMPLECTIC_POSTERIOR_SAMPLED")
        self.assertGreater(res["acceptance_rate"], 0.75)
        self.assertLess(res["mean_error_vs_exact"], 0.25)
        self.assertGreater(res["ess_dim0"], 50.0)

    def test_05_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'hjb_solve_mdp' e 'hmc_sample_posterior'."""
        h_res = self.cortex.execute_cognitive_mission("hjb_solve_mdp", {})
        self.assertEqual(h_res["mission_type"], "hjb_solve_mdp")
        self.assertEqual(h_res["result"]["status"], "HJB_MDP_OPTIMAL_VALUE_CONVERGED")
        self.assertTrue(h_res["result"]["banach_contraction_verified"])

        m_res = self.cortex.execute_cognitive_mission("hmc_sample_posterior", {"n_samples": 200})
        self.assertEqual(m_res["mission_type"], "hmc_sample_posterior")
        self.assertEqual(m_res["result"]["status"], "HMC_SYMPLECTIC_POSTERIOR_SAMPLED")
        self.assertGreater(m_res["result"]["acceptance_rate"], 0.70)


if __name__ == "__main__":
    unittest.main()
