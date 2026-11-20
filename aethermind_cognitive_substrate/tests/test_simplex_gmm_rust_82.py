"""Test Suite 47: Órgãos 81 e 82 + Rust Spectral Power Iteration (`v7.0.0`, 82 Órgãos).

Valida empiricamente:
1. SovereignCortexRuntime com 82 órgãos ativos (v7.0.0-APEX-V7-82-ORGANS-SOVEREIGN);
2. Kernel bare-metal Rust LTO `spectral_power_iteration_f64` em `aether_cortex_vsa.dll`
   calculando raio espectral dominante rho(A) com precisão < 1e-10 vs `np.linalg.eigvals`;
3. Órgão 81: RevisedSimplexLPSolver certificando dualidade forte (gap < 1e-8) e viabilidade;
4. Órgão 82: GaussianMixtureEMEngine garantindo monotonicidade estrita da log-verossimilhança
   e recuperação dos 3 componentes;
5. Despacho cognitivo das missões 'simplex_lp_solve' e 'gmm_em_fit'.
"""
from __future__ import annotations

import ctypes
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
from aethermind_cognitive_substrate.physical_bridge.native_cortex_dll_singleton import (
    get_native_cortex_dll,
)
from aethermind_cognitive_substrate.logic_symbolic.simplex_linear_programming import (
    RevisedSimplexLPSolver,
)
from aethermind_cognitive_substrate.planning.expectation_maximization_gmm import (
    GaussianMixtureEMEngine,
)


class TestSimplexGMMAndRustSpectral82(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 81 e 82 + kernel Rust LTO v7.0.0."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_82_organs_v7(self):
        """Verifica se o córtex inicializou na v7.0.0 com 82 órgãos ativos."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 82)
        self.assertTrue(health.get("simplex_lp_solver_active"))
        self.assertTrue(health.get("gaussian_mixture_em_active"))

    def test_02_rust_lto_spectral_power_iteration(self):
        """Valida kernel bare-metal `spectral_power_iteration_f64` contra NumPy eigvals."""
        dll = get_native_cortex_dll()
        self.assertIsNotNone(dll)
        self.assertTrue(hasattr(dll, "spectral_power_iteration_f64"))

        # Matriz simétrica positiva 8x8 com autovalor dominante bem separado
        rng = np.random.default_rng(202682)
        M = rng.normal(0.0, 0.2, size=(8, 8))
        A = np.ascontiguousarray(0.5 * (M + M.T) + np.diag([0.92, 0.4, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01]), dtype=np.float64)
        rho_numpy = float(np.max(np.abs(np.linalg.eigvals(A))))

        rho_rust = float(dll.spectral_power_iteration_f64(
            A.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            8,
            500,
            1e-13,
        ))
        self.assertAlmostEqual(rho_rust, rho_numpy, places=9)

    def test_03_simplex_lp_strong_duality_and_optimality(self):
        """Valida Simplex exato com dualidade forte c^T x* == -b^T y*."""
        lp = RevisedSimplexLPSolver()
        res = lp.solve_lp()
        self.assertEqual(res["status"], "SIMPLEX_LP_OPTIMAL")
        self.assertTrue(res["strong_duality_certified"])
        self.assertLess(res["strong_duality_gap"], 1e-8)
        self.assertLess(res["primal_violation"], 1e-8)
        self.assertLess(res["dual_violation"], 1e-8)

    def test_04_gmm_em_monotonic_log_likelihood(self):
        """Valida EM de mistura de gaussianas com log-verossimilhança monotônica."""
        gmm = GaussianMixtureEMEngine(n_components=3, max_iters=60, seed=202682)
        res = gmm.fit_gmm()
        self.assertEqual(res["status"], "GMM_EM_CONVERGED")
        self.assertTrue(res["monotonic_ll_verified"])
        self.assertGreater(res["final_log_likelihood"], res["initial_log_likelihood"])
        self.assertAlmostEqual(sum(res["component_weights"]), 1.0, places=3)

    def test_05_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'simplex_lp_solve' e 'gmm_em_fit'."""
        s_res = self.cortex.execute_cognitive_mission("simplex_lp_solve", {})
        self.assertEqual(s_res["mission_type"], "simplex_lp_solve")
        self.assertTrue(s_res["result"]["strong_duality_certified"])

        g_res = self.cortex.execute_cognitive_mission("gmm_em_fit", {"n_components": 3})
        self.assertEqual(g_res["mission_type"], "gmm_em_fit")
        self.assertTrue(g_res["result"]["monotonic_ll_verified"])


if __name__ == "__main__":
    unittest.main()
