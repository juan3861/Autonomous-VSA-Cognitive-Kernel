"""Bare-Metal Rust LTO C-ABI Physics & Temporal Logic Accelerator Bridge.

Organ 50 do Substrato Cognitivo Não-LLM (AetherCOS v5.0 — Marco dos 50 Órgãos).
Conecta-se via `ctypes.CDLL` diretamente aos kernels nativos compilados com LTO em
`aether_cortex_vsa.dll`:
- `symplectic_yoshida4_coupled_f64`: Executa milhares de passos de integração simplética
  Yoshida de 4ª ordem em código de máquina nativo x86_64/AVX2 (centenas de vezes mais rápido que Python).
- `stl_globally_upper_robustness_f64`: Avalia robustez quantitativa STL em silício nativo.
Inclui fallback gracioso em NumPy caso a DLL não esteja presente.
"""
from __future__ import annotations

import ctypes
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np


class RustNativePhysicsKernel:
    """
    Ponte Bare-Metal para Aceleração Física Simplética e Lógica Temporal em Rust C-ABI.
    """

    def __init__(self, dll_path: Optional[str] = None):
        if dll_path is None:
            resolved = Path(__file__).parent.parent.parent / "aether_cortex_vsa" / "target" / "release" / "aether_cortex_vsa.dll"
            self.dll_path = str(resolved)
        else:
            self.dll_path = dll_path

        self.lib = None
        self.is_native_ready = False
        self._load_dll()

    def _load_dll(self) -> None:
        try:
            from .native_cortex_dll_singleton import get_native_cortex_dll
            cached = get_native_cortex_dll() if self.dll_path.endswith("aether_cortex_vsa.dll") else None
            lib = cached if cached is not None else (ctypes.CDLL(self.dll_path) if Path(self.dll_path).exists() else None)
            if lib is not None and hasattr(lib, "symplectic_yoshida4_coupled_f64") and hasattr(lib, "stl_globally_upper_robustness_f64"):
                lib.symplectic_yoshida4_coupled_f64.argtypes = [
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_size_t,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_size_t,
                ]
                lib.symplectic_yoshida4_coupled_f64.restype = ctypes.c_double

                lib.stl_globally_upper_robustness_f64.argtypes = [
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_size_t,
                    ctypes.c_double,
                ]
                lib.stl_globally_upper_robustness_f64.restype = ctypes.c_double

                self.lib = lib
                self.is_native_ready = True
        except Exception:
            self.is_native_ready = False

    def run_yoshida4_native(
        self,
        q0: List[float] | np.ndarray,
        p0: List[float] | np.ndarray,
        mass: float = 1.0,
        stiffness: float = 1.0,
        beta: float = 0.25,
        dt: float = 0.05,
        steps: int = 5000
    ) -> Dict[str, Any]:
        """Executa integração simplética Yoshida-4 de longo horizonte em código de máquina Rust."""
        t0 = time.perf_counter()
        q_arr = np.ascontiguousarray(q0, dtype=np.float64)
        p_arr = np.ascontiguousarray(p0, dtype=np.float64)
        dof = len(q_arr)

        if self.is_native_ready and self.lib is not None:
            max_drift = float(
                self.lib.symplectic_yoshida4_coupled_f64(
                    q_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    p_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    dof,
                    mass,
                    stiffness,
                    beta,
                    dt,
                    steps,
                )
            )
            backend = "aether_cortex_vsa.dll (Rust LTO x86_64)"
        else:
            from aethermind_cognitive_substrate.logic_symbolic.hamiltonian_symplectic_integrator import (
                HamiltonianSymplecticIntegrator
            )
            sim = HamiltonianSymplecticIntegrator(dof=dof, mass=mass, stiffness=stiffness, anharmonic_beta=beta)
            res_py = sim.simulate(q_arr, p_arr, dt=dt, steps=steps, order=4)
            q_arr = np.array(res_py["final_q"], dtype=np.float64)
            p_arr = np.array(res_py["final_p"], dtype=np.float64)
            max_drift = float(res_py["max_absolute_energy_drift"])
            backend = "numpy_fallback"

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "RUST_NATIVE_SYMPLECTIC_COMPLETED",
            "native_accelerated": self.is_native_ready,
            "backend": backend,
            "steps": steps,
            "dof": dof,
            "max_absolute_energy_drift": float(f"{max_drift:.3e}"),
            "final_q": [round(float(v), 5) for v in q_arr],
            "final_p": [round(float(v), 5) for v in p_arr],
            "elapsed_us": round(elapsed_us, 2),
            "steps_per_sec": round(steps / (elapsed_us / 1e6 + 1e-12), 1)
        }

    def eval_stl_globally_native(
        self,
        trace: List[float] | np.ndarray,
        upper_limit: float = 0.95
    ) -> Dict[str, Any]:
        """Avalia robustez quantitativa G(x_t <= upper_limit) diretamente na DLL Rust."""
        t0 = time.perf_counter()
        arr = np.ascontiguousarray(trace, dtype=np.float64)
        n = len(arr)

        if self.is_native_ready and self.lib is not None:
            rob = float(
                self.lib.stl_globally_upper_robustness_f64(
                    arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                    n,
                    upper_limit,
                )
            )
            backend = "aether_cortex_vsa.dll (Rust C-ABI)"
        else:
            rob = float(np.min(upper_limit - arr)) if n > 0 else -1e9
            backend = "numpy_fallback"

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "STL_GLOBALLY_EVALUATED",
            "native_accelerated": self.is_native_ready,
            "backend": backend,
            "trace_length": n,
            "upper_limit": upper_limit,
            "robustness": round(rob, 6),
            "satisfied": bool(rob >= 0.0),
            "elapsed_us": round(elapsed_us, 2)
        }
