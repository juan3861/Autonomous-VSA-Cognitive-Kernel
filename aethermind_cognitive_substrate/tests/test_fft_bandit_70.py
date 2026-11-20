"""Test Suite 41: Órgãos 69 e 70 - FFT Spectral PDE Solver & Contextual Bandit (LinUCB / Thompson).

Valida empiricamente:
1. SovereignCortexRuntime com 70 órgãos ativos (v6.0.0-APEX-V6-70-ORGANS-SOVEREIGN);
2. Órgão 69: FFTSpectralPDESolver resolvendo advecção-difusão com erro de massa < 1e-12,
   identidade de Parseval < 1e-12 e conservação exata de energia em advecção pura (nu=0);
3. Órgão 70: ContextualBanditLinUCBThompson (LinUCB + Thompson Sampling) com melhoria
   empírica de acerto ótimo e arrependimento médio sublinear;
4. Despacho cognitivo das missões 'fft_spectral_pde' e 'contextual_bandit_run'.
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
from aethermind_cognitive_substrate.logic_symbolic.fft_spectral_pde_solver import (
    FFTSpectralPDESolver,
)
from aethermind_cognitive_substrate.planning.bandit_thompson_linucb import (
    ContextualBanditLinUCBThompson,
)


class TestFFTPDEAndBandit70(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 69 e 70 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_70_organs(self):
        """Verifica se o córtex inicializou com 70 órgãos ativos (v6.0.0) e SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 70)
        self.assertTrue(health.get("fft_spectral_pde_solver_active"))
        self.assertTrue(health.get("contextual_bandit_linucb_active"))

    def test_02_fft_spectral_pde_conservation_and_parseval(self):
        """Valida conservação de massa, identidade de Parseval e decaimento dissipativo."""
        pde = FFTSpectralPDESolver(n_grid=128, advection_c=1.0, viscosity_nu=0.05)
        res = pde.solve_advection_diffusion(t_final=1.0)
        self.assertEqual(res["status"], "FFT_SPECTRAL_PDE_SOLVED")
        self.assertLess(res["mass_conservation_error"], 1e-12)
        self.assertLess(res["parseval_identity_error"], 1e-12)
        self.assertTrue(res["dissipative_decay_verified"])
        self.assertLess(res["l2_energy_final"], res["l2_energy_initial"])

        # Advecção pura (nu=0) deve conservar energia L2 exatamente
        res_adv = pde.solve_advection_diffusion(t_final=1.5, viscosity_nu=0.0)
        self.assertAlmostEqual(res_adv["l2_energy_initial"], res_adv["l2_energy_final"], places=8)

    def test_03_contextual_bandit_linucb_and_thompson(self):
        """Valida aprendizado online LinUCB e Thompson Sampling com Sherman-Morrison."""
        bandit = ContextualBanditLinUCBThompson(n_arms=4, context_dim=5, alpha=1.0, seed=202670)
        res_ucb = bandit.simulate_contextual_bandit(n_rounds=300, policy="linucb")
        self.assertEqual(res_ucb["status"], "CONTEXTUAL_BANDIT_SIMULATED")
        self.assertTrue(res_ucb["learning_verified"])
        self.assertGreater(res_ucb["late_optimal_arm_rate"], 0.70)

        res_ts = bandit.simulate_contextual_bandit(n_rounds=300, policy="thompson")
        self.assertTrue(res_ts["learning_verified"])
        self.assertGreater(res_ts["late_optimal_arm_rate"], 0.65)

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'fft_spectral_pde' e 'contextual_bandit_run'."""
        f_res = self.cortex.execute_cognitive_mission("fft_spectral_pde", {"t_final": 0.5})
        self.assertEqual(f_res["mission_type"], "fft_spectral_pde")
        self.assertEqual(f_res["result"]["status"], "FFT_SPECTRAL_PDE_SOLVED")
        self.assertLess(f_res["result"]["parseval_identity_error"], 1e-12)

        b_res = self.cortex.execute_cognitive_mission("contextual_bandit_run", {"n_rounds": 250})
        self.assertEqual(b_res["mission_type"], "contextual_bandit_run")
        self.assertEqual(b_res["result"]["status"], "CONTEXTUAL_BANDIT_SIMULATED")
        self.assertTrue(b_res["result"]["learning_verified"])


if __name__ == "__main__":
    unittest.main()
