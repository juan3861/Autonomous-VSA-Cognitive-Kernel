"""Centralized Singleton Loader & Warm Cache for Bare-Metal Native Rust Cortex DLL.

Elimina carregamento redundante via `ctypes.CDLL` entre múltiplos órgãos do sistema
e mantém assinaturas C-ABI pré-configuradas para chamadas em microssegundos.
Utiliza a camada de abstração de plataforma `platform_compat` para suporte multiplataforma.
"""
from __future__ import annotations

import ctypes
from typing import Optional

from .platform_compat import load_native_library

_CACHED_LIB: Optional[ctypes.CDLL] = None
_INIT_ATTEMPTED: bool = False


def get_native_cortex_dll() -> Optional[ctypes.CDLL]:
    """Retorna o handle singleton para o kernel Rust nativo com assinaturas C-ABI aquecidas."""
    global _CACHED_LIB, _INIT_ATTEMPTED
    if _INIT_ATTEMPTED:
        return _CACHED_LIB

    _INIT_ATTEMPTED = True
    lib = load_native_library("aether_cortex_vsa")
    if lib is None:
        _CACHED_LIB = None
        return None

    try:
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

        # 7. Assinatura Projeção Esparsa OMP (Orthogonal Matching Pursuit)
        if hasattr(lib, "omp_sparse_project_f64"):
            lib.omp_sparse_project_f64.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_double),
            ]
            lib.omp_sparse_project_f64.restype = ctypes.c_size_t

        # 8. Assinatura RRT* Nearest Neighbor & Radius Rewiring
        if hasattr(lib, "rrt_star_nearest_and_radius_f64"):
            lib.rrt_star_nearest_and_radius_f64.argtypes = [
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_size_t,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_double),
                ctypes.c_double,
                ctypes.POINTER(ctypes.c_size_t),
                ctypes.POINTER(ctypes.c_double),
                ctypes.POINTER(ctypes.c_size_t),
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_size_t),
            ]
            lib.rrt_star_nearest_and_radius_f64.restype = ctypes.c_int32

        # 9. Assinatura Fused VSA Expression Graph Bytecode VM (AVX2)
        if hasattr(lib, "vsa_eval_graph_bytecode"):
            lib.vsa_eval_graph_bytecode.argtypes = [
                ctypes.c_void_p,
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_uint64),
                ctypes.c_size_t,
                ctypes.POINTER(ctypes.c_uint32),
                ctypes.c_size_t,
            ]
            lib.vsa_eval_graph_bytecode.restype = ctypes.c_int32

        # 10. Assinaturas Native x86_64 AVX2 W^X JIT Emitter
        if hasattr(lib, "vsa_jit_compile_xor_chain"):
            lib.vsa_jit_compile_xor_chain.argtypes = [ctypes.c_size_t]
            lib.vsa_jit_compile_xor_chain.restype = ctypes.c_void_p
        if hasattr(lib, "vsa_jit_exec_xor_chain"):
            lib.vsa_jit_exec_xor_chain.argtypes = [
                ctypes.c_void_p,
                ctypes.POINTER(ctypes.POINTER(ctypes.c_uint64)),
                ctypes.POINTER(ctypes.c_uint64),
            ]
            lib.vsa_jit_exec_xor_chain.restype = ctypes.c_int32
        if hasattr(lib, "vsa_jit_free_xor_chain"):
            lib.vsa_jit_free_xor_chain.argtypes = [ctypes.c_void_p]
            lib.vsa_jit_free_xor_chain.restype = None

        _CACHED_LIB = lib
        return _CACHED_LIB
    except Exception:
        _CACHED_LIB = None
        return None
