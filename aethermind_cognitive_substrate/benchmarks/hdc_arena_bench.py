"""HDC-Arena / VSA-Bench: Standardized Comparative Benchmark Suite.

Compares Autonomous VSA Cognitive Kernel (v7.2.0) head-to-head against standard
Python/ML/Optimization ecosystems (`numpy`, `torch`, `scipy`, `cvxpy`) on identical
hardware under strict single-thread BLAS parity (`OPENBLAS/OMP/MKL_NUM_THREADS=1`).

Outputs reproducible metrics to `BENCHMARK_RESULTS.json` and `BENCHMARK_RESULTS.md`.
"""
from __future__ import annotations

import ctypes
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import numpy as np
import scipy.linalg
import scipy.optimize
import torch
import cvxpy as cp

from aethermind_cognitive_substrate.memory_vault.vsa_expression_compiler import (
    VSAExpressionCompiler,
    VSASeed,
    VSAVar,
)
from aethermind_cognitive_substrate.physical_bridge.fast_vsa_bridge import FastVSABridge
from aethermind_cognitive_substrate.physical_bridge.native_cortex_dll_singleton import get_native_cortex_dll
from aethermind_cognitive_substrate.logic_symbolic.lyapunov_sdp_stability_certifier import LyapunovSDPStabilityCertifier
from aethermind_cognitive_substrate.logic_symbolic.simplex_linear_programming import RevisedSimplexLPSolver
from aethermind_cognitive_substrate.metacognition.cbf_control_barrier_shield import CBFControlBarrierShield


def bench_vsa_10240(n_iters: int = 2000) -> Dict[str, Any]:
    """Benchmark 10,240-bit bind + permute + hamming workflows across 5 backends."""
    rng = np.random.default_rng(42)
    a_u64 = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)
    b_u64 = rng.integers(0, np.iinfo(np.uint64).max, size=160, dtype=np.uint64)

    # 1. Pure NumPy uint8/bipolar baseline (10,240 bits)
    a_bip = rng.choice([-1, 1], size=10240).astype(np.int8)
    b_bip = rng.choice([-1, 1], size=10240).astype(np.int8)
    t0 = time.perf_counter()
    acc_np = 0
    for _ in range(n_iters):
        p = np.roll(a_bip, 7)
        bnd = p * b_bip
        rec = np.roll(bnd * b_bip, -7)
        acc_np += int(np.count_nonzero(rec != a_bip))
    numpy_ms = (time.perf_counter() - t0) * 1000.0

    # 2. PyTorch CPU Tensor baseline (10,240 float32/int8 VSA op, TorchHD-style)
    torch.set_num_threads(1)
    ta = torch.from_numpy(a_bip.copy())
    tb = torch.from_numpy(b_bip.copy())
    t0 = time.perf_counter()
    acc_th = 0
    for _ in range(n_iters):
        p = torch.roll(ta, shifts=7, dims=0)
        bnd = p * tb
        rec = torch.roll(bnd * tb, shifts=-7, dims=0)
        acc_th += int((rec != ta).sum().item())
    torch_ms = (time.perf_counter() - t0) * 1000.0

    # 3. Discrete Ctypes Rust C-ABI FFI (single bind + hamming comparison)
    bridge_dll = get_native_cortex_dll()
    from aethermind_cognitive_substrate.memory_vault.native_vsa_ffi import NativeVSAFFI
    ffi = NativeVSAFFI()
    t0 = time.perf_counter()
    acc_ct = 0
    for _ in range(n_iters):
        bnd = ffi.bind(a_u64, b_u64)
        rec = ffi.bind(bnd, b_u64)
        acc_ct += ffi.hamming_distance(rec, a_u64)
    ctypes_ms = (time.perf_counter() - t0) * 1000.0

    # 4. Zero-Copy Cython Native Extension (bind_into + hamming with zero Python ctypes overhead)
    fast = FastVSABridge()
    out_buf = np.zeros(160, dtype=np.uint64)
    t0 = time.perf_counter()
    acc_cy = 0
    for _ in range(n_iters):
        fast.bind_into(a_u64, b_u64, out_buf)
        fast.bind_into(out_buf, b_u64, out_buf)
        acc_cy += fast.hamming_distance(out_buf, a_u64)
    cython_ms = (time.perf_counter() - t0) * 1000.0

    # 5. Fused AVX2 Expression Graph Bytecode VM via Cython Zero-Copy (or ctypes fallback)
    comp = VSAExpressionCompiler()
    va = VSAVar("a")
    vb = VSAVar("b")
    expr = va.permute(7).bind(vb)
    recovered = expr.bind(vb).unpermute(7)
    ops, _ = comp.compile_program(outputs=[], hamming_queries=[(recovered, va)])
    in_buf = np.vstack([a_u64, b_u64])
    out_empty = np.empty((0, 160), dtype=np.uint64)
    scalar_buf = np.zeros(1, dtype=np.uint32)
    op_arr = (type(ops[0]) * len(ops))(*ops)

    t0 = time.perf_counter()
    acc_vm = 0
    if comp._cy is not None and hasattr(comp._cy, "cy_eval_graph"):
        op_bytes = np.frombuffer(op_arr, dtype=np.uint8)
        for _ in range(n_iters):
            comp._cy.cy_eval_graph(op_bytes, len(ops), in_buf, out_empty, scalar_buf)
            acc_vm += int(scalar_buf[0])
    else:
        in_ptr = in_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        out_ptr = ctypes.POINTER(ctypes.c_uint64)()
        sc_ptr = scalar_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
        for _ in range(n_iters):
            bridge_dll.vsa_eval_graph_bytecode(op_arr, len(ops), in_ptr, 2, out_ptr, 0, sc_ptr, 1)
            acc_vm += int(scalar_buf[0])
    fused_vm_ms = (time.perf_counter() - t0) * 1000.0

    assert acc_np == 0 and acc_th == 0 and acc_ct == 0 and acc_cy == 0 and acc_vm == 0

    return {
        "n_iters": n_iters,
        "numpy_10240_ms": round(numpy_ms, 3),
        "pytorch_10240_ms": round(torch_ms, 3),
        "ctypes_rust_ms": round(ctypes_ms, 3),
        "cython_zero_copy_ms": round(cython_ms, 3),
        "cython_backend": fast.backend_mode,
        "fused_avx2_vm_ms": round(fused_vm_ms, 3),
        "speedup_fused_vs_numpy": round(numpy_ms / max(fused_vm_ms, 1e-6), 2),
        "speedup_fused_vs_pytorch": round(torch_ms / max(fused_vm_ms, 1e-6), 2),
        "speedup_cython_vs_ctypes": round(ctypes_ms / max(cython_ms, 1e-6), 2),
        "us_per_fused_graph": round((fused_vm_ms * 1000.0) / n_iters, 3),
    }


def bench_lyapunov_16x16(n_iters: int = 200) -> Dict[str, Any]:
    """Compare 16x16 Discrete Lyapunov equation solver: SciPy vs Rust Smith Doubling."""
    rng = np.random.default_rng(7)
    M = rng.normal(0, 0.1, size=(16, 16))
    A = np.ascontiguousarray(M / (np.max(np.abs(np.linalg.eigvals(M))) + 0.35), dtype=np.float64)
    Q = np.eye(16, dtype=np.float64)

    t0 = time.perf_counter()
    for _ in range(n_iters):
        P_sp = scipy.linalg.solve_discrete_lyapunov(A.T, Q)
    scipy_ms = (time.perf_counter() - t0) * 1000.0

    cert = LyapunovSDPStabilityCertifier()
    t0 = time.perf_counter()
    for _ in range(n_iters):
        res_ru = cert.certify_discrete_lyapunov(A=A, Q=Q)
    rust_ms = (time.perf_counter() - t0) * 1000.0

    P_ru = np.array(res_ru["lyapunov_matrix_P"], dtype=np.float64)
    max_diff = float(np.max(np.abs(P_sp - P_ru)))

    return {
        "n_iters": n_iters,
        "scipy_lyapunov_ms": round(scipy_ms, 3),
        "rust_smith_doubling_ms": round(rust_ms, 3),
        "speedup_rust_vs_scipy": round(scipy_ms / max(rust_ms, 1e-6), 2),
        "max_parity_error": float(f"{max_diff:.3e}"),
        "native_accelerated": "Rust" in str(res_ru.get("backend", "")),
    }


def bench_simplex_vs_highs(n_iters: int = 100) -> Dict[str, Any]:
    """Compare RevisedSimplexLPSolver (with exact dual certificate) vs SciPy HiGHS."""
    c = np.array([-3.0, -5.0, -2.0], dtype=np.float64)
    A = np.array([[1.0, 1.0, 2.0], [2.0, 1.0, 0.0], [0.0, 2.0, 1.0]], dtype=np.float64)
    b = np.array([10.0, 8.0, 9.0], dtype=np.float64)

    t0 = time.perf_counter()
    for _ in range(n_iters):
        res_sp = scipy.optimize.linprog(c, A_ub=A, b_ub=b, bounds=(0, None), method="highs")
    scipy_ms = (time.perf_counter() - t0) * 1000.0

    lp = RevisedSimplexLPSolver(max_pivots=500, tol=1e-10)
    t0 = time.perf_counter()
    for _ in range(n_iters):
        res_our = lp.solve_lp(c=c, A=A, b=b)
    our_ms = (time.perf_counter() - t0) * 1000.0

    gap = abs(float(res_sp.fun) - float(res_our["primal_objective"]))

    return {
        "n_iters": n_iters,
        "scipy_highs_ms": round(scipy_ms, 3),
        "revised_simplex_ms": round(our_ms, 3),
        "speedup_vs_highs": round(scipy_ms / max(our_ms, 1e-6), 2),
        "objective_parity_error": float(f"{gap:.3e}"),
        "strong_duality_gap": float(f"{res_our['strong_duality_gap']:.3e}"),
    }


def bench_cbf_qp_vs_cvxpy(n_iters: int = 100) -> Dict[str, Any]:
    """Compare CBFControlBarrierShield analytical KKT QP vs CVXPY disciplined QP."""
    x = np.array([0.88, 0.80, 0.75, 0.85], dtype=np.float64)
    u_nom = np.array([0.5, 0.4, 0.3, 0.4], dtype=np.float64)
    shield = CBFControlBarrierShield(state_dim=4, control_dim=4, gamma=2.0)

    t0 = time.perf_counter()
    for _ in range(n_iters):
        shield.filter_control_action(x.tolist(), u_nom.tolist())
    cbf_ms = (time.perf_counter() - t0) * 1000.0

    # CVXPY equivalent box-CBF QP
    h = shield.safe_upper_bounds - x
    t0 = time.perf_counter()
    for _ in range(n_iters):
        u_var = cp.Variable(4)
        obj = cp.Minimize(0.5 * cp.sum_squares(u_var - u_nom))
        cons = [-u_var + 2.0 * h >= 0]
        cp.Problem(obj, cons).solve(solver=cp.CLARABEL)
    cvxpy_ms = (time.perf_counter() - t0) * 1000.0

    return {
        "n_iters": n_iters,
        "cvxpy_clarabel_ms": round(cvxpy_ms, 3),
        "cbf_kkt_shield_ms": round(cbf_ms, 3),
        "speedup_cbf_vs_cvxpy": round(cvxpy_ms / max(cbf_ms, 1e-6), 2),
        "us_per_safety_filter": round((cbf_ms * 1000.0) / n_iters, 2),
    }


def main():
    results = {
        "timestamp": datetime.now().isoformat(),
        "version": "7.2.0-APEX-V72-82-ORGANS-FUSED-SOVEREIGN",
        "vsa_10240": bench_vsa_10240(2000),
        "lyapunov_16x16": bench_lyapunov_16x16(200),
        "simplex_lp": bench_simplex_vs_highs(100),
        "cbf_qp_safety": bench_cbf_qp_vs_cvxpy(100),
    }

    out_dir = Path(__file__).resolve().parent
    json_path = out_dir / "BENCHMARK_RESULTS.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    v = results["vsa_10240"]
    l = results["lyapunov_16x16"]
    s = results["simplex_lp"]
    c = results["cbf_qp_safety"]

    md = f"""# HDC-Arena / VSA-Bench Reproducible Results

**Generated:** `{results['timestamp']}`  
**Kernel Version:** `{results['version']}`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, {v['n_iters']} iters)

| Backend | Wall Time (ms) | Relative Speedup vs NumPy | Speedup vs PyTorch |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | {v['numpy_10240_ms']} ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | {v['pytorch_10240_ms']} ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | {v['ctypes_rust_ms']} ms | {round(v['numpy_10240_ms']/v['ctypes_rust_ms'], 2)}x | {round(v['pytorch_10240_ms']/v['ctypes_rust_ms'], 2)}x |
| **Cython Zero-Copy (`{v['cython_backend']}`)** | {v['cython_zero_copy_ms']} ms | {round(v['numpy_10240_ms']/v['cython_zero_copy_ms'], 2)}x | {round(v['pytorch_10240_ms']/v['cython_zero_copy_ms'], 2)}x |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **{v['fused_avx2_vm_ms']} ms** | **{v['speedup_fused_vs_numpy']}x** | **{v['speedup_fused_vs_pytorch']}x** |

*Cython vs `ctypes` bind/hamming speedup:* **`{v['speedup_cython_vs_ctypes']}x`** | *Fused Graph latency:* **`{v['us_per_fused_graph']} µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Rust Smith) | {l['scipy_lyapunov_ms']} ms | **{l['rust_smith_doubling_ms']} ms** | **{l['speedup_rust_vs_scipy']}x** | `{l['max_parity_error']}` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | {s['scipy_highs_ms']} ms | **{s['revised_simplex_ms']} ms** | **{s['speedup_vs_highs']}x** | `{s['objective_parity_error']}` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | {c['cvxpy_clarabel_ms']} ms | **{c['cbf_kkt_shield_ms']} ms** | **{c['speedup_cbf_vs_cvxpy']}x** | Exact KKT (`{c['us_per_safety_filter']} µs/step`) |
"""

    md_path = out_dir / "BENCHMARK_RESULTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(md)


if __name__ == "__main__":
    main()
