"""Centralized Singleton Loader & Warm Cache for Bare-Metal Native Rust Cortex DLL.

Elimina carregamento redundante via `ctypes.CDLL` entre múltiplos órgãos do sistema
e mantém assinaturas C-ABI pré-configuradas para chamadas em microssegundos.
"""
from __future__ import annotations

import ctypes
from pathlib import Path
from typing import Optional

_CACHED_LIB: Optional[ctypes.CDLL] = None
_INIT_ATTEMPTED: bool = False


def get_native_cortex_dll() -> Optional[ctypes.CDLL]:
    """Retorna o handle singleton para `aether_cortex_vsa.dll` com assinaturas aquecidas."""
    global _CACHED_LIB, _INIT_ATTEMPTED
    if _INIT_ATTEMPTED:
        return _CACHED_LIB

    _INIT_ATTEMPTED = True
    dll_path = Path(__file__).parent.parent.parent / "aether_cortex_vsa" / "target" / "release" / "aether_cortex_vsa.dll"
    if not dll_path.exists():
        _CACHED_LIB = None
        return None

    try:
        lib = ctypes.CDLL(str(dll_path))

        # 1. Assinaturas VSA 10.240 bits
        if hasattr(lib, "vsa_create_from_seed"):
            lib.vsa_create_from_seed.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
            lib.vsa_create_from_seed.restype = None

        # 2. Assinaturas Integrador Simplético Yoshida-4
        if hasattr(lib, "symplectic_yoshida4_coupled_f64"):
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

        # 3. Assinaturas Monitor de Robustez STL
        if hasattr(lib, "stl_globally_upper_robustness_f64"):
            lib.stl_globally_upper_robustness_f64.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_size_t,
                ctypes.c_double,
            ]
            lib.stl_globally_upper_robustness_f64.restype = ctypes.c_double

        # 4. Assinaturas Filtro SMC Partículas Não-Linear
        if hasattr(lib, "smc_quadratic_track_f64"):
            lib.smc_quadratic_track_f64.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_double,
                ctypes.c_uint64,
                ctypes.POINTER(ctypes.c_double),
            ]
            lib.smc_quadratic_track_f64.restype = ctypes.c_int32

        # 5. Assinaturas Equação de Stein / Lyapunov Smith Doubling
        if hasattr(lib, "lyapunov_smith_doubling_f64"):
            lib.lyapunov_smith_doubling_f64.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.c_double,
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_size_t),
            ]
            lib.lyapunov_smith_doubling_f64.restype = ctypes.c_double

        # 6. Assinatura Iteração de Potência Espectral (Raio Espectral LTO)
        if hasattr(lib, "spectral_power_iteration_f64"):
            lib.spectral_power_iteration_f64.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.c_double,
            ]
            lib.spectral_power_iteration_f64.restype = ctypes.c_double

        _CACHED_LIB = lib
        return _CACHED_LIB
    except Exception:
        _CACHED_LIB = None
        return None
