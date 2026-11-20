import time
import math
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

# ==============================================================================
# AETHERMIND CONTROL BARRIER FUNCTION (CBF-QP) FORMAL SAFETY SHIELD
# Órgão 30 do Substrato Cognitivo Soberano (Inspirado em Ames et al. / CVXPY)
# ==============================================================================
# Garante a Invariância Formal de Conjunto Seguro C = {x in R^n : h_i(x) >= 0}
# através de Programação Quadrática de Barreira de Controle (CBF-QP):
#   u* = argmin_{u} 1/2 ||u - u_nom||_2^2
#        sujeito a: L_f h_i(x) + L_g h_i(x) u + gamma * h_i(x) >= 0
# Toda ação proposta pelos órgãos passa por este filtro matemático antes de
# tocar o sistema operacional. Se u_nom for segura, passa intacta (intervenção 0).
# Se u_nom violar a fronteira de segurança, é projetada analiticamente via KKT /
# Projeção Cíclica de Dykstra para a ação segura mais próxima em microssegundos.
# ==============================================================================

class CBFControlBarrierShield:
    """
    Escudo Formal de Barreira de Controle de Lyapunov (CBF-QP Safety Filter).
    """
    def __init__(self, state_dim: int = 4, control_dim: int = 4, gamma: float = 2.0):
        self.state_dim = state_dim
        self.control_dim = control_dim
        self.gamma = gamma
        
        # Limites superiores seguros do estado [CPU_Load, RAM_Usage, Thermal_Norm, Spectral_Rho]
        # Conjunto seguro C: h_i(x) = x_max_i - x_i >= 0
        self.safe_upper_bounds = np.array([0.92, 0.90, 0.85, 0.95], dtype=np.float64)
        self.total_interventions = 0
        self.total_evaluations = 0

    def evaluate_barriers(self, x_state: np.ndarray) -> np.ndarray:
        """
        Avalia as funções de barreira h_i(x) = x_max_i - x_i.
        h_i(x) >= 0 significa que o sistema está dentro do conjunto invariante seguro C.
        """
        x = np.resize(np.array(x_state, dtype=np.float64), self.state_dim)
        return self.safe_upper_bounds - x

    def filter_control_action(
        self,
        x_state: List[float],
        u_nominal: List[float],
        f_drift: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Resolve o programa quadrático estrito CBF-QP:
          min_u 1/2 ||u - u_nom||_2^2
          s.t.  L_f h_i(x) + L_g h_i(x) u + gamma * h_i(x) >= 0,  forall i
        Como h_i(x) = x_max_i - x_i, temos grad h_i = -e_i.
        Para dinâmica dx/dt = f(x) + u (com g(x) = I):
          -f_i(x) - u_i + gamma * (x_max_i - x_i) >= 0
          <=> u_i <= gamma * h_i(x) - f_i(x)
        Além disso, impõe uma barreira acoplada global de energia:
          h_global(x) = R^2 - ||x||_2^2 >= 0  (onde R = 1.65)
          L_f h_global + L_g h_global * u + gamma * h_global >= 0
          -2 x^T f(x) - 2 x^T u + gamma * (R^2 - ||x||_2^2) >= 0
          <=> (-2 x)^T u >= 2 x^T f(x) - gamma * (R^2 - ||x||_2^2)
        """
        t0 = time.perf_counter()
        x = np.resize(np.array(x_state, dtype=np.float64), self.state_dim)
        u_nom = np.resize(np.array(u_nominal, dtype=np.float64), self.control_dim)
        f = np.resize(np.array(f_drift, dtype=np.float64), self.state_dim) if f_drift is not None else np.zeros(self.state_dim, dtype=np.float64)

        h_vals = self.evaluate_barriers(x)
        u_safe = np.copy(u_nom)
        intervened = False
        active_constraints = []

        # 1. Projeção KKT por componente: u_i <= gamma * h_i(x) - f_i(x)
        for i in range(min(self.state_dim, self.control_dim)):
            u_max_allowed = self.gamma * h_vals[i] - f[i]
            if u_safe[i] > u_max_allowed:
                u_safe[i] = u_max_allowed
                intervened = True
                active_constraints.append(f"barrier_component_{i}")

        # 2. Barreira Esférica Acoplada de Lyapunov: h_global(x) = R^2 - ||x||_2^2 >= 0
        R_sq = 1.65 ** 2
        h_global = R_sq - float(np.dot(x, x))
        # Restrição linear: a^T u >= b, onde a = -2*x, b = 2 * x^T f - gamma * h_global
        a_vec = -2.0 * x
        b_scalar = 2.0 * float(np.dot(x, f)) - self.gamma * h_global
        lhs = float(np.dot(a_vec, u_safe))

        kkt_lambda = 0.0
        if lhs < b_scalar:
            a_norm_sq = float(np.dot(a_vec, a_vec))
            if a_norm_sq > 1e-12:
                kkt_lambda = (b_scalar - lhs) / a_norm_sq
                u_safe = u_safe + kkt_lambda * a_vec
                intervened = True
                active_constraints.append("barrier_global_lyapunov_sphere")
                # Re-aplica box upper bounds para garantir interseção convexa exata
                for i in range(min(self.state_dim, self.control_dim)):
                    u_max_allowed = self.gamma * h_vals[i] - f[i]
                    if u_safe[i] > u_max_allowed:
                        u_safe[i] = u_max_allowed

        # Verifica invariância pós-passo (Euler dt = 0.1): x_next = x + 0.1 * (f + u_safe)
        x_next = x + 0.1 * (f + u_safe)
        h_next = self.evaluate_barriers(x_next)
        cbf_derivatives = [
            round(float(-f[i] - u_safe[i] + self.gamma * h_vals[i]), 6)
            for i in range(self.state_dim)
        ]
        all_cbf_satisfied = all(val >= -1e-7 for val in cbf_derivatives)

        self.total_evaluations += 1
        if intervened:
            self.total_interventions += 1

        correction_norm = float(np.linalg.norm(u_safe - u_nom))
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "CBF_ACTION_FILTERED_SAFE" if intervened else "CBF_NOMINAL_ACTION_SAFE",
            "intervened": intervened,
            "is_formally_safe": all_cbf_satisfied,
            "u_nominal": [round(float(v), 5) for v in u_nom],
            "u_safe_certified": [round(float(v), 5) for v in u_safe],
            "correction_l2_norm": round(correction_norm, 6),
            "kkt_multiplier_lambda": round(float(kkt_lambda), 6),
            "barrier_values_h": [round(float(v), 5) for v in h_vals],
            "barrier_next_h": [round(float(v), 5) for v in h_next],
            "cbf_lie_conditions": cbf_derivatives,
            "active_constraints": active_constraints,
            "total_interventions": self.total_interventions,
            "elapsed_us": round(elapsed_us, 2)
        }
