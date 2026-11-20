"""Normalizing Flow Affine Coupling Engine — Invertible Exact Log-Likelihood Density Estimation.

Organ 59 do Substrato Cognitivo Nao-LLM (AetherCOS v5.5).
Modelo generativo invertivel com camadas de acoplamento afim (Dinh et al., NICE 2014 / RealNVP 2016):
- Cada camada particiona o vetor x em [x_a, x_b] e aplica transformacao afim invertivel:
    y_a = x_a
    y_b = x_b * exp(s(x_a)) + t(x_a)
  onde s() e t() sao redes deterministas (aqui MLPs em NumPy);
- O determinante Jacobiano e triangular por construcao: log|det J| = sum(s(x_a));
- Composicao de L camadas alternando as particoes gera um diffeomorfismo expressivo
  z <-> x com log p(x) = log p_z(z) + sum_{l=1}^{L} log|det J_l| exato;
- Permite avaliacao de log-verossimilhanca, amostragem ancestral e deteccao de anomalias OOD
  sem aproximacao variacional nem adversarial, em tempo O(D) e zero tokens LLM.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class _AffineCouplingLayer:
    """Camada de acoplamento afim invertivel com MLP simples (s, t)."""

    def __init__(self, dim: int, split_idx: int, hidden: int, rng: np.random.Generator):
        self.split_idx = split_idx
        d_a = split_idx
        d_b = dim - split_idx

        # Pesos da rede s/t: single hidden layer com tanh
        scale = 0.3
        self.W1 = rng.normal(0, scale, (d_a, hidden))
        self.b1 = np.zeros(hidden)
        self.W2_s = rng.normal(0, scale, (hidden, d_b))
        self.b2_s = np.zeros(d_b)
        self.W2_t = rng.normal(0, scale, (hidden, d_b))
        self.b2_t = np.zeros(d_b)

    def _net(self, x_a: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Calcula s(x_a) e t(x_a) via MLP com tanh."""
        h = np.tanh(x_a @ self.W1 + self.b1)
        s = h @ self.W2_s + self.b2_s
        t = h @ self.W2_t + self.b2_t
        # Clamp s para estabilidade numerica
        s = np.clip(s, -5.0, 5.0)
        return s, t

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Transformacao direta x -> y com log|det J|."""
        x_a = x[:, :self.split_idx]
        x_b = x[:, self.split_idx:]
        s, t = self._net(x_a)
        y_a = x_a
        y_b = x_b * np.exp(s) + t
        log_det = np.sum(s, axis=1)
        return np.hstack([y_a, y_b]), log_det

    def inverse(self, y: np.ndarray) -> np.ndarray:
        """Transformacao inversa y -> x (exata, sem aproximacao)."""
        y_a = y[:, :self.split_idx]
        y_b = y[:, self.split_idx:]
        s, t = self._net(y_a)
        x_a = y_a
        x_b = (y_b - t) * np.exp(-s)
        return np.hstack([x_a, x_b])


class NormalizingFlowAffineEngine:
    """
    Motor de Normalizing Flow com Camadas de Acoplamento Afim para
    estimacao exata de log-verossimilhanca e amostragem invertivel.
    """

    def __init__(
        self,
        dim: int = 2,
        num_layers: int = 4,
        hidden_size: int = 16,
        seed: int = 202659,
    ):
        self.dim = dim
        self.num_layers = num_layers
        self.rng = np.random.default_rng(seed)

        self.layers: List[_AffineCouplingLayer] = []
        for i in range(num_layers):
            # Alterna a particao: primeira metade vs segunda metade
            if i % 2 == 0:
                split = dim // 2
            else:
                split = dim - dim // 2
            self.layers.append(
                _AffineCouplingLayer(dim, split, hidden_size, self.rng)
            )

    @staticmethod
    def _log_normal_pdf(z: np.ndarray) -> np.ndarray:
        """Log-densidade da normal padrao multivariada isotropica."""
        d = z.shape[1]
        return -0.5 * (d * math.log(2.0 * math.pi) + np.sum(z * z, axis=1))

    def forward(self, x: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Mapeia x -> z (espaco latente) acumulando log|det J|."""
        total_log_det = np.zeros(len(x))
        h = x.copy()
        for layer in self.layers:
            h, ld = layer.forward(h)
            total_log_det += ld
        return h, total_log_det

    def inverse(self, z: np.ndarray) -> np.ndarray:
        """Mapeia z -> x (espaco observado) invertendo cada camada."""
        h = z.copy()
        for layer in reversed(self.layers):
            h = layer.inverse(h)
        return h

    def log_likelihood(self, x: np.ndarray) -> np.ndarray:
        """Calcula log p(x) = log p_z(f(x)) + log|det J_f(x)| exato."""
        z, log_det = self.forward(x)
        return self._log_normal_pdf(z) + log_det

    def sample(self, n: int) -> np.ndarray:
        """Amostragem ancestral: z ~ N(0, I), x = f^{-1}(z)."""
        z = self.rng.standard_normal((n, self.dim))
        return self.inverse(z)

    def evaluate_density_estimation(
        self,
        X_data: Optional[List[List[float]] | np.ndarray] = None,
        n_samples: int = 100,
    ) -> Dict[str, Any]:
        """
        Avalia o motor de normalizing flow:
        1. Calcula log-verossimilhanca media nos dados fornecidos (ou sinteticos);
        2. Verifica invertibilidade (||x - f^{-1}(f(x))|| < tol);
        3. Gera amostras ancestrais e reporta estatisticas.
        """
        t0 = time.perf_counter()

        if X_data is not None:
            X = np.asarray(X_data, dtype=np.float64)
            if X.ndim == 1:
                X = X.reshape(-1, self.dim)
        else:
            # Dados sinteticos: mistura de 2 gaussianas
            n_half = max(n_samples // 2, 2)
            g1 = self.rng.normal(loc=[-2.0] * self.dim, scale=0.4, size=(n_half, self.dim))
            g2 = self.rng.normal(loc=[2.0] * self.dim, scale=0.4, size=(n_half, self.dim))
            X = np.vstack([g1, g2])

        # 1. Log-likelihood
        ll = self.log_likelihood(X)
        mean_ll = float(np.mean(ll))
        std_ll = float(np.std(ll))

        # 2. Teste de invertibilidade
        z, _ = self.forward(X)
        X_reconstructed = self.inverse(z)
        recon_error = float(np.max(np.abs(X - X_reconstructed)))

        # 3. Amostragem ancestral
        samples = self.sample(n_samples)
        sample_mean = [round(float(v), 5) for v in np.mean(samples, axis=0)]
        sample_std = [round(float(v), 5) for v in np.std(samples, axis=0)]

        # 4. Anomalia OOD: ponto muito longe deve ter log-likelihood menor
        ood_point = np.full((1, self.dim), 50.0)
        ll_ood = float(self.log_likelihood(ood_point)[0])

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "NORMALIZING_FLOW_DENSITY_ESTIMATED",
            "dim": self.dim,
            "num_layers": self.num_layers,
            "n_data": len(X),
            "mean_log_likelihood": round(mean_ll, 5),
            "std_log_likelihood": round(std_ll, 5),
            "invertibility_max_error": round(recon_error, 12),
            "invertibility_exact": recon_error < 1e-8,
            "ood_log_likelihood": round(ll_ood, 3),
            "ood_is_lower": ll_ood < mean_ll,
            "sample_mean": sample_mean,
            "sample_std": sample_std,
            "n_samples_generated": n_samples,
            "elapsed_us": round(elapsed_us, 2),
        }
