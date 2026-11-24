# HDC-Arena / VSA-Bench Reproducible Results (`v7.4.0`)

**Generated:** `2026-11-23T21:03:52.096620`  
**Kernel Version:** `7.6.0-APEX-MODULAR-AGI-JIT-ARC-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 126.136 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 229.826 ms | 0.55x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 618.706 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 62.529 ms | 2.02x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **9.58 ms** | **13.17x** | **64.59x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **10.155 ms** | **12.42x** | **60.93x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`2.08 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`1.917 ms`**
- *Cython vs `ctypes` speedup:* **`6.53x`** | *Fused Graph latency:* **`5.077 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 76.645 ms | **14.915 ms** | **5.14x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 298.477 ms | **18.17 ms** | **16.43x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 1108.467 ms | **11.103 ms** | **99.84x** | Exact KKT (`111.03 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `4186.004 ms` (`gpu_queue_ms=1.383 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `3896.526 ms` (`gpu_queue_ms=1.19 ms`)
