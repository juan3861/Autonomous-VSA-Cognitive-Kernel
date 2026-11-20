"""Sparse Dictionary Learning (K-SVD) & Orthogonal Matching Pursuit (OMP) Engine.

Organ 61 do Substrato Cognitivo Nao-LLM (AetherCOS v5.6).
Aprendizado de dicionarios supercompletos e codificacao esparsa determinista
(Aharon, Elad & Bruckstein, IEEE TSP 2006 / Tropp & Gilbert, 2007):
- Codificacao esparsa via Orthogonal Matching Pursuit (OMP) mantendo suporte ativo |S| <= s;
- Atualizacao atomo-a-atomo K-SVD via decomposicao SVD de posto-1 sobre a matriz de erro
  restrita aos sinais que utilizam o atomo j (atualizando simultaneamente o atomo d_j e
  os coeficientes esparsos correspondentes);
- Garante invariancia de norma unitaria das colunas do dicionario (||d_j||_2 = 1);
- Calcula coerencia mutua mu(D) = max_{i!=j} |<d_i, d_j>|, RMSE de reconstrucao e SNR (dB).
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional
import numpy as np


class SparseDictionaryKSVDEngine:
    """
    Motor de Aprendizado de Dicionarios Esparsos K-SVD e Orthogonal Matching Pursuit (OMP).
    """

    def __init__(
        self,
        n_atoms: int = 16,
        sparsity_k: int = 3,
        n_iters: int = 15,
        seed: int = 202661,
    ):
        self.n_atoms = n_atoms
        self.sparsity_k = sparsity_k
        self.n_iters = n_iters
        self.rng = np.random.default_rng(seed)

    @staticmethod
    def _normalize_columns(D: np.ndarray) -> np.ndarray:
        """Normaliza cada coluna do dicionario para norma L2 unitaria."""
        norms = np.linalg.norm(D, axis=0, keepdims=True)
        norms = np.where(norms < 1e-12, 1.0, norms)
        return D / norms

    def omp_encode(
        self,
        Y: np.ndarray,
        D: np.ndarray,
        sparsity_k: Optional[int] = None,
        tol: float = 1e-8,
    ) -> np.ndarray:
        """
        Orthogonal Matching Pursuit (OMP) para Y (d, N) sobre dicionario D (d, K).
        Retorna matriz esparsa de coeficientes X (K, N).
        """
        d, n_samples = Y.shape
        K = D.shape[1]
        s_max = min(sparsity_k or self.sparsity_k, d, K)
        X = np.zeros((K, n_samples), dtype=np.float64)

        for n in range(n_samples):
            y = Y[:, n]
            residual = y.copy()
            support: List[int] = []

            for _ in range(s_max):
                if float(np.linalg.norm(residual)) < tol:
                    break
                # Correlacao com todos os atomos
                proj = np.abs(D.T @ residual)
                if support:
                    proj[support] = -1.0
                best_atom = int(np.argmax(proj))
                if proj[best_atom] <= 1e-12:
                    break
                support.append(best_atom)

                # Minimos quadrados restrito ao suporte ativo
                D_sub = D[:, support]
                coeffs, _, _, _ = np.linalg.lstsq(D_sub, y, rcond=None)
                residual = y - D_sub @ coeffs

            if support:
                D_sub = D[:, support]
                coeffs, _, _, _ = np.linalg.lstsq(D_sub, y, rcond=None)
                X[support, n] = coeffs

        return X

    @staticmethod
    def mutual_coherence(D: np.ndarray) -> float:
        """Calcula a coerencia mutua mu(D) = max_{i != j} |d_i^T d_j|."""
        G = np.abs(D.T @ D)
        np.fill_diagonal(G, 0.0)
        return float(np.max(G)) if G.size > 0 else 0.0

    def fit_and_encode(
        self,
        Y_signals: Optional[List[List[float]] | np.ndarray] = None,
        n_atoms: Optional[int] = None,
        sparsity_k: Optional[int] = None,
        n_iters: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executa K-SVD para aprender um dicionario supercompleto D e codificar Y ~= D X.
        """
        t0 = time.perf_counter()

        K = n_atoms or self.n_atoms
        s_k = sparsity_k or self.sparsity_k
        iters = n_iters or self.n_iters

        if Y_signals is not None:
            Y = np.asarray(Y_signals, dtype=np.float64)
            if Y.ndim == 1:
                Y = Y.reshape(-1, 1)
            # Espera-se (d, N); se vier (N, d) com N > d e d pequeno, usuario passa (d, N)
        else:
            # Gera 40 sinais 8D gerados por combinacoes 2-esparsas de um dicionario verdadeiro
            d_syn, n_syn, k_true = 8, 40, 12
            D_true = self._normalize_columns(self.rng.normal(0.0, 1.0, size=(d_syn, k_true)))
            X_true = np.zeros((k_true, n_syn))
            for i in range(n_syn):
                idx = self.rng.choice(k_true, size=2, replace=False)
                X_true[idx, i] = self.rng.normal(0.0, 1.5, size=2)
            Y = D_true @ X_true + self.rng.normal(0.0, 0.01, size=(d_syn, n_syn))
            K = min(K, 14)
            s_k = min(s_k, 3)

        d, N = Y.shape
        # Inicializa D com amostras normalizadas + ruido para cobrir K atomos
        if N >= K:
            chosen = self.rng.choice(N, size=K, replace=False)
            D = Y[:, chosen].copy()
        else:
            D = self.rng.normal(0.0, 1.0, size=(d, K))
        D = self._normalize_columns(D)

        X = np.zeros((K, N), dtype=np.float64)
        for _ in range(iters):
            # 1. Sparse Coding (OMP)
            X = self.omp_encode(Y, D, sparsity_k=s_k)

            # 2. Dictionary Update (K-SVD atom-by-atom)
            for j in range(K):
                omega_j = np.where(np.abs(X[j, :]) > 1e-12)[0]
                if len(omega_j) == 0:
                    # Atomo morto: reinicializa com sinal de maior erro residual
                    err_norms = np.linalg.norm(Y - D @ X, axis=0)
                    worst_idx = int(np.argmax(err_norms))
                    atom = Y[:, worst_idx] - D @ X[:, worst_idx]
                    norm_a = float(np.linalg.norm(atom))
                    if norm_a > 1e-12:
                        D[:, j] = atom / norm_a
                    continue

                # Erro sem o atomo j restrito a omega_j
                X_no_j = X[:, omega_j].copy()
                X_no_j[j, :] = 0.0
                E_j_omega = Y[:, omega_j] - D @ X_no_j

                # SVD de posto-1
                U_j, S_j, Vt_j = np.linalg.svd(E_j_omega, full_matrices=False)
                D[:, j] = U_j[:, 0]
                X[j, omega_j] = S_j[0] * Vt_j[0, :]

        # Avaliacao final
        X = self.omp_encode(Y, D, sparsity_k=s_k)
        Y_hat = D @ X
        mse = float(np.mean((Y - Y_hat) ** 2))
        rmse = math.sqrt(mse)
        sig_power = float(np.mean(Y ** 2))
        snr_db = 10.0 * math.log10(max(sig_power, 1e-15) / max(mse, 1e-15))
        mean_l0 = float(np.mean(np.sum(np.abs(X) > 1e-10, axis=0)))
        coherence = self.mutual_coherence(D)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "KSVD_SPARSE_DICTIONARY_LEARNED",
            "signal_dim": d,
            "n_signals": N,
            "n_atoms": K,
            "sparsity_k": s_k,
            "n_iters": iters,
            "mean_l0_sparsity": round(mean_l0, 3),
            "reconstruction_rmse": round(rmse, 6),
            "snr_db": round(snr_db, 3),
            "mutual_coherence": round(coherence, 5),
            "elapsed_us": round(elapsed_us, 2),
        }
