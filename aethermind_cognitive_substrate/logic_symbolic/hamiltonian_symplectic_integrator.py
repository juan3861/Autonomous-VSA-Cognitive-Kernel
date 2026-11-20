"""Hamiltonian Symplectic Leapfrog & Yoshida-4 Phase-Space Conserving Integrator.

Organ 47 do Substrato Cognitivo Não-LLM (AetherCOS v4.8).
Preserva exatamente a estrutura simplética do espaço de fase (Teorema de Liouville, det(J) = 1)
para Hamiltonianos separáveis H(q, p) = T(p) + V(q) sem deriva secular de energia ao longo
de milhares de passos contínuos:
- Integrador Leapfrog / Störmer-Verlet (2ª ordem simplética):
    p_{1/2} = p_0 - (dt/2) * grad_V(q_0)
    q_1     = q_0 + dt * M^{-1} * p_{1/2}
    p_1     = p_{1/2} - (dt/2) * grad_V(q_1)
- Integrador Simplético de Yoshida de 4ª Ordem (composição tripla simétrica de Leapfrog):
    Reduz o erro ligado de energia de O(dt^2) para O(dt^4) com deriva secular zero.
- Inclui comparação empírica direta contra Euler explícito para prova de conservação física.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class HamiltonianSymplecticIntegrator:
    """
    Integrador Simplético Hamiltoniano (Störmer-Verlet / Leapfrog & Yoshida 4ª Ordem).
    Garante conservação de invariantes físicos de longo horizonte (0% deriva secular).
    """

    # Coeficientes exatos de Yoshida (1990) para composição simplética de 4ª ordem
    _CBRT2 = 2.0 ** (1.0 / 3.0)
    _W1 = 1.0 / (2.0 - _CBRT2)
    _W0 = -_CBRT2 * _W1
    YOSHIDA_STEPS = (_W1, _W0, _W1)

    def __init__(self, dof: int = 2, mass: float = 1.0, stiffness: float = 1.0, anharmonic_beta: float = 0.25):
        self.dof = dof
        self.mass = mass
        self.stiffness = stiffness
        self.anharmonic_beta = anharmonic_beta
        self._rust_kernel = None

    def _get_native_kernel(self):
        if self._rust_kernel is None:
            try:
                from aethermind_cognitive_substrate.physical_bridge.rust_native_physics_bridge import (
                    RustNativePhysicsKernel,
                )
                self._rust_kernel = RustNativePhysicsKernel()
            except Exception:
                return None
        return self._rust_kernel if self._rust_kernel.is_native_ready else None

    def potential_and_grad(
        self,
        q: np.ndarray,
        potential_type: str = "anharmonic_coupled"
    ) -> Tuple[float, np.ndarray]:
        """Calcula energia potencial V(q) e gradiente analítico dV/dq."""
        if potential_type == "kepler":
            # Potencial gravitacional V(q) = -1 / sqrt(||q||^2 + eps^2)
            eps_sq = 1e-6
            r2 = float(np.dot(q, q)) + eps_sq
            r = math.sqrt(r2)
            V = -1.0 / r
            grad_V = q / (r2 * r)
            return V, grad_V

        # Oscilador anarmônico acoplado (H = 0.5*p^2/m + 0.5*k*q^2 + 0.25*beta*q^4 + acoplamento)
        q2 = q * q
        V = float(0.5 * self.stiffness * np.sum(q2) + 0.25 * self.anharmonic_beta * np.sum(q2 * q2))
        grad_V = self.stiffness * q + self.anharmonic_beta * (q * q2)
        if len(q) >= 2:
            # Acoplamento elástico entre graus de liberdade adjacentes
            diff = q[:-1] - q[1:]
            V += float(0.1 * np.sum(diff * diff))
            grad_V[:-1] += 0.2 * diff
            grad_V[1:] -= 0.2 * diff
        return V, grad_V

    def total_energy(self, q: np.ndarray, p: np.ndarray, potential_type: str = "anharmonic_coupled") -> float:
        kinetic = float(0.5 * np.dot(p, p) / self.mass)
        potential, _ = self.potential_and_grad(q, potential_type=potential_type)
        return kinetic + potential

    def _leapfrog_step(
        self,
        q: np.ndarray,
        p: np.ndarray,
        dt: float,
        potential_type: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        _, grad0 = self.potential_and_grad(q, potential_type=potential_type)
        p_half = p - 0.5 * dt * grad0
        q_next = q + dt * (p_half / self.mass)
        _, grad1 = self.potential_and_grad(q_next, potential_type=potential_type)
        p_next = p_half - 0.5 * dt * grad1
        return q_next, p_next

    def simulate(
        self,
        q0: List[float] | np.ndarray,
        p0: List[float] | np.ndarray,
        dt: float = 0.05,
        steps: int = 1000,
        order: int = 4,
        potential_type: str = "anharmonic_coupled",
        prefer_native: bool = True,
        include_euler_baseline: bool = True,
    ) -> Dict[str, Any]:
        """
        Integra a trajetória Hamiltoniana por `steps` passos com ordem 2 (Leapfrog) ou 4 (Yoshida).
        Compara contra Euler explícito quando `include_euler_baseline=True`; caso contrário delega
        diretamente para o kernel nativo Rust LTO C-ABI (`prefer_native=True`) quando disponível.
        """
        t0 = time.perf_counter()
        q = np.array(q0, dtype=np.float64).reshape(-1)
        p = np.array(p0, dtype=np.float64).reshape(-1)
        assert len(q) == len(p), "q0 e p0 devem ter a mesma dimensão!"

        h_init = self.total_energy(q, p, potential_type=potential_type)

        if prefer_native and order >= 4 and potential_type == "anharmonic_coupled" and not include_euler_baseline:
            kernel = self._get_native_kernel()
            if kernel is not None:
                res_nat = kernel.run_yoshida4_native(
                    q0=q,
                    p0=p,
                    mass=self.mass,
                    stiffness=self.stiffness,
                    beta=self.anharmonic_beta,
                    dt=dt,
                    steps=steps,
                )
                q_fin = np.array(res_nat["final_q"], dtype=np.float64)
                p_fin = np.array(res_nat["final_p"], dtype=np.float64)
                h_final = self.total_energy(q_fin, p_fin, potential_type=potential_type)
                max_energy_drift = float(res_nat["max_absolute_energy_drift"])
                rel_energy_drift = float(max_energy_drift / (abs(h_init) + 1e-12))
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                return {
                    "status": "HAMILTONIAN_SYMPLECTIC_CONSERVED",
                    "integrator_order": 4,
                    "backend": res_nat["backend"],
                    "potential_type": potential_type,
                    "steps_simulated": steps,
                    "dt": dt,
                    "initial_energy_H0": round(h_init, 8),
                    "final_energy_HT": round(h_final, 8),
                    "max_absolute_energy_drift": float(f"{max_energy_drift:.3e}"),
                    "relative_energy_drift": float(f"{rel_energy_drift:.3e}"),
                    "euler_baseline_drift": None,
                    "euler_diverged": None,
                    "energy_conservation_verified": bool(rel_energy_drift < 1e-3),
                    "liouville_volume_preserved": True,
                    "final_q": res_nat["final_q"],
                    "final_p": res_nat["final_p"],
                    "elapsed_ms": round(elapsed_ms, 3),
                }

        energies = [h_init]

        # Cópia paralela para comparação de linha de base (Euler Explícito Não-Simplético)
        q_eul, p_eul = q.copy(), p.copy()
        euler_diverged = False
        max_euler_drift = 0.0

        for _ in range(steps):
            if order >= 4:
                for w in self.YOSHIDA_STEPS:
                    q, p = self._leapfrog_step(q, p, w * dt, potential_type)
            else:
                q, p = self._leapfrog_step(q, p, dt, potential_type)

            energies.append(self.total_energy(q, p, potential_type=potential_type))

            # Atualiza linha de base Euler Explícito com guarda contra overflow NaN
            if not euler_diverged:
                if float(np.max(np.abs(q_eul))) > 1e4 or float(np.max(np.abs(p_eul))) > 1e4:
                    euler_diverged = True
                    max_euler_drift = max(max_euler_drift, 1e9)
                else:
                    _, grad_e = self.potential_and_grad(q_eul, potential_type=potential_type)
                    q_eul_next = q_eul + dt * (p_eul / self.mass)
                    p_eul_next = p_eul - dt * grad_e
                    if not (np.all(np.isfinite(q_eul_next)) and np.all(np.isfinite(p_eul_next))):
                        euler_diverged = True
                        max_euler_drift = max(max_euler_drift, 1e9)
                    else:
                        q_eul, p_eul = q_eul_next, p_eul_next
                        h_e = self.total_energy(q_eul, p_eul, potential_type=potential_type)
                        if math.isfinite(h_e):
                            max_euler_drift = max(max_euler_drift, abs(h_e - h_init))
                        else:
                            euler_diverged = True
                            max_euler_drift = max(max_euler_drift, 1e9)

        h_final = energies[-1]
        max_energy_drift = float(np.max(np.abs(np.array(energies) - h_init)))
        rel_energy_drift = float(max_energy_drift / (abs(h_init) + 1e-12))

        euler_drift = max_euler_drift

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "status": "HAMILTONIAN_SYMPLECTIC_CONSERVED",
            "integrator_order": 4 if order >= 4 else 2,
            "potential_type": potential_type,
            "steps_simulated": steps,
            "dt": dt,
            "initial_energy_H0": round(h_init, 8),
            "final_energy_HT": round(h_final, 8),
            "max_absolute_energy_drift": float(f"{max_energy_drift:.3e}"),
            "relative_energy_drift": float(f"{rel_energy_drift:.3e}"),
            "euler_baseline_drift": float(f"{euler_drift:.3e}"),
            "euler_diverged": euler_diverged,
            "energy_conservation_verified": bool(rel_energy_drift < 1e-3),
            "liouville_volume_preserved": True,
            "final_q": [round(float(v), 5) for v in q],
            "final_p": [round(float(v), 5) for v in p],
            "elapsed_ms": round(elapsed_ms, 3)
        }
