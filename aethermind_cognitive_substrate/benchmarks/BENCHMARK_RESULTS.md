# HDC-Arena / VSA-Bench Reproducible Results (`v7.4.0`)

**Generated:** `2026-11-23T23:49:49.642479`  
**Kernel Version:** `7.7.0-APEX-MODULAR-AGI-FUSED-JIT-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 224.164 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 286.577 ms | 0.78x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 1141.26 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 149.298 ms | 1.5x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **15.612 ms** | **14.36x** | **73.1x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **16.042 ms** | **13.97x** | **71.14x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`2.464 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`2.25 ms`**
- *Native x86_64 AVX2 W^X Fused Permute+XOR (4-way route, 2000 iters):* **`2.653 ms`**
- *Cython vs `ctypes` speedup:* **`9.56x`** | *Fused Graph latency:* **`8.021 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 107.936 ms | **19.303 ms** | **5.59x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 402.134 ms | **14.34 ms** | **28.04x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 1652.686 ms | **10.243 ms** | **161.35x** | Exact KKT (`102.43 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `801.838 ms` (`gpu_queue_ms=2.782 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `463.637 ms` (`gpu_queue_ms=2.897 ms`)
