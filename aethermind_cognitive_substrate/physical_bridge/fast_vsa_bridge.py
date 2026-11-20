"""Unified Zero-Copy VSA Hardware Bridge (Cython C-Extension Primary + ctypes Fallback).

Automatically adds the Rust release library directory to Windows DLL search paths,
loads the zero-copy compiled Cython module `fast_vsa_ext` (~30-60 ns call latency),
and falls back cleanly to `NativeVSAFFI` if compiled `.pyd`/`.so` is unavailable.
"""
from __future__ import annotations

import os
import sys
from typing import Optional
import numpy as np

from .platform_compat import find_native_library_path, is_windows
from ..memory_vault.native_vsa_ffi import NativeVSAFFI

_CYTHON_EXT = None
_CYTHON_PROBED = False


def _load_cython_ext():
    global _CYTHON_EXT, _CYTHON_PROBED
    if _CYTHON_PROBED:
        return _CYTHON_EXT
    _CYTHON_PROBED = True

    lib_path = find_native_library_path("aether_cortex_vsa")
    if lib_path is not None and is_windows() and hasattr(os, "add_dll_directory"):
        try:
            os.add_dll_directory(str(lib_path.parent))
        except Exception:
            pass

    try:
        from . import fast_vsa_ext  # type: ignore
        _CYTHON_EXT = fast_vsa_ext
    except Exception:
        _CYTHON_EXT = None

    return _CYTHON_EXT


class FastVSABridge:
    """High-speed zero-copy 10,240-bit VSA dispatch bridge."""

    def __init__(self):
        self._cy = _load_cython_ext()
        self._ffi: Optional[NativeVSAFFI] = None if self._cy is not None else NativeVSAFFI()

    @property
    def backend_mode(self) -> str:
        return "CYTHON_ZERO_COPY" if self._cy is not None else "CTYPES_C_ABI"

    def create_from_seed(self, seed: int) -> np.ndarray:
        if self._cy is not None:
            return self._cy.cy_create_from_seed(seed)
        return self._ffi.create_from_seed(seed)

    def bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        if self._cy is not None:
            return self._cy.cy_bind(a, b)
        return self._ffi.bind(a, b)

    def bind_into(self, a: np.ndarray, b: np.ndarray, out: np.ndarray) -> None:
        if self._cy is not None:
            self._cy.cy_bind_into(a, b, out)
            return
        res = self._ffi.bind(a, b)
        out[:] = res

    def hamming_distance(self, a: np.ndarray, b: np.ndarray) -> int:
        if self._cy is not None:
            return int(self._cy.cy_hamming_distance(a, b))
        return int(self._ffi.hamming_distance(a, b))

    def hamming_distance_batch(self, a: np.ndarray, b: np.ndarray, n_iterations: int) -> int:
        if self._cy is not None:
            return int(self._cy.cy_hamming_distance_batch(a, b, n_iterations))
        return int(self._ffi.hamming_distance_batch(a, b, n_iterations))
