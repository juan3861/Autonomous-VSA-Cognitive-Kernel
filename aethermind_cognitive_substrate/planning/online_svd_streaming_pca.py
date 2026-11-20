"""Online Streaming SVD / Incremental PCA Engine (Brand's Algorithm).

Organ 60 do Substrato Cognitivo Nao-LLM (AetherCOS v5.5).
Reducao de dimensionalidade em streams infinitos de dados via SVD incremental
(Brand, Linear Algebra and its Applications 2006):
- Mantem decomposicao de posto-k truncada U_k Sigma_k V_k^T em memoria O(D*k);
- Atualiza com cada novo vetor (ou mini-batch) sem recalcular a SVD completa;
- Projeta e reconstroi dados em tempo O(D*k) por amostra;
- Calcula variancia explicada cumulativa e erro de reconstrucao residual;
- Suporta deteccao de mudanca de distribuicao (concept drift) via monitoramento
  do decaimento relativo dos valores singulares.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class OnlineSVDStreamingPCA:
    """
    Motor de SVD Incremental (Brand) para PCA em streams infinitos sem
    recomputar a decomposicao completa.
    """

    def __init__(self, n_components: int = 4, seed: int = 202660):
        self.k = n_components
        self.rng = np.random.default_rng(seed)
        self.U: Optional[np.ndarray] = None   # (D, k) base ortonormal
        self.S: Optional[np.ndarray] = None   # (k,) valores singulares
        self.n_seen: int = 0
        self._mean: Optional[np.ndarray] = None
        self._initialized: bool = False

    def _initialize(self, X: np.ndarray):
        """Inicializa com SVD truncada do primeiro batch."""
        self._mean = np.mean(X, axis=0)
        X_centered = X - self._mean
        U, s, Vt = np.linalg.svd(X_centered, full_matrices=False)
        k = min(self.k, len(s))
        self.U = Vt[:k].T  # (D, k)
        self.S = s[:k]
        self.n_seen = len(X)
        self._initialized = True

    def partial_fit(self, X: np.ndarray):
        """
        Atualiza incrementalmente a SVD com novas observacoes.
        Brand's rank-1 update generalizado para mini-batches.
        """
        X = np.asarray(X, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)

        if not self._initialized:
            self._initialize(X)
            return

        # Atualiza media online (Welford)
        for row in X:
            self.n_seen += 1
            delta = row - self._mean
            self._mean += delta / self.n_seen

        X_centered = X - self._mean

        for x in X_centered:
            x = x.reshape(-1, 1)  # (D, 1)
            # Projeta x no subespaco atual
            proj = self.U.T @ x  # (k, 1)
            # Componente ortogonal residual
            residual = x - self.U @ proj
            res_norm = float(np.linalg.norm(residual))

            if res_norm < 1e-14:
                # x esta inteiramente no subespaco atual — atualizar apenas S
                K = np.diag(self.S).astype(np.float64)
                K += proj @ proj.T / self.n_seen
                eigvals, eigvecs = np.linalg.eigh(K)
                idx = np.argsort(eigvals)[::-1][:self.k]
                self.S = np.sqrt(np.maximum(eigvals[idx], 0.0))
                self.U = self.U @ eigvecs[:, idx]
            else:
                # Rank-1 expansion + truncation
                q = residual / res_norm  # (D, 1) novo vetor base
                U_ext = np.hstack([self.U, q])  # (D, k+1)

                # Constroi a matriz intermediaria (k+1, k+1)
                S_diag = np.diag(self.S)
                top_row = np.hstack([S_diag, proj])  # (k, k+1)
                bot_row = np.zeros((1, self.k + 1))
                bot_row[0, self.k] = res_norm
                K = np.vstack([top_row, bot_row])  # (k+1, k+1)

                # SVD da matriz intermediaria
                U2, s2, Vt2 = np.linalg.svd(K, full_matrices=False)
                trunc = min(self.k, len(s2))
                self.U = U_ext @ U2[:, :trunc]
                self.S = s2[:trunc]

    def transform(self, X: np.ndarray) -> np.ndarray:
        """Projeta dados no subespaco de posto-k."""
        if not self._initialized:
            raise RuntimeError("Engine nao inicializada. Chame partial_fit() primeiro.")
        X_centered = np.asarray(X, dtype=np.float64) - self._mean
        return X_centered @ self.U  # (N, k)

    def inverse_transform(self, Z: np.ndarray) -> np.ndarray:
        """Reconstroi dados do subespaco para o espaco original."""
        return np.asarray(Z, dtype=np.float64) @ self.U.T + self._mean

    def explained_variance_ratio(self) -> np.ndarray:
        """Fracao da variancia explicada por cada componente."""
        if self.S is None:
            return np.array([])
        total = np.sum(self.S ** 2)
        if total < 1e-15:
            return np.zeros_like(self.S)
        return self.S ** 2 / total

    def fit_and_evaluate(
        self,
        X_train: Optional[List[List[float]] | np.ndarray] = None,
        X_test: Optional[List[List[float]] | np.ndarray] = None,
        batch_size: int = 10,
    ) -> Dict[str, Any]:
        """
        Treina incrementalmente em X_train (mini-batches), projeta X_test,
        calcula erro de reconstrucao e variancia explicada.
        """
        t0 = time.perf_counter()

        if X_train is not None:
            X_tr = np.asarray(X_train, dtype=np.float64)
        else:
            # Dados sinteticos: 3 clusters em 6D
            c1 = self.rng.normal([2, 0, 0, 0, 0, 0], 0.3, (30, 6))
            c2 = self.rng.normal([0, 3, 0, 0, 0, 0], 0.3, (30, 6))
            c3 = self.rng.normal([0, 0, 4, 0, 0, 0], 0.3, (30, 6))
            X_tr = np.vstack([c1, c2, c3])

        if X_test is not None:
            X_te = np.asarray(X_test, dtype=np.float64)
        else:
            X_te = X_tr[-10:]

        # Treinamento incremental por mini-batches
        num_batches = 0
        for i in range(0, len(X_tr), batch_size):
            batch = X_tr[i:i + batch_size]
            self.partial_fit(batch)
            num_batches += 1

        # Projecao e reconstrucao
        Z_test = self.transform(X_te)
        X_recon = self.inverse_transform(Z_test)
        recon_error = float(np.mean(np.sum((X_te - X_recon) ** 2, axis=1)))
        recon_error_max = float(np.max(np.sum((X_te - X_recon) ** 2, axis=1)))

        ev_ratio = self.explained_variance_ratio()
        cumulative_ev = float(np.sum(ev_ratio))

        # Deteccao de drift: razao entre ultimo e primeiro valor singular
        drift_ratio = float(self.S[-1] / self.S[0]) if len(self.S) > 1 and self.S[0] > 1e-15 else 0.0

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "ONLINE_SVD_PCA_FITTED",
            "dim_original": X_tr.shape[1],
            "n_components": len(self.S),
            "n_train_samples": len(X_tr),
            "n_batches": num_batches,
            "batch_size": batch_size,
            "n_test_samples": len(X_te),
            "singular_values": [round(float(v), 5) for v in self.S],
            "explained_variance_ratio": [round(float(v), 5) for v in ev_ratio],
            "cumulative_explained_variance": round(cumulative_ev, 5),
            "mean_reconstruction_mse": round(recon_error, 8),
            "max_reconstruction_mse": round(recon_error_max, 8),
            "drift_ratio_last_first_sv": round(drift_ratio, 5),
            "elapsed_us": round(elapsed_us, 2),
        }
