"""Test Suite 38: Órgãos 63 e 64 - Spectral Graph Chebyshev Filter & Pontryagin iLQR Optimizer.

Valida empiricamente:
1. SovereignCortexRuntime com 64 órgãos ativos (v5.7.0-APEX-CHEB-ILQR-64-ORGANS-SOVEREIGN);
2. Órgão 63: SpectralGraphChebyshevEngine reduzindo a energia de Dirichlet x^T L_sym x
   via difusão térmica espectral exp(-t L_sym) sem autodecomposição;
3. Órgão 64: PontryaginILQROptimizer estabilizando o pêndulo invertido não-linear com redução
   monotônica de custo e erro terminal < 0.05;
4. Despacho cognitivo das missões 'chebyshev_graph_filter' e 'ilqr_optimize_trajectory'.
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
from aethermind_cognitive_substrate.logic_symbolic.spectral_graph_chebyshev import (
    SpectralGraphChebyshevEngine,
)
from aethermind_cognitive_substrate.planning.pontryagin_ilqr_trajectory_optimizer import (
    PontryaginILQROptimizer,
)


class TestChebAndILQR64(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 63 e 64 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_64_organs(self):
        """Verifica se o córtex inicializou com 64 órgãos ativos e status SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 64)
        self.assertTrue(health.get("spectral_graph_chebyshev_active"))
        self.assertTrue(health.get("pontryagin_ilqr_optimizer_active"))

    def test_02_spectral_chebyshev_dirichlet_smoothing(self):
        """Valida que a difusão térmica de Chebyshev atenua altas frequências no grafo."""
        cheb = SpectralGraphChebyshevEngine(cheb_order=10, diffusion_time=2.0)
        res = cheb.apply_chebyshev_filter()
        self.assertEqual(res["status"], "SPECTRAL_CHEBYSHEV_FILTER_APPLIED")
        self.assertTrue(res["smoothing_verified"])
        self.assertLess(res["dirichlet_energy_out"], res["dirichlet_energy_in"] * 0.2)

    def test_03_spectral_chebyshev_constant_signal_invariance(self):
        """Um sinal constante pertence ao núcleo de L_sym (lambda=0) e deve ser preservado."""
        cheb = SpectralGraphChebyshevEngine(cheb_order=8, diffusion_time=1.5)
        n = 6
        A = np.ones((n, n)) - np.eye(n)
        const_sig = np.full(n, 3.5)
        res = cheb.apply_chebyshev_filter(adjacency=A, signal=const_sig)
        self.assertLess(res["dirichlet_energy_in"], 1e-10)
        self.assertTrue(np.allclose(res["filtered_signal"], const_sig, atol=1e-4))

    def test_04_pontryagin_ilqr_inverted_pendulum_stabilization(self):
        """Valida estabilização não-linear do pêndulo invertido de theta=0.8 rad até 0."""
        ilqr = PontryaginILQROptimizer(dt=0.05, max_iters=30)
        res = ilqr.optimize_trajectory(x0=[0.8, 0.0], x_goal=[0.0, 0.0], horizon=40)
        self.assertEqual(res["status"], "ILQR_NONLINEAR_TRAJECTORY_OPTIMIZED")
        self.assertLess(res["final_cost"], res["initial_cost"])
        self.assertGreater(res["cost_reduction_ratio"], 5.0)
        self.assertLess(res["final_terminal_error"], 0.05)

    def test_05_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'chebyshev_graph_filter' e 'ilqr_optimize_trajectory'."""
        c_res = self.cortex.execute_cognitive_mission("chebyshev_graph_filter", {})
        self.assertEqual(c_res["mission_type"], "chebyshev_graph_filter")
        self.assertEqual(c_res["result"]["status"], "SPECTRAL_CHEBYSHEV_FILTER_APPLIED")
        self.assertTrue(c_res["result"]["smoothing_verified"])

        i_res = self.cortex.execute_cognitive_mission("ilqr_optimize_trajectory", {})
        self.assertEqual(i_res["mission_type"], "ilqr_optimize_trajectory")
        self.assertEqual(i_res["result"]["status"], "ILQR_NONLINEAR_TRAJECTORY_OPTIMIZED")
        self.assertLess(i_res["result"]["final_terminal_error"], 0.05)


if __name__ == "__main__":
    unittest.main()
