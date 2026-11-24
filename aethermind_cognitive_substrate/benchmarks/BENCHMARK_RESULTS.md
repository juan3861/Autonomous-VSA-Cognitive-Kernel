# HDC-Arena / VSA-Bench Reproducible Results (`v7.4.0`)

**Generated:** `2026-11-24T14:27:20.706295`  
**Kernel Version:** `7.8.0-APEX-MODULAR-AGI-INDUCTIVE-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 255.295 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 371.431 ms | 0.69x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 1323.787 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 154.389 ms | 1.65x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **9.929 ms** | **25.71x** | **133.33x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **28.607 ms** | **8.92x** | **46.28x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`3.589 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`3.924 ms`**
- *Native x86_64 AVX2 W^X Fused Permute+XOR (4-way route, 2000 iters):* **`3.371 ms`**
- *Cython vs `ctypes` speedup:* **`15.55x`** | *Fused Graph latency:* **`14.303 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 129.954 ms | **26.453 ms** | **4.91x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 498.065 ms | **35.952 ms** | **13.85x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 1820.738 ms | **21.718 ms** | **83.83x** | Exact KKT (`217.18 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `603.57 ms` (`gpu_queue_ms=9.526 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `501.614 ms` (`gpu_queue_ms=2.317 ms`)
