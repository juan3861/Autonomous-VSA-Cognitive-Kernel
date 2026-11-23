# HDC-Arena / VSA-Bench Reproducible Results (`v7.4.0`)

**Generated:** `2026-11-23T18:22:23.112315`  
**Kernel Version:** `7.4.0-APEX-MODULAR-AGI-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 113.839 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 200.725 ms | 0.57x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 606.601 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 64.631 ms | 1.76x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **7.687 ms** | **14.81x** | **78.91x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **10.097 ms** | **11.27x** | **60.08x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`2.016 ms`**
- *Cython vs `ctypes` speedup:* **`8.41x`** | *Fused Graph latency:* **`5.049 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 63.447 ms | **14.926 ms** | **4.25x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 225.355 ms | **12.541 ms** | **17.97x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 1084.947 ms | **8.407 ms** | **129.05x** | Exact KKT (`84.07 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `1920.635 ms` (`gpu_queue_ms=7.891 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `316.287 ms` (`gpu_queue_ms=2.566 ms`)
