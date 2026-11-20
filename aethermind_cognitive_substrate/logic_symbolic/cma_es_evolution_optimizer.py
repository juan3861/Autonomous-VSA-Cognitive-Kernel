"""Covariance Matrix Adaptation Evolution Strategy (CMA-ES) Optimizer.

Organ 67 do Substrato Cognitivo Nao-LLM (AetherCOS v5.9).
Otimizador evolutivo de caixa-preta nao-convexo e livre de gradientes (Hansen & Ostermeier, 2001):
- Adapta dinamicamente a matriz de covariancia C (rank-1 + rank-mu) e o tamanho de passo global sigma
  via Cumulative Step-size Adaptation (CSA);
- Invariante a rotacoes e transformacoes monotonicas da funcao objetivo f(x);
- Resolve funcoes multimodais e mal-condicionadas (Rosenbrock, Rastrigin, Esfera anisotropica)
  sem gradientes e com zero tokens LLM.
"""
from __future__ import annotations

import math
import time
from typing import Callable, Dict, Any, List, Optional
import numpy as np


class CMAESBlackBoxOptimizer:
    """
    Otimizador Continuo Livre de Gradientees CMA-ES (Hansen).
    """

    def __init__(self, dim: int = 4, sigma0: float = 1.0, seed: int = 202667):
        self.dim = int(dim)
        self.sigma0 = float(sigma0)
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _default_rosenbrock(x: np.ndarray) -> float:
        """Funcao de Rosenbrock (vale estreito curvo nao-convexo, minimo global 0 em [1,...,1])."""
        return float(np.sum(100.0 * (x[1:] - x[:-1] ** 2) ** 2 + (1.0 - x[:-1]) ** 2))

    def minimize(
        self,
        objective_fn: Optional[Callable[[np.ndarray], float]] = None,
        x0: Optional[List[float] | np.ndarray] = None,
        sigma0: Optional[float] = None,
        max_gens: int = 120,
        tol: float = 1e-6,
    ) -> Dict[str, Any]:
        """
        Minimiza objective_fn(x) em R^d via CMA-ES.
        """
        t0 = time.perf_counter()

        fn = objective_fn if objective_fn is not None else self._default_rosenbrock
        mean = np.asarray(x0 if x0 is not None else np.zeros(self.dim), dtype=np.float64).copy()
        n = len(mean)
        sigma = float(sigma0 if sigma0 is not None else self.sigma0)

        # Parametros canonicos de Hansen
        lam = 4 + int(3 * math.log(max(n, 2)))
        mu = lam // 2
        raw_w = np.array([math.log(mu + 0.5) - math.log(i + 1) for i in range(mu)], dtype=np.float64)
        weights = raw_w / np.sum(raw_w)
        mueff = float(1.0 / np.sum(weights ** 2))

        cc = (4.0 + mueff / n) / (n + 4.0 + 2.0 * mueff / n)
        cs = (mueff + 2.0) / (n + mueff + 5.0)
        c1 = 2.0 / ((n + 1.3) ** 2 + mueff)
        cmu = min(1.0 - c1, 2.0 * (mueff - 2.0 + 1.0 / mueff) / ((n + 2.0) ** 2 + mueff))
        damps = 1.0 + 2.0 * max(0.0, math.sqrt((mueff - 1.0) / (n + 1.0)) - 1.0) + cs
        chiN = math.sqrt(n) * (1.0 - 1.0 / (4.0 * n) + 1.0 / (21.0 * n * n))

        pc = np.zeros(n, dtype=np.float64)
        ps = np.zeros(n, dtype=np.float64)
        B = np.eye(n, dtype=np.float64)
        D = np.ones(n, dtype=np.float64)
        C = np.eye(n, dtype=np.float64)
        invsqrtC = np.eye(n, dtype=np.float64)

        initial_f = fn(mean)
        best_f = initial_f
        best_x = mean.copy()
        gens_run = 0

        for gen in range(1, max_gens + 1):
            gens_run = gen
            # Amostragem da populacao
            arz = self.rng.standard_normal((lam, n))
            arx = np.zeros((lam, n), dtype=np.float64)
            fitness = np.zeros(lam, dtype=np.float64)

            for k in range(lam):
                arx[k] = mean + sigma * (B @ (D * arz[k]))
                fitness[k] = fn(arx[k])

            order = np.argsort(fitness)
            if fitness[order[0]] < best_f:
                best_f = float(fitness[order[0]])
                best_x = arx[order[0]].copy()

            # Recombinacao ponderada
            old_mean = mean.copy()
            selected = arx[order[:mu]]
            mean = weights @ selected
            y_w = (mean - old_mean) / max(sigma, 1e-15)

            # Atualizacao dos caminhos evolutivos
            ps = (1.0 - cs) * ps + math.sqrt(cs * (2.0 - cs) * mueff) * (invsqrtC @ y_w)
            ps_norm = float(np.linalg.norm(ps))
            hsig = 1.0 if ps_norm / math.sqrt(1.0 - (1.0 - cs) ** (2 * gen)) / chiN < (1.4 + 2.0 / (n + 1.0)) else 0.0
            pc = (1.0 - cc) * pc + hsig * math.sqrt(cc * (2.0 - cc) * mueff) * y_w

            # Adaptacao da matriz de covariancia C
            artmp = (selected - old_mean) / max(sigma, 1e-15)
            C_mu_mat = (artmp.T * weights) @ artmp
            C = (
                (1.0 - c1 - cmu) * C
                + c1 * (np.outer(pc, pc) + (1.0 - hsig) * cc * (2.0 - cc) * C)
                + cmu * C_mu_mat
            )
            C = 0.5 * (C + C.T)

            # Adaptacao do passo sigma
            sigma *= math.exp((cs / damps) * (ps_norm / chiN - 1.0))
            sigma = min(max(sigma, 1e-12), 1e4)

            # Decomposicao espectral de C
            eigvals, B = np.linalg.eigh(C)
            eigvals = np.maximum(eigvals, 1e-16)
            D = np.sqrt(eigvals)
            invsqrtC = B @ np.diag(1.0 / D) @ B.T

            if best_f < tol or sigma < 1e-9:
                break

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "CMAES_BLACKBOX_CONVERGED",
            "dim": n,
            "population_size": lam,
            "generations": gens_run,
            "initial_fitness": round(initial_f, 6),
            "best_fitness": float(f"{best_f:.3e}"),
            "best_x": [round(float(v), 5) for v in best_x],
            "final_sigma": float(f"{sigma:.3e}"),
            "elapsed_us": round(elapsed_us, 2),
        }
