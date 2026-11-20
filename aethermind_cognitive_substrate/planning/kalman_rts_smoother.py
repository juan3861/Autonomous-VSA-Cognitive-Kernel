"""Rauch-Tung-Striebel (RTS) Optimal Fixed-Interval Bayesian Smoother.

Organ 62 do Substrato Cognitivo Nao-LLM (AetherCOS v5.6).
Suavizador Bayesiano otimo em intervalo fixo para reconstrucao retrospectiva de trajetoria
e estimacao de estado a posteriori com toda a evidencia temporal y_{1:T}:
- Passo Forward (Filtro de Kalman): calcula (x_{t|t}, P_{t|t}) e predicoes (x_{t+1|t}, P_{t+1|t});
- Passo Backward (Rauch-Tung-Striebel, 1965):
    C_t = P_{t|t} A^T P_{t+1|t}^{-1}
    x_{t|T} = x_{t|t} + C_t (x_{t+1|T} - x_{t+1|t})
    P_{t|T} = P_{t|t} + C_t (P_{t+1|T} - P_{t+1|t}) C_t^T
- Garante reducao monotona da covariancia posterior: Tr(P_{t|T}) <= Tr(P_{t|t}) para todo t < T;
- Zero tokens LLM, algebra linear exata O(T * n^3).
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional
import numpy as np


class RauchTungStriebelSmoother:
    """
    Suavizador Otimo de Rauch-Tung-Striebel (RTS) sobre sistemas lineares Gaussianos.
    """

    def __init__(self, dt: float = 0.1, seed: int = 202662):
        self.dt = float(dt)
        self.rng = np.random.default_rng(seed)

    def smooth_trajectory(
        self,
        observations: Optional[List[List[float]] | np.ndarray] = None,
        A: Optional[List[List[float]] | np.ndarray] = None,
        H: Optional[List[List[float]] | np.ndarray] = None,
        Q: Optional[List[List[float]] | np.ndarray] = None,
        R: Optional[List[List[float]] | np.ndarray] = None,
        x0: Optional[List[float] | np.ndarray] = None,
        P0: Optional[List[List[float]] | np.ndarray] = None,
        ground_truth_positions: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """
        Executa filtragem Kalman forward + suavizacao RTS backward sobre a sequencia observada.
        """
        t0 = time.perf_counter()

        if observations is None:
            # Gera trajetoria sintetica 1D com velocidade constante + ruido de processo e medicao
            T_syn = 40
            dt = self.dt
            A_mat = np.array([[1.0, dt], [0.0, 1.0]], dtype=np.float64)
            H_mat = np.array([[1.0, 0.0]], dtype=np.float64)
            Q_mat = np.array([[1e-3, 0.0], [0.0, 2e-2]], dtype=np.float64)
            R_mat = np.array([[0.25]], dtype=np.float64)

            states_true = np.zeros((T_syn, 2), dtype=np.float64)
            obs_arr = np.zeros((T_syn, 1), dtype=np.float64)
            curr = np.array([0.0, 1.2], dtype=np.float64)
            for t in range(T_syn):
                curr = A_mat @ curr + self.rng.multivariate_normal([0.0, 0.0], Q_mat)
                states_true[t] = curr
                obs_arr[t] = H_mat @ curr + self.rng.normal(0.0, math.sqrt(R_mat[0, 0]), size=1)
            gt_pos = states_true[:, 0]
        else:
            obs_arr = np.asarray(observations, dtype=np.float64)
            if obs_arr.ndim == 1:
                obs_arr = obs_arr.reshape(-1, 1)
            dt = self.dt
            A_mat = np.asarray(A, dtype=np.float64) if A is not None else np.array([[1.0, dt], [0.0, 1.0]], dtype=np.float64)
            m_obs = obs_arr.shape[1]
            n_state = A_mat.shape[0]
            H_mat = np.asarray(H, dtype=np.float64) if H is not None else np.eye(m_obs, n_state, dtype=np.float64)
            Q_mat = np.asarray(Q, dtype=np.float64) if Q is not None else (1e-2 * np.eye(n_state, dtype=np.float64))
            R_mat = np.asarray(R, dtype=np.float64) if R is not None else (0.25 * np.eye(m_obs, dtype=np.float64))
            gt_pos = np.asarray(ground_truth_positions, dtype=np.float64) if ground_truth_positions is not None else None

        T = len(obs_arr)
        n = A_mat.shape[0]
        I_n = np.eye(n, dtype=np.float64)

        x_init = np.asarray(x0, dtype=np.float64) if x0 is not None else np.zeros(n, dtype=np.float64)
        P_init = np.asarray(P0, dtype=np.float64) if P0 is not None else np.eye(n, dtype=np.float64)

        # Estruturas forward
        x_filt = np.zeros((T, n), dtype=np.float64)
        P_filt = np.zeros((T, n, n), dtype=np.float64)
        x_pred = np.zeros((T, n), dtype=np.float64)
        P_pred = np.zeros((T, n, n), dtype=np.float64)

        x_curr = x_init.copy()
        P_curr = P_init.copy()

        # 1. Passo Forward (Kalman Filter)
        for t in range(T):
            if t == 0:
                xp = x_curr
                Pp = P_curr
            else:
                xp = A_mat @ x_filt[t - 1]
                Pp = A_mat @ P_filt[t - 1] @ A_mat.T + Q_mat

            x_pred[t] = xp
            P_pred[t] = 0.5 * (Pp + Pp.T)

            # Inovacao e ganho de Kalman
            S = H_mat @ P_pred[t] @ H_mat.T + R_mat + 1e-12 * np.eye(H_mat.shape[0])
            K = np.linalg.solve(S.T, (P_pred[t] @ H_mat.T).T).T
            innov = obs_arr[t] - H_mat @ xp

            xf = xp + K @ innov
            IKH = I_n - K @ H_mat
            # Forma de Joseph para estabilidade numerica da covariancia
            Pf = IKH @ P_pred[t] @ IKH.T + K @ R_mat @ K.T
            x_filt[t] = xf
            P_filt[t] = 0.5 * (Pf + Pf.T)

        # 2. Passo Backward (Rauch-Tung-Striebel Smoother)
        x_smooth = np.zeros((T, n), dtype=np.float64)
        P_smooth = np.zeros((T, n, n), dtype=np.float64)
        x_smooth[-1] = x_filt[-1]
        P_smooth[-1] = P_filt[-1]

        for t in range(T - 2, -1, -1):
            Pp_next = P_pred[t + 1] + 1e-12 * I_n
            # C_t = P_{t|t} A^T P_{t+1|t}^{-1}
            C_t = np.linalg.solve(Pp_next.T, (P_filt[t] @ A_mat.T).T).T

            x_smooth[t] = x_filt[t] + C_t @ (x_smooth[t + 1] - x_pred[t + 1])
            Ps = P_filt[t] + C_t @ (P_smooth[t + 1] - P_pred[t + 1]) @ C_t.T
            P_smooth[t] = 0.5 * (Ps + Ps.T)

        # Verificacao de reducao monotona da covariancia: Tr(P_{t|T}) <= Tr(P_{t|t})
        filt_traces = [float(np.trace(P_filt[t])) for t in range(T)]
        smooth_traces = [float(np.trace(P_smooth[t])) for t in range(T)]
        mean_filt_trace = float(np.mean(filt_traces))
        mean_smooth_trace = float(np.mean(smooth_traces))
        cov_reduction_ok = all(smooth_traces[t] <= filt_traces[t] + 1e-9 for t in range(T))

        filt_rmse = None
        smooth_rmse = None
        if gt_pos is not None and len(gt_pos) == T:
            filt_rmse = round(float(np.sqrt(np.mean((x_filt[:, 0] - gt_pos) ** 2))), 6)
            smooth_rmse = round(float(np.sqrt(np.mean((x_smooth[:, 0] - gt_pos) ** 2))), 6)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "RTS_OPTIMAL_TRAJECTORY_SMOOTHED",
            "horizon_steps": T,
            "state_dim": n,
            "mean_filtered_cov_trace": round(mean_filt_trace, 6),
            "mean_smoothed_cov_trace": round(mean_smooth_trace, 6),
            "covariance_reduction_verified": cov_reduction_ok,
            "filtered_rmse": filt_rmse,
            "smoothed_rmse": smooth_rmse,
            "final_smoothed_state": [round(float(v), 5) for v in x_smooth[-1]],
            "elapsed_us": round(elapsed_us, 2),
        }
