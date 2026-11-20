"""Koopman Operator Spectral Linearizer & Extended Dynamic Mode Decomposition (pykoopman Inspiration).

Organ 41 do Substrato Cognitivo Não-LLM (AetherCOS v4.5).
Lineariza sistemas dinâmicos não-lineares e caóticos levantando o espaço de estados x
para um espaço de observáveis de alta dimensão Psi(x):
    Psi(x_{t+1}) = K * Psi(x_t)
onde K é o Operador de Koopman de dimensão finita aprendido de forma analítica fechada
(Extended Dynamic Mode Decomposition — EDMD regularizado por Tikhonov / SVD):
    K = Psi_Y @ Psi_X^T @ (Psi_X @ Psi_X^T + lambda * I)^{-1}
Extrai autovalores espectrais, frequências dominantes, verifica estabilidade discreta
rho(K) e realiza previsões analíticas multi-passo em tempo de sub-milissegundo.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class KoopmanSpectralLinearizer:
    """
    Linearizador Espectral pelo Operador de Koopman (EDMD Analítico em 1-Shot).
    Transforma dinâmicas físicas não-lineares em propagação linear exata no espaço levantado.
    """

    def __init__(self, state_dim: int = 4, ridge_alpha: float = 1e-4):
        self.state_dim = state_dim
        self.ridge_alpha = ridge_alpha
        self.K_matrix: Optional[np.ndarray] = None
        self.lifted_dim: int = self._compute_lifted_dim(state_dim)
        self.C_proj: np.ndarray = self._build_state_projector(state_dim, self.lifted_dim)

    @staticmethod
    def _compute_lifted_dim(d: int) -> int:
        # [1.0 (1)] + [x (d)] + [x^2 (d)] + [x_i * x_{i+1} (max(0, d-1))] + [sin(x) (d)] + [cos(x) (d)]
        cross_dim = max(0, d - 1)
        return 1 + d + d + cross_dim + d + d

    @staticmethod
    def _build_state_projector(d: int, lifted_dim: int) -> np.ndarray:
        """Constrói matriz C exata que recupera os estados físicos x a partir de Psi(x)."""
        C = np.zeros((d, lifted_dim), dtype=np.float64)
        for i in range(d):
            C[i, 1 + i] = 1.0
        return C

    def lift_state(self, x: np.ndarray) -> np.ndarray:
        """Mapeia um vetor de estado físico x em R^d para o espaço de observáveis Psi(x)."""
        vec = np.resize(np.array(x, dtype=np.float64).reshape(-1), self.state_dim)
        feats: List[float] = [1.0]
        feats.extend(vec.tolist())
        feats.extend((vec ** 2).tolist())
        if self.state_dim > 1:
            feats.extend((vec[:-1] * vec[1:]).tolist())
        feats.extend(np.sin(vec).tolist())
        feats.extend(np.cos(vec).tolist())
        return np.array(feats, dtype=np.float64)

    def lift_trajectory(self, states: np.ndarray) -> np.ndarray:
        """Levanta uma matriz de snapshots (T, d) para (lifted_dim, T)."""
        T = states.shape[0]
        lifted = np.zeros((self.lifted_dim, T), dtype=np.float64)
        for t in range(T):
            lifted[:, t] = self.lift_state(states[t])
        return lifted

    def fit_edmd(
        self,
        trajectory: List[List[float]] | np.ndarray
    ) -> Dict[str, Any]:
        """
        Ajusta o Operador de Koopman finito K em forma fechada (1-Shot) a partir de uma
        trajetória temporal contínua X = [x_0, x_1, ..., x_T].
        """
        t0 = time.perf_counter()
        traj = np.array(trajectory, dtype=np.float64)
        if traj.ndim == 1:
            traj = traj.reshape(-1, 1)

        if traj.shape[1] != self.state_dim:
            self.state_dim = traj.shape[1]
            self.lifted_dim = self._compute_lifted_dim(self.state_dim)
            self.C_proj = self._build_state_projector(self.state_dim, self.lifted_dim)

        if traj.shape[0] < 3:
            return {"status": "INSUFFICIENT_SNAPSHOTS", "fitted": False}

        X_snap = traj[:-1, :]  # (T-1, d)
        Y_snap = traj[1:, :]   # (T-1, d)

        psi_X = self.lift_trajectory(X_snap)  # (D, T-1)
        psi_Y = self.lift_trajectory(Y_snap)  # (D, T-1)

        # Solução fechada regularizada (Tikhonov Ridge EDMD):
        # K = Psi_Y * Psi_X^T * (Psi_X * Psi_X^T + alpha * I)^{-1}
        gram_G = np.dot(psi_X, psi_X.T) + self.ridge_alpha * np.eye(self.lifted_dim, dtype=np.float64)
        cross_A = np.dot(psi_Y, psi_X.T)
        self.K_matrix = np.linalg.solve(gram_G.T, cross_A.T).T

        # Decomposição Espectral de K
        eigvals = np.linalg.eigvals(self.K_matrix)
        moduli = np.abs(eigvals)
        spectral_radius = float(np.max(moduli))
        dominant_idx = int(np.argmax(moduli))
        dominant_freq_rad = float(np.angle(eigvals[dominant_idx]))

        # Erro de reconstrução em 1 passo no espaço físico
        psi_Y_pred = np.dot(self.K_matrix, psi_X)
        Y_pred = np.dot(self.C_proj, psi_Y_pred).T
        mse_1step = float(np.mean((Y_snap - Y_pred) ** 2))
        var_y = float(np.var(Y_snap))
        r2_score = float(1.0 - mse_1step / (var_y + 1e-12))

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "KOOPMAN_OPERATOR_FITTED",
            "fitted": True,
            "state_dim": self.state_dim,
            "lifted_observable_dim": self.lifted_dim,
            "snapshots_used": int(X_snap.shape[0]),
            "spectral_radius_rho": round(spectral_radius, 5),
            "is_spectrally_bounded": bool(spectral_radius <= 1.05),
            "dominant_eigenvalue_freq_rad": round(dominant_freq_rad, 5),
            "one_step_mse": float(f"{mse_1step:.3e}"),
            "r2_reconstruction": round(r2_score, 6),
            "elapsed_us": round(elapsed_us, 2)
        }

    def predict_horizon(
        self,
        initial_state: List[float] | np.ndarray,
        horizon_steps: int = 10
    ) -> Dict[str, Any]:
        """Propaga o sistema não-linear no futuro aplicando potências lineares K^t * Psi(x_0)."""
        t0 = time.perf_counter()
        if self.K_matrix is None:
            return {"status": "KOOPMAN_NOT_FITTED", "predicted": False}

        psi = self.lift_state(np.array(initial_state, dtype=np.float64))
        rollout: List[List[float]] = []

        for _ in range(horizon_steps):
            psi = np.dot(self.K_matrix, psi)
            # Evita divergência numérica extrema caso o sistema seja instável
            norm_psi = float(np.linalg.norm(psi))
            if norm_psi > 1e6:
                psi = psi * (1e6 / norm_psi)
            x_next = np.dot(self.C_proj, psi)
            rollout.append([round(float(v), 5) for v in x_next])

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "KOOPMAN_HORIZON_PREDICTED",
            "predicted": True,
            "horizon_steps": horizon_steps,
            "predicted_trajectory": rollout,
            "final_predicted_state": rollout[-1] if rollout else [],
            "elapsed_us": round(elapsed_us, 2)
        }
