"""
Strict Empirical Test for 10,240-bit VSA Persistence Bridge & Rust Bare-Metal Integration
Verifies:
1. Generation and Orthogonality of 10,240-bit vectors in NumPy
2. Low-level persistence to disk (1280 bytes exactly) and SQLite
3. Dynamic retrieval and exact byte-level match
4. Binding and distance calculation matching Kanerva hyperdimensional bounds
5. Execution of compiled bare-metal Rust VSA binary through the bridge
"""

import sys
import os
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

from aethermind_cognitive_substrate.memory_vault.vsa_persistence_bridge import VSA10240PersistenceBridge, WORDS, BITS, BYTES

def test_vsa_persistence_bridge():
    bridge = VSA10240PersistenceBridge()
    
    # 1. Vector generation & orthogonality
    v1 = bridge.generate_random_orthogonal(seed=42)
    v2 = bridge.generate_random_orthogonal(seed=1337)
    
    assert v1.shape == (160,)
    assert v1.dtype == np.uint64
    assert len(v1.tobytes()) == 1280
    
    dist = bridge.hamming_distance(v1, v2)
    sigma = bridge.compute_resonance_sigma(dist)
    print(f"[TEST] Random Orthogonal Distance: {dist}/10240 bits ({dist/10240*100:.2f}%) | Sigma: {sigma:.2f}")
    assert 4800 <= dist <= 5440, f"Distance out of 6-sigma bounds: {dist}"
    assert abs(sigma) < 6.0, f"Spurious correlation: {sigma}"
    
    # 2. Persistence to DB & Disk
    concept_name = "TEST_HYPERVECTOR_ALPHA"
    bridge.save_hypervector(concept_name, v1, category="test", resonance_sigma=sigma, free_energy_f=0.5)
    
    # Check disk file size
    bin_path = bridge.storage_dir / f"{concept_name}.bin"
    assert bin_path.exists(), "Binary file not created"
    assert os.path.getsize(bin_path) == 1280, f"Invalid file size: {os.path.getsize(bin_path)}"
    
    # 3. Retrieval and Exact Byte Match
    v1_loaded = bridge.load_hypervector(concept_name)
    assert v1_loaded is not None, "Failed to load hypervector"
    assert np.array_equal(v1, v1_loaded), "Retrieved vector does not match original"
    
    # 4. XOR Binding and Invertibility
    bound = bridge.bind_xor(v1, v2)
    unbound = bridge.bind_xor(bound, v2)
    assert np.array_equal(v1, unbound), "XOR binding not invertible: A ^ B ^ B != A"
    
    # 5. Rust Bare-Metal Kernel Execution via Bridge
    rust_res = bridge.execute_rust_kernel_proof()
    assert rust_res["status"] == "SUCCESS", f"Rust kernel failed: {rust_res}"
    assert rust_res["execution_verified"] is True
    print("[TEST] Rust Bare-Metal VSA Kernel successfully verified through bridge!")
    print("[TEST PASSED] All 10,240-bit VSA persistence & bare-metal proofs verified.")

if __name__ == "__main__":
    test_vsa_persistence_bridge()
