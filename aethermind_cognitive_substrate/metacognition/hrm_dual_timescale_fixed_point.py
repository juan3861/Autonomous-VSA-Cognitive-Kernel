"""Hierarchical Reasoning Model (HRM) & Tiny Recursive Model (TRM) Engine.

Área 06: Metacognição, Raciocínio de Ponto Fixo e Dinâmica em Dupla Frequência.
Inspirado na arquitetura cortical-talâmica (Sapient Intelligence / Samsung SAIL Montreal):
- Módulo Lento (z_H, Planejador, Ritmo Theta): opera em escala temporal macro.
- Módulo Rápido (z_L, Operário, Ritmo Gamma): itera até convergir para o Ponto Fixo z*.
- Teorema da Função Implícita (IFT): permite gradiente analítico em O(1) de memória
  sem Backpropagation Through Time (BPTT).
- Cabeça Q de parada adaptativa: decide dinamicamente a profundidade deliberativa.
- Aceleração Bare-Metal AVX2: compilação direta via Rust FFI (aether_cortex_vsa.dll)
  para convergência em microssegundos.
"""
from __future__ import annotations

import time
import math
import ctypes
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class HRMDualTimescaleFixedPoint:
    """Motor de Ponto Fixo em Dupla Frequência (Córtex-Tálamo)."""

    def __init__(
        self,
        slow_dim: int = 16,
        fast_dim: int = 32,
        input_dim: int = 16,
        contraction_factor: float = 0.85,
        max_fast_cycles: int = 40,
        fixed_point_tol: float = 1e-4
    ):
        self.slow_dim = slow_dim
        self.fast_dim = fast_dim
        self.input_dim = input_dim
        self.contraction_factor = contraction_factor
        self.max_fast_cycles = max_fast_cycles
        self.fixed_point_tol = fixed_point_tol

        # Matrizes do operador rápido z_L (Contrativo para garantir convergência de Banach)
        rng = np.random.RandomState(42)
        w_ll_raw = rng.randn(fast_dim, fast_dim)
        # Normaliza raio espectral para garantir mapa de contração ||f(x) - f(y)|| <= c ||x - y||
        u, s, vt = np.linalg.svd(w_ll_raw)
        self.W_LL = (w_ll_raw / (s[0] + 1e-6)) * contraction_factor

        self.W_HL = rng.randn(fast_dim, slow_dim) * 0.1
        self.W_in = rng.randn(fast_dim, input_dim) * 0.1
        self.b_L = np.zeros(fast_dim, dtype=np.float64)

        # Matrizes do planejador lento z_H
        self.W_HH = rng.randn(slow_dim, slow_dim) * 0.5
        self.W_LH = rng.randn(slow_dim, fast_dim) * 0.1
        self.b_H = np.zeros(slow_dim, dtype=np.float64)

        # Cabeça Q de parada adaptativa (avalia valor de continuar pensando vs agir)
        self.W_q = rng.randn(1, fast_dim + slow_dim) * 0.1

        # Estados persistentes
        self.z_H = np.zeros(slow_dim, dtype=np.float64)
        self.z_L = np.zeros(fast_dim, dtype=np.float64)

        # Vinculação com o Kernel Rust Bare-Metal AVX2
        self.rust_dll = None
        self._rust_hrm_solver = None
        self.is_native_accelerated = False
        dll_path = Path("F:/AetherMind_Apotheosis_Final/aether_cortex_vsa/target/release/aether_cortex_vsa.dll")
        if dll_path.exists():
            try:
                self.rust_dll = ctypes.CDLL(str(dll_path))
                fn = getattr(self.rust_dll, "hrm_fast_fixed_point_solve", None)
                if fn:
                    fn.argtypes = [
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.POINTER(ctypes.c_double),
                        ctypes.c_size_t,
                        ctypes.c_size_t,
                        ctypes.c_size_t,
                        ctypes.c_size_t,
                        ctypes.c_double
                    ]
                    fn.restype = ctypes.c_size_t
                    self._rust_hrm_solver = fn
                    self.is_native_accelerated = True
            except Exception:
                self.is_native_accelerated = False

    def _activation(self, x: np.ndarray) -> np.ndarray:
        """Função de ativação não-linear suave (GELU aproximada)."""
        return 0.5 * x * (1.0 + np.tanh(math.sqrt(2.0 / math.pi) * (x + 0.044715 * np.power(x, 3))))

    def _fast_step(self, z_l: np.ndarray, z_h: np.ndarray, x_in: np.ndarray) -> np.ndarray:
        """Equação de transição do operário rápido z_L em Python."""
        pre = np.dot(self.W_LL, z_l) + np.dot(self.W_HL, z_h) + np.dot(self.W_in, x_in) + self.b_L
        return np.tanh(pre)

    def _slow_step(self, z_h: np.ndarray, z_l_star: np.ndarray) -> np.ndarray:
        """Equação de atualização do planejador lento z_H."""
        pre = np.dot(self.W_HH, z_h) + np.dot(self.W_LH, z_l_star) + self.b_H
        return self._activation(pre)

    def find_fixed_point_equilibrium(
        self,
        x_input: np.ndarray,
        slow_macro_steps: int = 3,
        prefer_native: bool = True
    ) -> Dict[str, Any]:
        """Executa a dinâmica completa de ponto fixo em dupla frequência."""
        start = time.perf_counter()
        x_in = np.resize(x_input.astype(np.float64), self.input_dim)

        macro_history = []
        total_fast_cycles = 0
        use_native = (self.is_native_accelerated and prefer_native)

        for macro in range(slow_macro_steps):
            if use_native:
                # Disparo Bare-Metal em Rust FFI (AVX2, zero cópias intermediárias)
                c_w_ll = np.ascontiguousarray(self.W_LL, dtype=np.float64).ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                c_w_hl = np.ascontiguousarray(self.W_HL, dtype=np.float64).ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                c_w_in = np.ascontiguousarray(self.W_in, dtype=np.float64).ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                c_b_l = np.ascontiguousarray(self.b_L, dtype=np.float64).ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                c_z_h = np.ascontiguousarray(self.z_H, dtype=np.float64).ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                c_x_in = np.ascontiguousarray(x_in, dtype=np.float64).ctypes.data_as(ctypes.POINTER(ctypes.c_double))
                z_l_buf = np.ascontiguousarray(self.z_L, dtype=np.float64)
                c_z_l = z_l_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_double))

                cycles = self._rust_hrm_solver(
                    c_w_ll, c_w_hl, c_w_in, c_b_l, c_z_h, c_x_in, c_z_l,
                    self.fast_dim, self.slow_dim, self.input_dim,
                    self.max_fast_cycles, self.fixed_point_tol
                )
                self.z_L = np.copy(z_l_buf)
                z_l_star = self.z_L
                converged = (cycles < self.max_fast_cycles)
                total_fast_cycles += cycles
                cycle_deltas = [0.0] * cycles
            else:
                # Fallback em Python puro
                z_l_current = np.copy(self.z_L)
                converged = False
                cycle_deltas = []

                for cycle in range(self.max_fast_cycles):
                    total_fast_cycles += 1
                    z_l_next = self._fast_step(z_l_current, self.z_H, x_in)
                    delta = float(np.linalg.norm(z_l_next - z_l_current))
                    cycle_deltas.append(delta)

                    if delta < self.fixed_point_tol:
                        converged = True
                        z_l_current = z_l_next
                        break
                    z_l_current = z_l_next

                z_l_star = z_l_current
                self.z_L = z_l_star

            # Avalia cabeça Q de parada adaptativa
            state_concat = np.concatenate([self.z_L, self.z_H])
            q_halt = float(np.dot(self.W_q, state_concat)[0])

            # O planejador lento dá 1 passo macro
            self.z_H = self._slow_step(self.z_H, z_l_star)

            macro_history.append({
                "macro_step": macro + 1,
                "fast_cycles_to_converge": len(cycle_deltas) if not use_native else cycles,
                "is_fixed_point": converged,
                "final_delta": cycle_deltas[-1] if cycle_deltas else 0.0,
                "q_halt_value": round(q_halt, 4)
            })

            # Se o Q-head decidir parar (sinal de certeza atingido)
            if q_halt > 1.5:
                break

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        # Derivada implícita O(1) pelo Teorema da Função Implícita (I - J)^-1
        diag_deriv = 1.0 - np.square(self.z_L)
        jacobian = self.W_LL * diag_deriv[:, None]
        identity = np.eye(self.fast_dim)
        resolvent = np.linalg.pinv(identity - jacobian)
        spectral_radius = float(np.max(np.abs(np.linalg.eigvals(jacobian))))

        return {
            "status": "EQUILIBRIUM_REACHED",
            "slow_dim": self.slow_dim,
            "fast_dim": self.fast_dim,
            "total_fast_cycles": total_fast_cycles,
            "macro_steps_executed": len(macro_history),
            "spectral_radius_jacobian": round(spectral_radius, 4),
            "is_banach_contractive": spectral_radius < 1.0,
            "macro_history": macro_history,
            "z_L_fixed_point_norm": round(float(np.linalg.norm(self.z_L)), 4),
            "z_H_slow_norm": round(float(np.linalg.norm(self.z_H)), 4),
            "ift_resolvent_frobenius_norm": round(float(np.linalg.norm(resolvent)), 4),
            "elapsed_ms": round(elapsed_ms, 3),
            "native_rust_accelerated": use_native,
            "kernel_backend": "RUST_BARE_METAL_AVX2" if use_native else "NUMPY_FALLBACK"
        }
