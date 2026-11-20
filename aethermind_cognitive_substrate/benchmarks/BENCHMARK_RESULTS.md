# HDC-Arena / VSA-Bench Reproducible Results

**Generated:** `2026-11-20T17:48:37.083948`  
**Kernel Version:** `7.2.0-APEX-V72-82-ORGANS-FUSED-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Relative Speedup vs NumPy | Speedup vs PyTorch |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 141.162 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 246.441 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 86.107 ms | 1.64x | 2.86x |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | 7.926 ms | 17.81x | 31.09x |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **11.211 ms** | **12.59x** | **21.98x** |

*Cython vs `ctypes` bind/hamming speedup:* **`10.86x`** | *Fused Graph latency:* **`5.606 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Rust Smith) | 69.536 ms | **120.161 ms** | **0.58x** | `4.941e-06` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 226.196 ms | **14.24 ms** | **15.88x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 916.958 ms | **9.794 ms** | **93.62x** | Exact KKT (`97.94 µs/step`) |
