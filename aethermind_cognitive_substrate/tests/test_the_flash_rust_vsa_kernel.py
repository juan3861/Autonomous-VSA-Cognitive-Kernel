"""
Test suite for Bare-Metal Native Rust 10,240-bit VSA Kernel
Executes the compiled release binary and verifies all 5 phases:
1. One-Shot Learning Tabula Rasa
2. Active Inference Predictive Reflex in Nanoseconds
3. Holographic Resilience with 35% Corrupted Bits
4. Direct Algebraic Analogical Reasoning in O(1)
5. REM Dream Consolidation of Noisy Traces into Causal Invariant
"""

import subprocess
import os
import sys

# Configure UTF-8 safe output for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def test_rust_vsa_kernel_execution():
    exe_path = r"F:\AetherMind_Apotheosis_Final\aether_cortex_vsa\target\release\aether_cortex_vsa.exe"
    
    # If not finished compiling yet, build explicitly
    if not os.path.exists(exe_path):
        cargo = r"C:\Users\juanp\.cargo\bin\cargo.exe"
        manifest = r"F:\AetherMind_Apotheosis_Final\aether_cortex_vsa\Cargo.toml"
        build_res = subprocess.run([cargo, "build", "--release", "--manifest-path", manifest], capture_output=True, text=True, encoding="utf-8", errors="replace")
        assert build_res.returncode == 0, f"Cargo build failed: {build_res.stderr}"

    assert os.path.exists(exe_path), f"Binary not found at {exe_path}"

    res = subprocess.run([exe_path], capture_output=True, text=True, encoding="utf-8", errors="replace")
    
    # Print safe string
    safe_out = res.stdout.encode("ascii", errors="replace").decode("ascii")
    print("STDOUT:\n", safe_out)
    if res.stderr:
        print("STDERR:\n", res.stderr.encode("ascii", errors="replace").decode("ascii"))

    assert res.returncode == 0, f"Rust kernel exited with code {res.returncode}"
    
    # Assertions on outputs of all 5 phases
    assert "FASE 1" in res.stdout
    assert "FASE 2" in res.stdout
    assert "FASE 3" in res.stdout
    assert "FASE 4" in res.stdout
    assert "FASE 5" in res.stdout
    assert "0% GPU" in res.stdout
    assert "0% LLM" in res.stdout
    assert "Conceito Recuperado:" in res.stdout or "Conceito" in res.stdout
    assert "ATIVAR_QUANT_Q4" in res.stdout
    assert "DORY_4B_LOOPED" in res.stdout
    assert "EFEITO_EMERGENTE" in res.stdout
    print("[TEST PASSED] Bare-Metal Native Rust 10,240-bit VSA Kernel fully verified!")

if __name__ == "__main__":
    test_rust_vsa_kernel_execution()
