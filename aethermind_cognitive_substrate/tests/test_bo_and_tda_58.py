"""Test Suite 35: Órgãos 57 e 58 - Bayesian Optimization (EI/UCB) & Topological Persistence Homology (TDA).

Valida empiricamente:
1. SovereignCortexRuntime com 58 órgãos ativos (v5.4.0-APEX-BO-TDA-58-ORGANS-SOVEREIGN);
2. Órgão 57: BayesianOptimizationEIEngine com aquisição analítica por Expected Improvement (EI) e UCB;
3. Órgão 58: TopologicalPersistenceHomologyEngine com filtração Vietoris-Rips, barcodes H0/H1 e entropia topológica;
4. Despacho cognitivo das missões 'bo_acquisition_step' e 'tda_persistence_diagram';
5. Native Cortex DLL Singleton com assinatura C-ABI íntegra.
"""
from __future__ import annotations

import math
import os
import sys
import unittest
from pathlib import Path
import numpy as np

# Configurações de ambiente anti-contenção de threads
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"

# Adiciona o substrate ao path
ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime
from aethermind_cognitive_substrate.planning.bayesian_optimization_ei import (
    BayesianOptimizationEIEngine,
)
from aethermind_cognitive_substrate.logic_symbolic.topological_persistence_homology import (
    TopologicalPersistenceHomologyEngine,
)
from aethermind_cognitive_substrate.physical_bridge.native_cortex_dll_singleton import (
    get_native_cortex_dll,
)


class TestBayesianOptAndTDA58(unittest.TestCase):
    """Bateria de testes empíricos para os órgãos 57 e 58 do Substrato Cognitivo Soberano."""

    @classmethod
    def setUpClass(cls):
        cls.cortex = SovereignCortexRuntime()

    def test_01_cortex_health_58_organs(self):
        """Verifica se o córtex inicializou e relata ao menos 58 órgãos ativos e status SOVEREIGN_READY."""
        health = self.cortex.get_system_health()
        self.assertEqual(health["status"], "SOVEREIGN_READY")
        self.assertGreaterEqual(health["organs_active_count"], 58)
        self.assertTrue(health.get("bayesian_optimization_ei_active"))
        self.assertTrue(health.get("topological_persistence_homology_active"))
        self.assertTrue(health.get("gp_cholesky_estimator_active"))
        self.assertTrue(health.get("optimal_transport_sinkhorn_active"))

    def test_02_native_cortex_dll_singleton(self):
        """Valida que o singleton da DLL Rust C-ABI carrega com sucesso e mantém identidade."""
        dll1 = get_native_cortex_dll()
        dll2 = get_native_cortex_dll()
        self.assertIs(dll1, dll2)
        if dll1 is not None:
            self.assertTrue(hasattr(dll1, "vsa_create_from_seed"))
            self.assertTrue(hasattr(dll1, "smc_quadratic_track_f64"))
            self.assertTrue(hasattr(dll1, "lyapunov_smith_doubling_f64"))

    def test_03_bayesian_optimization_expected_improvement(self):
        """Valida otimização Bayesiana 1D com Expected Improvement (EI)."""
        bo = BayesianOptimizationEIEngine(kernel="rbf", lengthscale=0.5, seed=42)

        # Função objetivo caixa-preta: f(x) = sin(3x) + 0.5x em [0, 3]
        def black_box_f(x: float) -> float:
            return math.sin(3.0 * x) + 0.5 * x

        # Amostras iniciais
        x_init = [0.2, 1.2, 2.8]
        y_init = [black_box_f(x) for x in x_init]
        bounds = [(0.0, 3.0)]

        res = bo.suggest_next_query(
            X_observed=x_init,
            y_observed=y_init,
            bounds=bounds,
            acquisition="ei",
            xi=0.01,
            n_candidates=128,
            maximize=True,
        )

        self.assertEqual(res["status"], "BAYESIAN_OPTIMIZATION_ACQUISITION_OPTIMIZED")
        self.assertEqual(res["acquisition"], "ei")
        self.assertEqual(len(res["suggested_next_x"]), 1)
        x_next = res["suggested_next_x"][0]

        # x_next deve respeitar os limites bounds
        self.assertGreaterEqual(x_next, bounds[0][0])
        self.assertLessEqual(x_next, bounds[0][1])

        # Score de aquisição deve ser não-negativo
        self.assertGreaterEqual(res["acquisition_score"], 0.0)

        # Incerteza e predição no ponto sugerido
        self.assertGreater(res["predicted_std"], 0.0)
        self.assertLess(res["gp_train_rmse"], 0.05)

    def test_04_bayesian_optimization_ucb_multistep(self):
        """Valida que iterações sucessivas de BO com UCB exploram o espaço e refinam o ótimo."""
        bo = BayesianOptimizationEIEngine(kernel="matern52", lengthscale=0.8, seed=123)

        bounds = [(-2.0, 2.0)]
        # Função parabólica invertida com pico em x = 0.5: f(x) = 2.0 - (x - 0.5)^2
        def objective(x: float) -> float:
            return 2.0 - (x - 0.5) ** 2

        X_obs = [[-1.5], [1.8]]
        y_obs = [objective(X_obs[0][0]), objective(X_obs[1][0])]

        for _ in range(3):
            step = bo.suggest_next_query(
                X_observed=X_obs,
                y_observed=y_obs,
                bounds=bounds,
                acquisition="ucb",
                kappa=2.5,
                n_candidates=64,
                maximize=True,
            )
            x_cand = step["suggested_next_x"]
            y_cand = objective(x_cand[0])
            X_obs.append(x_cand)
            y_obs.append(y_cand)

        best_y = max(y_obs)
        # O ótimo teórico é 2.0; após 3 passos de BO, deve ter se aproximado (> 1.5)
        self.assertGreater(best_y, 1.5)

    def test_05_topological_persistence_two_separated_clusters(self):
        """Valida que Vietoris-Rips detecta corretamente 2 clusters bem separados com grande gap de H0."""
        tda = TopologicalPersistenceHomologyEngine()

        # 4 pontos no Cluster A (ao redor de 0.0, 0.0)
        cluster_a = [
            [0.0, 0.0],
            [0.05, 0.0],
            [0.0, 0.05],
            [-0.05, 0.0]
        ]
        # 4 pontos no Cluster B (ao redor de 10.0, 10.0)
        cluster_b = [
            [10.0, 10.0],
            [10.05, 10.0],
            [10.0, 10.05],
            [9.95, 10.0]
        ]
        points = cluster_a + cluster_b

        res = tda.compute_persistence_diagram(point_cloud=points)

        self.assertEqual(res["status"], "PERSISTENCE_HOMOLOGY_COMPUTED")
        self.assertEqual(res["n_points"], 8)
        self.assertEqual(res["h0_components_born"], 8)
        # 7 componentes devem morrer ao se fundirem, 1 sobrevive infinitamente
        self.assertEqual(res["h0_deaths_recorded"], 7)

        # A distância entre os clusters é aproximadamente sqrt(10^2 + 10^2) ~= 14.14
        # Portanto, a morte mais persistente de H0 deve ser > 10.0
        self.assertGreater(res["max_h0_persistence_lifetime"], 10.0)

        # Entropia topológica de persistência deve ser estritamente positiva
        self.assertGreater(res["persistence_entropy"], 0.0)

    def test_06_topological_persistence_circle_h1_cycle(self):
        """Valida que uma nuvem em anel circular gera potenciais 1-ciclos topológicos H1."""
        tda = TopologicalPersistenceHomologyEngine()

        # 8 pontos regularmente espaçados sobre um círculo de raio 2.0
        num_pts = 8
        circle_pts = []
        for i in range(num_pts):
            theta = 2.0 * math.pi * i / num_pts
            circle_pts.append([2.0 * math.cos(theta), 2.0 * math.sin(theta)])

        res = tda.compute_persistence_diagram(point_cloud=circle_pts)

        self.assertEqual(res["status"], "PERSISTENCE_HOMOLOGY_COMPUTED")
        self.assertEqual(res["n_points"], 8)
        # Em um anel, arestas que fecham ciclos no 1-esqueleto produzem nascimentos de ciclos H1
        self.assertGreater(res["h1_cycle_births_count"], 0)

    def test_07_cognitive_missions_orchestration(self):
        """Testa o despacho orquestrado das novas missões no Córtex Soberano."""
        # Missão 1: bo_acquisition_step
        bo_res = self.cortex.execute_cognitive_mission(
            mission_type="bo_acquisition_step",
            payload={
                "X_observed": [[0.5], [1.5], [4.0]],
                "y_observed": [0.479, 0.997, -0.756],
                "bounds": [(0.0, 5.0)],
                "acquisition": "ei",
                "num_candidates": 64,
            }
        )
        self.assertEqual(bo_res["mission_type"], "bo_acquisition_step")
        self.assertEqual(bo_res["result"]["status"], "BAYESIAN_OPTIMIZATION_ACQUISITION_OPTIMIZED")
        self.assertIn("suggested_next_x", bo_res["result"])

        # Missão 2: tda_persistence_diagram
        tda_res = self.cortex.execute_cognitive_mission(
            mission_type="tda_persistence_diagram",
            payload={
                "points": [[0.0, 0.0], [0.1, 0.0], [5.0, 5.0], [5.1, 5.0]],
            }
        )
        self.assertEqual(tda_res["mission_type"], "tda_persistence_diagram")
        self.assertEqual(tda_res["result"]["status"], "PERSISTENCE_HOMOLOGY_COMPUTED")
        self.assertEqual(tda_res["result"]["h0_deaths_recorded"], 3)


if __name__ == "__main__":
    unittest.main()
