# HDC-Arena / VSA-Bench Reproducible Results (`v7.3.0`)

**Generated:** `2026-11-21T16:27:19.956087`  
**Kernel Version:** `7.3.0-APEX-QUAD-FRONT-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 183.897 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 265.063 ms | 0.69x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 984.511 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 90.366 ms | 2.04x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **16.356 ms** | **11.24x** | **60.19x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **15.021 ms** | **12.24x** | **65.54x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`3.639 ms`**
- *Cython vs `ctypes` speedup:* **`5.52x`** | *Fused Graph latency:* **`7.511 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 76.965 ms | **18.686 ms** | **4.12x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 376.265 ms | **16.808 ms** | **22.39x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 1222.965 ms | **21.016 ms** | **58.19x** | Exact KKT (`210.16 µs/step`) |

## 3. Massive Batch VSA Search (4096 × 10,240-bit vectors)
- **Backend Executed:** `CPU_NUMPY_FALLBACK` (`gpu_executed=False`)
- **Elapsed Time:** `144.614 ms` (`gpu_queue_ms=0.0 ms`)
