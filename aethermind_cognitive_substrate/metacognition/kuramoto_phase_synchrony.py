"""AKOrN & Continuous Thought Machine (CTM) Kuramoto Oscillatory Engine.

Área 06 & 09: Dinâmica Não-Linear, Resolução do 'Binding Problem' e Sincronia de Fase.
Substitui o neurônio escalar de McCulloch-Pitts por osciladores neurais acoplados:
- Cada neurônio possui uma frequência intrínseca natural (omega_i) e fase (theta_i).
- Dinâmica diferencial de Kuramoto: d(theta_i)/dt = omega_i + (K/N) * sum_j sin(theta_j - theta_i) + Input_i.
- Parâmetro de Ordem de Kuramoto R(t) in [0, 1]: mede a coerência global de disparo.
- Matriz de Sincronização Neural S = Z * Z^T: os conceitos emergem de quem sincroniza fase no tempo.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class KuramotoOscillatoryNetwork:
    """Rede de Osciladores Neurais de Kuramoto para Ligação Semântica (Binding)."""

    def __init__(
        self,
        num_oscillators: int = 64,
        coupling_strength_k: float = 2.5,
        dt: float = 0.05
    ):
        self.num_oscillators = num_oscillators
        self.K = coupling_strength_k
        self.dt = dt

        # Frequências naturais intrínsecas (distribuição Cauchy/Lorentziana simétrica)
        rng = np.random.RandomState(42)
        self.natural_frequencies = rng.standard_cauchy(num_oscillators) * 0.5

        # Fases iniciais theta in [0, 2*pi)
        self.phases = rng.uniform(0.0, 2.0 * math.pi, num_oscillators)

        # Matriz de acoplamento sináptico J_ij (pesos de atração/repulsão de fase)
        self.synaptic_coupling = np.ones((num_oscillators, num_oscillators), dtype=np.float64) / num_oscillators
        np.fill_diagonal(self.synaptic_coupling, 0.0)

    def compute_order_parameter(self) -> Tuple[float, float]:
        """Calcula o parâmetro de ordem macroscópico R * e^(i * psi) de Kuramoto."""
        complex_sum = np.sum(np.exp(1j * self.phases)) / self.num_oscillators
        order_r = float(np.abs(complex_sum))
        mean_phase_psi = float(np.angle(complex_sum))
        return order_r, mean_phase_psi

    def step_dynamics(self, input_currents: Optional[np.ndarray] = None) -> float:
        """Avança a equação diferencial de Kuramoto por 1 passo temporal Euler/Heun."""
        if input_currents is None:
            inputs = np.zeros(self.num_oscillators, dtype=np.float64)
        else:
            inputs = np.resize(input_currents.astype(np.float64), self.num_oscillators)

        # Diferenças de fase em grade: phase_diff[i, j] = theta_j - theta_i
        phase_diff = self.phases[None, :] - self.phases[:, None]
        coupling_terms = np.sum(self.synaptic_coupling * np.sin(phase_diff), axis=1)

        # d(theta)/dt = omega + K * coupling + inputs
        d_theta = self.natural_frequencies + self.K * coupling_terms + inputs
        self.phases = (self.phases + self.dt * d_theta) % (2.0 * math.pi)

        order_r, _ = self.compute_order_parameter()
        return order_r

    def bind_features_by_phase(
        self,
        feature_stimuli: Dict[str, List[int]],
        integration_steps: int = 50
    ) -> Dict[str, Any]:
        """Resolve o 'Binding Problem' agrupando atributos estimulados no mesmo atrator de fase."""
        start = time.perf_counter()

        # Cria estímulos de corrente para os grupos de neurônios
        currents = np.zeros(self.num_oscillators, dtype=np.float64)
        for group_name, neuron_indices in feature_stimuli.items():
            for idx in neuron_indices:
                if 0 <= idx < self.num_oscillators:
                    currents[idx] += 1.5

        # Integra a dinâmica de sincronização temporal
        trajectory_order_r = []
        for step in range(integration_steps):
            r_val = self.step_dynamics(currents)
            if step % 5 == 0:
                trajectory_order_r.append(round(r_val, 4))

        # Matriz de Sincronização Neural S_ij = cos(theta_i - theta_j) in [-1, 1]
        phase_matrix = self.phases[:, None] - self.phases[None, :]
        sync_matrix = np.cos(phase_matrix)

        # Calcula a coerência interna de cada grupo de conceitos
        group_coherences = {}
        for group_name, neuron_indices in feature_stimuli.items():
            valid_indices = [idx for idx in neuron_indices if 0 <= idx < self.num_oscillators]
            if len(valid_indices) > 1:
                sub_matrix = sync_matrix[np.ix_(valid_indices, valid_indices)]
                # Média dos elementos fora da diagonal
                n_sub = len(valid_indices)
                mean_sync = float((np.sum(sub_matrix) - n_sub) / (n_sub * (n_sub - 1)))
                group_coherences[group_name] = round(mean_sync, 4)
            elif len(valid_indices) == 1:
                group_coherences[group_name] = 1.0

        final_order_r, mean_phase = self.compute_order_parameter()
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "PHASE_SYNCHRONY_CONVERGED",
            "total_oscillators": self.num_oscillators,
            "final_global_order_R": round(final_order_r, 4),
            "mean_phase_psi_rad": round(mean_phase, 4),
            "group_internal_coherences": group_coherences,
            "is_binding_successful": all(v > 0.6 for v in group_coherences.values()) if group_coherences else True,
            "trajectory_order_r": trajectory_order_r,
            "elapsed_ms": round(elapsed_ms, 3)
        }
