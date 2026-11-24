# HDC-Arena / VSA-Bench Reproducible Results (`v7.4.0`)

**Generated:** `2026-11-24T15:29:45.838290`  
**Kernel Version:** `7.9.0-APEX-MODULAR-AGI-JIT-GPU-NESTED-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 137.173 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 231.266 ms | 0.59x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 812.771 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 62.785 ms | 2.18x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **8.026 ms** | **17.09x** | **101.27x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **10.576 ms** | **12.97x** | **76.85x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`2.037 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`1.9 ms`**
- *Native x86_64 AVX2 W^X Fused Permute+XOR (4-way route, 2000 iters):* **`2.163 ms`**
- *Cython vs `ctypes` speedup:* **`7.82x`** | *Fused Graph latency:* **`5.288 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 68.385 ms | **14.126 ms** | **4.84x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 270.94 ms | **14.689 ms** | **18.45x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 868.088 ms | **10.522 ms** | **82.5x** | Exact KKT (`105.22 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `2733.409 ms` (`gpu_queue_ms=3.89 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `553.966 ms` (`gpu_queue_ms=1.417 ms`)
- **Fused Permute+XOR Shader (`vsa_batch_permuted_xor.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `678.986 ms` (`gpu_queue_ms=4.285 ms`)
