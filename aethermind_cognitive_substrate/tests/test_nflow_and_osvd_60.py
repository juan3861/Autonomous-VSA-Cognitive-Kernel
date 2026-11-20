"""Test Suite 36: Órgãos 59 e 60 - Normalizing Flow Affine Coupling & Online SVD Streaming PCA.

Valida empiricamente:
1. SovereignCortexRuntime com 60 órgãos ativos (v5.5.0-APEX-NFLOW-OSVD-60-ORGANS-SOVEREIGN);
2. Órgão 59: NormalizingFlowAffineEngine com invertibilidade exata, log-verossimilhança e detecção OOD;
3. Órgão 60: OnlineSVDStreamingPCA (Brand's incremental SVD) com ortonormalidade preservada e reconstrução de posto-k;
4. Despacho cognitivo das missões 'normalizing_flow_density' e 'online_svd_pca'.
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
from aethermind_cognitive_substrate.logic_symbolic.normalizing_flow_affine import (
    NormalizingFlowAffineEngine,
)
from aethermind_cognitive_substrate.planning.online_svd_streaming_pca import (
    OnlineSVDStreamingPCA,
)


class TestNFlowAndOSVD60(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 59 e 60 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_60_organs(self):
        """Verifica se o córtex inicializou com 60 órgãos ativos e status SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 60)
        self.assertTrue(health.get("normalizing_flow_affine_active"))
        self.assertTrue(health.get("online_svd_streaming_pca_active"))

    def test_02_normalizing_flow_exact_invertibility_and_ood(self):
        """Valida difeomorfismo exato f^{-1}(f(x)) == x, log-likelihood finita e detecção OOD."""
        flow = NormalizingFlowAffineEngine(dim=4, num_layers=6, hidden_size=16, seed=42)
        rng = np.random.default_rng(7)
        X = rng.normal(0.0, 1.5, size=(50, 4))

        z, log_det = flow.forward(X)
        self.assertEqual(z.shape, (50, 4))
        self.assertEqual(log_det.shape, (50,))
        self.assertTrue(np.all(np.isfinite(log_det)))

        X_rec = flow.inverse(z)
        max_err = float(np.max(np.abs(X - X_rec)))
        self.assertLess(max_err, 1e-10)

        res = flow.evaluate_density_estimation(X_data=X, n_samples=40)
        self.assertEqual(res["status"], "NORMALIZING_FLOW_DENSITY_ESTIMATED")
        self.assertTrue(res["invertibility_exact"])
        self.assertTrue(res["ood_is_lower"])
        self.assertLess(res["ood_log_likelihood"], res["mean_log_likelihood"])

    def test_03_normalizing_flow_ancestral_sampling(self):
        """Valida amostragem ancestral z ~ N(0, I) -> x = f^{-1}(z)."""
        flow = NormalizingFlowAffineEngine(dim=3, num_layers=4, hidden_size=12, seed=99)
        samples = flow.sample(64)
        self.assertEqual(samples.shape, (64, 3))
        self.assertTrue(np.all(np.isfinite(samples)))

    def test_04_online_svd_streaming_pca_orthonormality_and_low_rank(self):
        """Valida SVD incremental de Brand em subespaço de posto 3 dentro de 6D."""
        osvd = OnlineSVDStreamingPCA(n_components=3, seed=2026)
        rng = np.random.default_rng(123)

        # Gera dados de posto intrínseco 3 em R^6 com ruído pequeno
        latent = rng.normal(0.0, 2.0, size=(120, 3))
        proj_mat = rng.normal(0.0, 1.0, size=(3, 6))
        noise = rng.normal(0.0, 0.02, size=(120, 6))
        X = latent @ proj_mat + noise

        res = osvd.fit_and_evaluate(X_train=X[:100], X_test=X[100:], batch_size=10)
        self.assertEqual(res["status"], "ONLINE_SVD_PCA_FITTED")
        self.assertEqual(res["dim_original"], 6)
        self.assertEqual(res["n_components"], 3)
        self.assertGreater(res["cumulative_explained_variance"], 0.90)
        self.assertLess(res["mean_reconstruction_mse"], 0.05)

        # Verifica ortonormalidade da base U: U^T U == I_k
        UtU = osvd.U.T @ osvd.U
        ortho_err = float(np.max(np.abs(UtU - np.eye(3))))
        self.assertLess(ortho_err, 1e-8)

    def test_05_cognitive_missions_orchestration(self):
        """Testa despacho orquestrado das missões 'normalizing_flow_density' e 'online_svd_pca'."""
        nf_res = self.cortex.execute_cognitive_mission("normalizing_flow_density", {"n_samples": 30})
        self.assertEqual(nf_res["mission_type"], "normalizing_flow_density")
        self.assertEqual(nf_res["result"]["status"], "NORMALIZING_FLOW_DENSITY_ESTIMATED")
        self.assertTrue(nf_res["result"]["invertibility_exact"])

        pca_res = self.cortex.execute_cognitive_mission("online_svd_pca", {"batch_size": 15})
        self.assertEqual(pca_res["mission_type"], "online_svd_pca")
        self.assertEqual(pca_res["result"]["status"], "ONLINE_SVD_PCA_FITTED")
        self.assertGreater(pca_res["result"]["cumulative_explained_variance"], 0.5)


if __name__ == "__main__":
    unittest.main()
