"""LTI Lyapunov Recurrent State Governor (AetherMind Cognitive Substrate).

Áreas 06 & 13: Metacognição, Teoria de Controle e Estabilidade Matemática.
Implementa o motor de reflexão profunda em espaço de estados contínuo:
x[k+1] = A * x[k] + B * u[k].
Garante incondicionalmente estabilidade assintótica via raio espectral de Lyapunov:
rho(A) = max |lambda_i| <= 0.95, impedindo divergência cognitiva.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class LTILyapunovGovernor:
    """Governador Metacognitivo de Espaço de Estados LTI Estável de Lyapunov."""

    def __init__(self, state_dim: int = 16, max_spectral_radius: float = 0.95):
        self.state_dim = state_dim
        self.max_spectral_radius = max_spectral_radius
        self.A = np.zeros((state_dim, state_dim))
        self.B = np.zeros((state_dim, state_dim))
        self.current_state = np.zeros(state_dim)
        self._initialize_stable_matrices()

    def _initialize_stable_matrices(self) -> None:
        """Inicializa matrizes A e B garantindo raio espectral estável rho(A) <= 0.95."""
        rng = np.random.default_rng(42)
        # Matriz ortogonal aleatória com decaimento
        raw_A = rng.normal(0, 1.0, (self.state_dim, self.state_dim))
        # Calcula autovalores
        eigenvalues = np.linalg.eigvals(raw_A)
        spectral_radius = float(np.max(np.abs(eigenvalues)))

        # Escalonamento forçado para estabilidade de Lyapunov (com margem de precisão flutuante)
        target_rho = self.max_spectral_radius * 0.995
        if spectral_radius > 0:
            self.A = raw_A * (target_rho / spectral_radius)
        else:
            self.A = np.eye(self.state_dim) * target_rho

        self.B = np.eye(self.state_dim) * 0.1

    def compute_stability_metrics(self) -> Dict[str, Any]:
        """Calcula autovalores e prova matemática de estabilidade assintótica."""
        eigenvalues = np.linalg.eigvals(self.A)
        spectral_radius = float(np.max(np.abs(eigenvalues)))
        is_lyapunov_stable = bool(spectral_radius <= (self.max_spectral_radius + 1e-6))

        return {
            "state_dimension": self.state_dim,
            "spectral_radius_rho": round(spectral_radius, 6),
            "max_allowed_rho": self.max_spectral_radius,
            "is_lyapunov_stable": is_lyapunov_stable,
            "top_eigenvalues_magnitude": [round(float(np.abs(ev)), 4) for ev in eigenvalues[:4]]
        }

    def deliberate_latent_steps(
        self,
        input_vector: np.ndarray,
        steps: int = 16,
        convergence_tol: float = 1e-4
    ) -> Dict[str, Any]:
        """Executa múltiplos passos de reflexão latente contínua até convergência de ponto fixo."""
        start = time.perf_counter()
        
        # Ajusta dimensões do vetor de entrada
        if len(input_vector) != self.state_dim:
            u = np.resize(input_vector, self.state_dim)
        else:
            u = input_vector

        x = np.copy(self.current_state)
        trajectory_energies = []
        converged_step = None

        for k in range(steps):
            x_next = np.dot(self.A, x) + np.dot(self.B, u)
            delta = float(np.linalg.norm(x_next - x))
            energy = float(np.dot(x_next, x_next))
            trajectory_energies.append(round(energy, 4))

            if delta < convergence_tol and converged_step is None:
                converged_step = k + 1

            x = x_next

        self.current_state = x
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "DELIBERATION_CONVERGED" if converged_step else "MAX_STEPS_REACHED",
            "converged_at_step": converged_step or steps,
            "total_steps_executed": steps,
            "final_state_norm": round(float(np.linalg.norm(x)), 4),
            "trajectory_energies": trajectory_energies[:8],
            "elapsed_ms": round(elapsed_ms, 3)
        }
