"""Hamiltonian Monte Carlo (HMC) Symplectic Bayesian Posterior Sampler.

Organ 66 do Substrato Cognitivo Nao-LLM (AetherCOS v5.8).
Amostrador MCMC simplético em espaço contínuo (Duane et al., 1987 / Neal, 2011):
- Simula dinâmica Hamiltoniana H(q, p) = U(q) + 0.5 ||p||^2 com integrador simplético Leapfrog
  (preservador de volume e reversível no tempo);
- Aplica correção exata de Metropolis-Hastings exp(H_init - H_prop) eliminando erro de
  discretização na distribuição estacionária alvo pi(q) = exp(-U(q));
- Evita passeio aleatório em distribuições fortemente correlacionadas, mantendo alta taxa de
  aceitação (> 0.70) e estimativa de Effective Sample Size (ESS).
"""
from __future__ import annotations

import math
import time
from typing import Callable, Dict, Any, List, Optional, Tuple
import numpy as np


class HamiltonianMonteCarloSampler:
    """
    Amostrador Bayesiano Hamiltonian Monte Carlo (HMC) com Integrador Leapfrog.
    """

    def __init__(
        self,
        step_size: float = 0.12,
        n_leapfrog: int = 12,
        seed: int = 202666,
    ):
        self.step_size = float(step_size)
        self.n_leapfrog = int(n_leapfrog)
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _default_correlated_gaussian_potential(
        mu: np.ndarray,
        inv_cov: np.ndarray,
    ) -> Tuple[Callable[[np.ndarray], float], Callable[[np.ndarray], np.ndarray]]:
        """Potencial U(q) = 0.5 (q - mu)^T Sigma^{-1} (q - mu) e gradiente."""
        def U(q: np.ndarray) -> float:
            d = q - mu
            return 0.5 * float(d.T @ inv_cov @ d)

        def grad_U(q: np.ndarray) -> np.ndarray:
            return inv_cov @ (q - mu)

        return U, grad_U

    @staticmethod
    def _estimate_ess_1d(chain: np.ndarray) -> float:
        """Estimativa de Effective Sample Size via autocorrelação de lag-1."""
        n = len(chain)
        if n < 10:
            return float(n)
        x = chain - np.mean(chain)
        var = float(np.var(x))
        if var < 1e-15:
            return 1.0
        rho1 = float(np.mean(x[:-1] * x[1:]) / var)
        rho1 = max(min(rho1, 0.99), -0.99)
        return float(n * (1.0 - rho1) / (1.0 + rho1))

    def sample_posterior(
        self,
        n_samples: int = 300,
        burn_in: int = 60,
        q0: Optional[List[float] | np.ndarray] = None,
        potential_fn: Optional[Callable[[np.ndarray], float]] = None,
        grad_potential_fn: Optional[Callable[[np.ndarray], np.ndarray]] = None,
        step_size: Optional[float] = None,
        n_leapfrog: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executa cadeia HMC retornando amostras da distribuição alvo, taxa de aceitação e ESS.
        """
        t0 = time.perf_counter()

        eps = float(step_size if step_size is not None else self.step_size)
        L = int(n_leapfrog if n_leapfrog is not None else self.n_leapfrog)

        target_mu = np.array([1.0, -1.0], dtype=np.float64)
        target_cov = np.array([[1.0, 0.85], [0.85, 1.0]], dtype=np.float64)
        if potential_fn is None or grad_potential_fn is None:
            inv_cov = np.linalg.inv(target_cov)
            U_fn, grad_U_fn = self._default_correlated_gaussian_potential(target_mu, inv_cov)
            using_default = True
        else:
            U_fn, grad_U_fn = potential_fn, grad_potential_fn
            using_default = False

        q_curr = np.asarray(q0 if q0 is not None else [0.0, 0.0], dtype=np.float64).reshape(-1)
        dim = len(q_curr)

        total_iters = burn_in + n_samples
        samples = np.zeros((n_samples, dim), dtype=np.float64)
        accepted_count = 0

        for it in range(total_iters):
            p_curr = self.rng.standard_normal(dim)
            q_prop = q_curr.copy()
            p_prop = p_curr.copy()

            # Integrador Simplético Leapfrog
            p_prop -= 0.5 * eps * grad_U_fn(q_prop)
            for step in range(L):
                q_prop += eps * p_prop
                if step != L - 1:
                    p_prop -= eps * grad_U_fn(q_prop)
            p_prop -= 0.5 * eps * grad_U_fn(q_prop)
            p_prop = -p_prop  # reversibilidade

            h_curr = U_fn(q_curr) + 0.5 * float(np.dot(p_curr, p_curr))
            h_prop = U_fn(q_prop) + 0.5 * float(np.dot(p_prop, p_prop))

            log_alpha = h_curr - h_prop
            if math.log(max(float(self.rng.uniform()), 1e-15)) < log_alpha:
                q_curr = q_prop
                if it >= burn_in:
                    accepted_count += 1

            if it >= burn_in:
                samples[it - burn_in] = q_curr

        acceptance_rate = accepted_count / max(1, n_samples)
        sample_mean = np.mean(samples, axis=0)
        sample_cov = np.cov(samples, rowvar=False)
        ess_dim0 = self._estimate_ess_1d(samples[:, 0])
        mean_error = float(np.linalg.norm(sample_mean - target_mu)) if using_default else None

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "HMC_SYMPLECTIC_POSTERIOR_SAMPLED",
            "dim": dim,
            "n_samples": n_samples,
            "burn_in": burn_in,
            "step_size": eps,
            "n_leapfrog": L,
            "acceptance_rate": round(acceptance_rate, 4),
            "sample_mean": [round(float(v), 5) for v in sample_mean],
            "sample_cov_diag": [round(float(v), 5) for v in np.diag(sample_cov)],
            "mean_error_vs_exact": round(mean_error, 5) if mean_error is not None else None,
            "ess_dim0": round(ess_dim0, 2),
            "elapsed_us": round(elapsed_us, 2),
        }
