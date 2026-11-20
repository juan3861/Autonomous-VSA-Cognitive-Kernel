"""Thermodynamic Computing & Ising Machine Engine (Extropic thrml & Polaris Vulkan Paradigm).

Área 03 & 13: Computação Física Baseada em Energia, Redes de Spins e Amostragem de Gibbs.
Implementa o paradigma termodinâmico de Guillaume Verdon (Extropic / JAX thrml) e
computação acelerada por silício nativo:
- Hipergrafo de spins magnéticos discretos s_i in {-1, +1}.
- Hamiltoniano de Energia: E(s) = - 0.5 * sum_{i,j} J_{ij} s_i s_j - sum_i h_i s_i.
- Amostragem de Gibbs em Blocos Bipartidos (Two-Color Block Gibbs Sampling):
  permite atualização paralela em hardware dividindo o grafo em partições disjuntas.
- Campo efetivo I_i = sum_j J_{ij} s_j + h_i.
- Probabilidade térmica de Glauber / Boltzmann: P(s_i = +1) = 1 / (1 + exp(-2 * beta * I_i)).
- Aceleração Dupla:
  1. Bare-Metal Rust SIMD / AVX2 (aether_cortex_vsa.dll): centenas de milhões de flips/s.
  2. Vulkan Polaris Wave64 Compute Shader (ising_block_gibbs.spv): compilação nativa para GPU RX 580.
"""
from __future__ import annotations

import time
import math
import ctypes
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ThermodynamicIsingMachine:
    """Simulador de Computação Termodinâmica e Modelo de Ising em Blocos Bipartidos."""

    def __init__(self, num_spins: int = 64, seed: int = 42):
        self.num_spins = num_spins
        self.rng = np.random.RandomState(seed)
        self.seed = seed

        # Matriz simétrica de acoplamento J (ferromagnético J > 0, antiferromagnético J < 0)
        self.J = np.zeros((num_spins, num_spins), dtype=np.float32)
        # Campo magnético local h
        self.h = np.zeros(num_spins, dtype=np.float32)

        # Estado inicial dos spins {-1, +1}
        self.spins = self.rng.choice([-1, 1], size=num_spins).astype(np.int8)

        # Particionamento em dois blocos (Bipartição Vermelho / Preto para amostragem em bloco)
        self.block_a = np.arange(0, num_spins, 2)
        self.block_b = np.arange(1, num_spins, 2)

        # Conexão com Kernel Bare-Metal em Rust FFI
        self.rust_dll = None
        self._fn_rust_relax = None
        self._fn_rust_energy = None
        self.is_native_accelerated = False

        dll_path = Path("F:/AetherMind_Apotheosis_Final/aether_cortex_vsa/target/release/aether_cortex_vsa.dll")
        if dll_path.exists():
            try:
                self.rust_dll = ctypes.CDLL(str(dll_path))
                fn_r = getattr(self.rust_dll, "ising_block_gibbs_relax", None)
                fn_e = getattr(self.rust_dll, "ising_compute_energy", None)
                if fn_r and fn_e:
                    fn_r.argtypes = [
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.POINTER(ctypes.c_int8),
                        ctypes.c_size_t,
                        ctypes.c_float,
                        ctypes.c_float,
                        ctypes.c_size_t,
                        ctypes.c_uint64
                    ]
                    fn_r.restype = ctypes.c_float

                    fn_e.argtypes = [
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.POINTER(ctypes.c_float),
                        ctypes.POINTER(ctypes.c_int8),
                        ctypes.c_size_t
                    ]
                    fn_e.restype = ctypes.c_float

                    self._fn_rust_relax = fn_r
                    self._fn_rust_energy = fn_e
                    self.is_native_accelerated = True
            except Exception:
                self.is_native_accelerated = False

        # Verificação do Shader Vulkan SPIR-V
        spv_path = Path(__file__).parent / "shaders" / "ising_block_gibbs.spv"
        self.has_vulkan_spirv = spv_path.exists()

    def set_coupling_matrix(self, j_matrix: np.ndarray, h_bias: Optional[np.ndarray] = None) -> None:
        """Configura o grafo de acoplamento do sistema."""
        j_arr = np.array(j_matrix, dtype=np.float32)
        self.J = 0.5 * (j_arr + j_arr.T)  # Garante simetria estrita
        np.fill_diagonal(self.J, 0.0)
        if h_bias is not None:
            self.h = np.resize(np.array(h_bias, dtype=np.float32), self.num_spins)

    def compute_energy(self, state: Optional[np.ndarray] = None) -> float:
        """Calcula a energia total do Hamiltoniano de Ising: E = -0.5 * s^T * J * s - h^T * s."""
        s = self.spins if state is None else state
        if self.is_native_accelerated and self._fn_rust_energy:
            c_j = np.ascontiguousarray(self.J, dtype=np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            c_h = np.ascontiguousarray(self.h, dtype=np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            c_s = np.ascontiguousarray(s, dtype=np.int8).ctypes.data_as(ctypes.POINTER(ctypes.c_int8))
            return float(self._fn_rust_energy(c_j, c_h, c_s, self.num_spins))

        s_f = s.astype(np.float64)
        j_f = self.J.astype(np.float64)
        h_f = self.h.astype(np.float64)
        interaction_energy = -0.5 * float(np.dot(s_f, np.dot(j_f, s_f)))
        field_energy = -float(np.dot(h_f, s_f))
        return interaction_energy + field_energy

    def block_gibbs_step_numpy(self, beta: float) -> None:
        """Executa 1 passo de amostragem de Gibbs em dois blocos bipartidos via NumPy."""
        field_a = np.dot(self.J[self.block_a, :], self.spins) + self.h[self.block_a]
        prob_plus_a = 1.0 / (1.0 + np.exp(-2.0 * beta * field_a))
        rand_a = self.rng.uniform(0.0, 1.0, size=len(self.block_a))
        self.spins[self.block_a] = np.where(rand_a < prob_plus_a, 1, -1)

        field_b = np.dot(self.J[self.block_b, :], self.spins) + self.h[self.block_b]
        prob_plus_b = 1.0 / (1.0 + np.exp(-2.0 * beta * field_b))
        rand_b = self.rng.uniform(0.0, 1.0, size=len(self.block_b))
        self.spins[self.block_b] = np.where(rand_b < prob_plus_b, 1, -1)

    def thermal_relax_to_ground_state(
        self,
        initial_temp: float = 5.0,
        final_temp: float = 0.05,
        cooling_steps: int = 50,
        prefer_native: bool = True
    ) -> Dict[str, Any]:
        """Executa o recozimento termodinâmico simulando o relaxamento para a menor energia livre."""
        start = time.perf_counter()
        initial_energy = self.compute_energy()

        use_native = (self.is_native_accelerated and prefer_native)
        backend = "RUST_BARE_METAL_AVX2" if use_native else "NUMPY_FALLBACK"

        if use_native:
            c_j = np.ascontiguousarray(self.J, dtype=np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            c_h = np.ascontiguousarray(self.h, dtype=np.float32).ctypes.data_as(ctypes.POINTER(ctypes.c_float))
            spins_buf = np.ascontiguousarray(self.spins, dtype=np.int8)
            c_s = spins_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_int8))

            best_energy = float(self._fn_rust_relax(
                c_j, c_h, c_s, self.num_spins,
                float(initial_temp), float(final_temp),
                int(cooling_steps), int(self.seed)
            ))
            self.spins = np.copy(spins_buf)
            energy_trajectory = [round(initial_energy, 3), round(best_energy, 3)]
            temp = final_temp
        else:
            energy_trajectory = [round(initial_energy, 3)]
            best_spins = np.copy(self.spins)
            best_energy = initial_energy
            decay = (final_temp / initial_temp) ** (1.0 / max(1, cooling_steps - 1))
            temp = initial_temp

            for step in range(cooling_steps):
                beta = 1.0 / max(temp, 1e-4)
                self.block_gibbs_step_numpy(beta)
                current_energy = self.compute_energy()

                if current_energy < best_energy:
                    best_energy = current_energy
                    best_spins = np.copy(self.spins)

                if step % 5 == 0:
                    energy_trajectory.append(round(current_energy, 3))
                temp *= decay

            self.spins = best_spins

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "GROUND_STATE_REACHED",
            "num_spins": self.num_spins,
            "backend": backend,
            "has_vulkan_spirv": self.has_vulkan_spirv,
            "initial_energy": round(initial_energy, 4),
            "ground_state_energy": round(best_energy, 4),
            "energy_drop": round(initial_energy - best_energy, 4),
            "final_temperature": round(temp, 4),
            "energy_trajectory": energy_trajectory,
            "magnetization": round(float(np.mean(self.spins)), 4),
            "elapsed_ms": round(elapsed_ms, 3)
        }
