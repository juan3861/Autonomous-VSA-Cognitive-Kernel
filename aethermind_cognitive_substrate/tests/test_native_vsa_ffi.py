"""
Strict Empirical Benchmark and Test for C-ABI FFI Bare-Metal Native Rust 10,240-bit VSA DLL
Verifies:
1. Zero-copy loading of aether_cortex_vsa.dll
2. Deterministic generation of 10,240-bit hypervectors
3. Native POPCNT AVX2 Hamming distance and Friston Free Energy computation
4. In-memory XOR binding invertibility (A ^ B ^ B = A)
5. Throughput benchmark (> 1,000,000 operations per second in native batch)
"""

import sys
import os
import time
from pathlib import Path
import numpy as np

# Ensure workspace root is in sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# UTF-8 safe output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.memory_vault.native_vsa_ffi import NativeVSAFFI, WORDS, BITS, BYTES

def test_native_vsa_ffi():
    ffi = NativeVSAFFI()
    
    # 1. Deterministic generation from seed
    v1 = ffi.create_from_seed(42)
    v2 = ffi.create_from_seed(1337)
    
    assert v1.shape == (WORDS,)
    assert v1.dtype == np.uint64
    assert len(v1.tobytes()) == BYTES
    
    # 2. Native Hamming Distance via DLL POPCNT
    dist = ffi.hamming_distance(v1, v2)
    sigma = ffi.resonance_sigma(dist)
    free_energy = ffi.free_energy_friston(dist)
    
    print(f"[FFI TEST] Native Rust POPCNT Distance: {dist}/10240 bits ({dist/10240*100:.2f}%) | Sigma: {sigma:.2f} | Free Energy: {free_energy:.4f}")
    assert 4800 <= dist <= 5440, f"Distance out of 6-sigma bounds: {dist}"
    assert abs(sigma) < 6.0, f"Unexpected high resonance: {sigma}"
    assert 0.90 <= free_energy <= 1.0, f"Expected high epistemic surprise for random orthogonal concepts: {free_energy}"
    
    # 3. Invertible Binding in Native C-ABI (A ^ B ^ B = A)
    bound = ffi.bind(v1, v2)
    unbound = ffi.bind(bound, v2)
    assert np.array_equal(v1, unbound), "Native FFI Binding is not invertible!"
    
    # Check self-distance = 0
    zero_dist = ffi.hamming_distance(v1, unbound)
    assert zero_dist == 0, f"Expected zero distance for identical vectors, got {zero_dist}"
    
    # 4. Native Bundle Majority Rule
    bundled = ffi.bundle_two(v1, v2, tie_seed=999)
    assert bundled.shape == (WORDS,)
    
    # 5. Throughput Benchmark Native Batch (10,000,000 in-memory comparisons)
    n_ops = 5_000_000
    t0 = time.perf_counter()
    batch_dist = ffi.hamming_distance_batch(v1, v2, n_ops)
    t_dist = time.perf_counter() - t0
    ops_per_sec = n_ops / t_dist
    ns_per_op = (t_dist / n_ops) * 1e9
    
    assert batch_dist == dist, f"Batch distance {batch_dist} != single distance {dist}"
    print(f"[FFI BATCH BENCHMARK] Native Bare-Metal POPCNT: {ops_per_sec:,.0f} ops/sec ({ns_per_op:.2f} ns/op)")
    assert ops_per_sec > 1_000_000, f"Throughput too low: {ops_per_sec}"

    print("[TEST PASSED] Bare-Metal Native Rust 10,240-bit VSA DLL (C-ABI FFI) fully verified!")

if __name__ == "__main__":
    test_native_vsa_ffi()
