"""Test Suite 37: Órgãos 61 e 62 - Sparse Dictionary K-SVD (OMP) & Rauch-Tung-Striebel (RTS) Smoother.

Valida empiricamente:
1. SovereignCortexRuntime com 62 órgãos ativos (v5.6.0-APEX-KSVD-RTS-62-ORGANS-SOVEREIGN);
2. Órgão 61: SparseDictionaryKSVDEngine com codificação esparsa OMP exata e aprendizado K-SVD;
3. Órgão 62: RauchTungStriebelSmoother com redução monotônica da covariância Tr(P_{t|T}) <= Tr(P_{t|t})
   e redução de RMSE sobre o filtro causal de Kalman;
4. Despacho cognitivo das missões 'ksvd_sparse_coding' e 'rts_smooth_trajectory'.
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
from aethermind_cognitive_substrate.logic_symbolic.sparse_dictionary_ksvd import (
    SparseDictionaryKSVDEngine,
)
from aethermind_cognitive_substrate.planning.kalman_rts_smoother import (
    RauchTungStriebelSmoother,
)


class TestKSVDAndRTS62(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 61 e 62 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_62_organs(self):
        """Verifica se o córtex inicializou com 62 órgãos ativos e status SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 62)
        self.assertTrue(health.get("sparse_dictionary_ksvd_active"))
        self.assertTrue(health.get("kalman_rts_smoother_active"))

    def test_02_omp_exact_recovery_on_orthonormal_basis(self):
        """Valida recuperação esparsa exata via OMP em dicionário ortonormal."""
        ksvd = SparseDictionaryKSVDEngine(n_atoms=8, sparsity_k=2, seed=42)
        D = np.eye(8, dtype=np.float64)
        X_true = np.zeros((8, 5), dtype=np.float64)
        X_true[1, 0], X_true[5, 0] = 3.2, -1.7
        X_true[0, 1], X_true[7, 1] = -2.5, 4.1
        X_true[3, 2], X_true[4, 2] = 1.9, 2.3
        X_true[2, 3], X_true[6, 3] = -0.8, 1.4
        X_true[0, 4], X_true[3, 4] = 5.0, -3.3

        Y = D @ X_true
        X_rec = ksvd.omp_encode(Y, D, sparsity_k=2)
        max_err = float(np.max(np.abs(X_rec - X_true)))
        self.assertLess(max_err, 1e-10)

    def test_03_ksvd_dictionary_learning_snr_and_sparsity(self):
        """Valida aprendizado de dicionário supercompleto K-SVD sobre sinais 2-esparsos."""
        ksvd = SparseDictionaryKSVDEngine(n_atoms=14, sparsity_k=3, n_iters=15, seed=202661)
        res = ksvd.fit_and_encode()
        self.assertEqual(res["status"], "KSVD_SPARSE_DICTIONARY_LEARNED")
        self.assertLessEqual(res["mean_l0_sparsity"], 3.0)
        self.assertGreater(res["snr_db"], 20.0)
        self.assertLess(res["reconstruction_rmse"], 0.08)
        self.assertGreater(res["mutual_coherence"], 0.0)
        self.assertLess(res["mutual_coherence"], 1.0)

    def test_04_rts_smoother_covariance_and_rmse_reduction(self):
        """Valida redução monotônica de covariância Tr(P_{t|T}) <= Tr(P_{t|t}) e melhora de RMSE."""
        rts = RauchTungStriebelSmoother(dt=0.1, seed=202662)
        res = rts.smooth_trajectory()
        self.assertEqual(res["status"], "RTS_OPTIMAL_TRAJECTORY_SMOOTHED")
        self.assertTrue(res["covariance_reduction_verified"])
        self.assertLess(res["mean_smoothed_cov_trace"], res["mean_filtered_cov_trace"])
        self.assertIsNotNone(res["filtered_rmse"])
        self.assertIsNotNone(res["smoothed_rmse"])
        self.assertLessEqual(res["smoothed_rmse"], res["filtered_rmse"])

    def test_05_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'ksvd_sparse_coding' e 'rts_smooth_trajectory'."""
        k_res = self.cortex.execute_cognitive_mission("ksvd_sparse_coding", {})
        self.assertEqual(k_res["mission_type"], "ksvd_sparse_coding")
        self.assertEqual(k_res["result"]["status"], "KSVD_SPARSE_DICTIONARY_LEARNED")

        r_res = self.cortex.execute_cognitive_mission("rts_smooth_trajectory", {})
        self.assertEqual(r_res["mission_type"], "rts_smooth_trajectory")
        self.assertEqual(r_res["result"]["status"], "RTS_OPTIMAL_TRAJECTORY_SMOOTHED")
        self.assertTrue(r_res["result"]["covariance_reduction_verified"])


if __name__ == "__main__":
    unittest.main()
