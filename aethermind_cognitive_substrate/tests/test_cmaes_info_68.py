"""Test Suite 40: Órgãos 67 e 68 - CMA-ES Black-Box Optimizer & Decentralized Information Filter.

Valida empiricamente:
1. SovereignCortexRuntime com >= 68 órgãos ativos;
2. Órgão 67: CMAESBlackBoxOptimizer convergindo na função não-convexa de Rosenbrock 4D
   (f_best < 1e-3, próximo de [1, 1, 1, 1]);
3. Órgão 68: DecentralizedInformationFilter fundindo M=3 sensores com comutatividade exata
   (erro < 1e-12) e ganho monotônico de informação de Fisher;
4. Despacho cognitivo das missões 'cmaes_minimize' e 'info_filter_fuse'.
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
from aethermind_cognitive_substrate.logic_symbolic.cma_es_evolution_optimizer import (
    CMAESBlackBoxOptimizer,
)
from aethermind_cognitive_substrate.planning.kalman_information_filter import (
    DecentralizedInformationFilter,
)


class TestCMAESAndInfoFilter68(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 67 e 68 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_68_organs(self):
        """Verifica se o córtex inicializou com >= 68 órgãos ativos."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 68)
        self.assertTrue(health.get("cmaes_blackbox_optimizer_active"))
        self.assertTrue(health.get("decentralized_information_filter_active"))

    def test_02_cmaes_rosenbrock_4d_convergence(self):
        """Valida convergência do CMA-ES em função não-convexa de Rosenbrock 4D."""
        cmaes = CMAESBlackBoxOptimizer(dim=4, sigma0=0.8, seed=202667)
        res = cmaes.minimize(x0=[0.0, 0.0, 0.0, 0.0], max_gens=250, tol=1e-6)
        self.assertEqual(res["status"], "CMAES_BLACKBOX_CONVERGED")
        self.assertLess(res["best_fitness"], 1e-3)
        self.assertTrue(np.allclose(res["best_x"], [1.0, 1.0, 1.0, 1.0], atol=0.1))

    def test_03_decentralized_information_filter_fusion(self):
        """Valida fusão multi-sensor aditiva, ganho de Fisher e comutatividade exata."""
        inf = DecentralizedInformationFilter(dt=0.1, seed=202668)
        res = inf.fuse_multisensor_stream(n_sensors=3, horizon=30)
        self.assertEqual(res["status"], "INFORMATION_FILTER_MULTISENSOR_FUSED")
        self.assertTrue(res["fisher_gain_verified"])
        self.assertLess(res["order_commutativity_error"], 1e-12)
        self.assertIsNotNone(res["position_rmse"])
        self.assertLess(res["position_rmse"], 0.35)

    def test_04_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'cmaes_minimize' e 'info_filter_fuse'."""
        c_res = self.cortex.execute_cognitive_mission("cmaes_minimize", {"max_gens": 200})
        self.assertEqual(c_res["mission_type"], "cmaes_minimize")
        self.assertEqual(c_res["result"]["status"], "CMAES_BLACKBOX_CONVERGED")
        self.assertLess(c_res["result"]["best_fitness"], 0.05)

        i_res = self.cortex.execute_cognitive_mission("info_filter_fuse", {"n_sensors": 4})
        self.assertEqual(i_res["mission_type"], "info_filter_fuse")
        self.assertEqual(i_res["result"]["status"], "INFORMATION_FILTER_MULTISENSOR_FUSED")
        self.assertTrue(i_res["result"]["fisher_gain_verified"])


if __name__ == "__main__":
    unittest.main()
