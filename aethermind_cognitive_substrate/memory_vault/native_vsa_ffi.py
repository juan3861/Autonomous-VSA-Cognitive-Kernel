"""
C-ABI ctypes FFI bridge for Bare-Metal Native Rust 10,240-bit VSA DLL
Direct zero-copy in-memory operations in nanoseconds.
"""

import ctypes
import os
import sys
from pathlib import Path
from typing import Tuple
import numpy as np

WORDS = 160
BITS = WORDS * 64
BYTES = WORDS * 8

class NativeVSAFFI:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(NativeVSAFFI, cls).__new__(cls)
            cls._instance._init_dll()
        return cls._instance

    def _init_dll(self):
        dll_path = Path(__file__).parent.parent.parent / "aether_cortex_vsa" / "target" / "release" / "aether_cortex_vsa.dll"
        if not dll_path.exists():
            raise FileNotFoundError(f"Native VSA DLL not found at {dll_path}")

        self.lib = ctypes.CDLL(str(dll_path))

        # Define ctypes signatures
        self.lib.vsa_create_from_seed.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
        self.lib.vsa_create_from_seed.restype = None

        self.lib.vsa_bind.argtypes = [
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64)
        ]
        self.lib.vsa_bind.restype = None

        self.lib.vsa_hamming_distance.argtypes = [
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64)
        ]
        self.lib.vsa_hamming_distance.restype = ctypes.c_uint32

        self.lib.vsa_hamming_distance_batch.argtypes = [
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_uint32
        ]
        self.lib.vsa_hamming_distance_batch.restype = ctypes.c_uint32

        self.lib.vsa_bundle_two.argtypes = [
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.POINTER(ctypes.c_uint64),
            ctypes.c_uint64,
            ctypes.POINTER(ctypes.c_uint64)
        ]
        self.lib.vsa_bundle_two.restype = None

        self.lib.vsa_resonance_sigma.argtypes = [ctypes.c_uint32]
        self.lib.vsa_resonance_sigma.restype = ctypes.c_double

        self.lib.vsa_free_energy_friston.argtypes = [ctypes.c_uint32]
        self.lib.vsa_free_energy_friston.restype = ctypes.c_double

    def create_from_seed(self, seed: int) -> np.ndarray:
        arr = np.zeros(WORDS, dtype=np.uint64)
        ptr = arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        self.lib.vsa_create_from_seed(ctypes.c_uint64(seed), ptr)
        return arr

    def bind(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        assert a.dtype == np.uint64 and len(a) == WORDS
        assert b.dtype == np.uint64 and len(b) == WORDS
        out = np.zeros(WORDS, dtype=np.uint64)
        a_ptr = a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        out_ptr = out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        self.lib.vsa_bind(a_ptr, b_ptr, out_ptr)
        return out

    def hamming_distance(self, a: np.ndarray, b: np.ndarray) -> int:
        assert a.dtype == np.uint64 and len(a) == WORDS
        assert b.dtype == np.uint64 and len(b) == WORDS
        a_ptr = a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        return int(self.lib.vsa_hamming_distance(a_ptr, b_ptr))

    def hamming_distance_batch(self, a: np.ndarray, b: np.ndarray, n_iterations: int) -> int:
        assert a.dtype == np.uint64 and len(a) == WORDS
        assert b.dtype == np.uint64 and len(b) == WORDS
        a_ptr = a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        return int(self.lib.vsa_hamming_distance_batch(a_ptr, b_ptr, ctypes.c_uint32(n_iterations)))

    def bundle_two(self, a: np.ndarray, b: np.ndarray, tie_seed: int = 123456789) -> np.ndarray:
        assert a.dtype == np.uint64 and len(a) == WORDS
        assert b.dtype == np.uint64 and len(b) == WORDS
        out = np.zeros(WORDS, dtype=np.uint64)
        a_ptr = a.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        b_ptr = b.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        out_ptr = out.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        self.lib.vsa_bundle_two(a_ptr, b_ptr, ctypes.c_uint64(tie_seed), out_ptr)
        return out

    def resonance_sigma(self, dist: int) -> float:
        return float(self.lib.vsa_resonance_sigma(ctypes.c_uint32(dist)))

    def free_energy_friston(self, dist: int) -> float:
        return float(self.lib.vsa_free_energy_friston(ctypes.c_uint32(dist)))
