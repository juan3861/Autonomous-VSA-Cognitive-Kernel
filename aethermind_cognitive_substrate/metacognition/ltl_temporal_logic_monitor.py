"""Formal Linear & Signal Temporal Logic (LTL / STL) Quantitative Robustness Runtime Monitor.

Organ 49 do Substrato Cognitivo Não-LLM (AetherCOS v5.0).
Implementa semântica quantitativa estrita (Maler & Nickovic) para Lógica Temporal de Sinais (STL)
e Lógica Temporal Linear (LTL) sobre traços finitos de telemetria e trajetória:
- Robustez Quantitativa rho(phi, x, t) in R:
    rho >= 0  <==>  propriedade satisfeita no tempo t (magnitude = margem exata até violação).
- Conectivos Booleanos:
    not(phi)  = -rho(phi)
    phi1 ^ phi2 = min(rho1, rho2)
    phi1 v phi2 = max(rho1, rho2)
- Operadores Temporais em Janela [a, b]:
    Globally G_[a, b](phi):   min_{t' in t + [a, b]} rho(phi, t')
    Eventually F_[a, b](phi): max_{t' in t + [a, b]} rho(phi, t')
    Until U_[a, b](p1, p2):   sup_{t' in [a, b]} min(rho(p2, t'), inf_{s in [a, t']} rho(p1, s))
    Response G(trigger -> F_[0, k] recover): todo evento de gatilho deve recuperar em até k passos.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional
import numpy as np


class STLTemporalLogicMonitor:
    """
    Monitor Formal de Lógica Temporal de Sinais (STL / LTL Quantitativo).
    Verifica garantias temporais de invariância, liveness e resposta com prova de robustez.
    """

    @staticmethod
    def eval_always_upper(trace: List[float] | np.ndarray, upper_bound: float, t_start: int = 0, t_end: Optional[int] = None) -> float:
        """Robustez de G_[a, b] (x <= upper_bound) = min_t (upper_bound - x_t)."""
        arr = np.array(trace, dtype=np.float64).reshape(-1)
        end = len(arr) if t_end is None else min(len(arr), t_end + 1)
        window = arr[max(0, t_start):end]
        if len(window) == 0:
            return -1e9
        return float(np.min(upper_bound - window))

    @staticmethod
    def eval_always_lower(trace: List[float] | np.ndarray, lower_bound: float, t_start: int = 0, t_end: Optional[int] = None) -> float:
        """Robustez de G_[a, b] (x >= lower_bound) = min_t (x_t - lower_bound)."""
        arr = np.array(trace, dtype=np.float64).reshape(-1)
        end = len(arr) if t_end is None else min(len(arr), t_end + 1)
        window = arr[max(0, t_start):end]
        if len(window) == 0:
            return -1e9
        return float(np.min(window - lower_bound))

    @staticmethod
    def eval_eventually_below(trace: List[float] | np.ndarray, target_upper: float, t_start: int = 0, t_end: Optional[int] = None) -> float:
        """Robustez de F_[a, b] (x <= target_upper) = max_t (target_upper - x_t)."""
        arr = np.array(trace, dtype=np.float64).reshape(-1)
        end = len(arr) if t_end is None else min(len(arr), t_end + 1)
        window = arr[max(0, t_start):end]
        if len(window) == 0:
            return -1e9
        return float(np.max(target_upper - window))

    @staticmethod
    def eval_until(
        robustness_phi1: List[float] | np.ndarray,
        robustness_phi2: List[float] | np.ndarray,
        t_start: int = 0,
        t_end: Optional[int] = None
    ) -> float:
        """Robustez exata de (phi1 U_[a, b] phi2)."""
        r1 = np.array(robustness_phi1, dtype=np.float64).reshape(-1)
        r2 = np.array(robustness_phi2, dtype=np.float64).reshape(-1)
        n = min(len(r1), len(r2))
        if n == 0:
            return -1e9
        end = n if t_end is None else min(n, t_end + 1)
        best = -1e18
        for tp in range(max(0, t_start), end):
            prefix_min = float(np.min(r1[max(0, t_start):tp + 1]))
            best = max(best, min(float(r2[tp]), prefix_min))
        return float(best)

    def verify_response_guarantee(
        self,
        trace: List[float] | np.ndarray,
        safety_ceiling: float = 0.95,
        trigger_threshold: float = 0.80,
        recovery_target: float = 0.65,
        response_deadline_steps: int = 4
    ) -> Dict[str, Any]:
        """
        Verifica simultaneamente duas fórmulas formais sobre o traço:
        1. Safety Invariance: phi_safe = G (x_t <= safety_ceiling)
        2. Bounded Response (Liveness): phi_resp = G (x_t >= trigger_threshold -> F_[0, k] (x_{t'} <= recovery_target))
        Retorna a robustez STL exata e o veredito de conformidade temporal.
        """
        t0 = time.perf_counter()
        arr = np.array(trace, dtype=np.float64).reshape(-1)
        n = len(arr)

        # 1. Safety: G(x <= safety_ceiling)
        rob_safety = self.eval_always_upper(arr, safety_ceiling)

        # 2. Response: min_t max( -(x_t - trigger_threshold), max_{t' in [t, t+k]} (recovery_target - x_{t'}) )
        response_margins = []
        triggers_detected = 0
        triggers_recovered_on_time = 0

        for t in range(n):
            rho_not_trigger = trigger_threshold - float(arr[t])
            end_w = min(n - 1, t + response_deadline_steps)
            rho_f_recover = self.eval_eventually_below(arr, recovery_target, t_start=t, t_end=end_w)

            # Implicação (A -> B) == (~A v B) == max(-rho_A, rho_B)
            rho_imp = max(rho_not_trigger, rho_f_recover)
            response_margins.append(rho_imp)

            if arr[t] >= trigger_threshold:
                triggers_detected += 1
                if rho_f_recover >= 0.0:
                    triggers_recovered_on_time += 1

        rob_response = float(min(response_margins)) if response_margins else 0.0
        overall_rob = min(rob_safety, rob_response)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "STL_TEMPORAL_SPEC_SATISFIED" if overall_rob >= 0.0 else "STL_TEMPORAL_VIOLATION",
            "satisfied": bool(overall_rob >= 0.0),
            "overall_stl_robustness": round(overall_rob, 6),
            "safety_invariance_robustness": round(rob_safety, 6),
            "bounded_response_robustness": round(rob_response, 6),
            "trace_length": n,
            "triggers_detected": triggers_detected,
            "triggers_recovered_in_window": triggers_recovered_on_time,
            "elapsed_us": round(elapsed_us, 2)
        }
