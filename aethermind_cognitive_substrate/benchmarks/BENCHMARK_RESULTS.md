# HDC-Arena / VSA-Bench Reproducible Results (`v8.5.0`)

**Generated:** `2026-11-24T20:40:41.471258`  
**Kernel Version:** `8.5.0-APEX-MODULAR-AGI-RESIDENT-GPU-JIT-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 104.008 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 207.434 ms | 0.5x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 659.97 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 63.838 ms | 1.63x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **7.684 ms** | **13.54x** | **85.89x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **9.592 ms** | **10.84x** | **68.81x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`1.986 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`2.17 ms`**
- *Native x86_64 AVX2 W^X Fused Permute+XOR (4-way route, 2000 iters):* **`2.49 ms`**
- *Cython vs `ctypes` speedup:* **`8.31x`** | *Fused Graph latency:* **`4.796 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 63.662 ms | **14.181 ms** | **4.49x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 218.358 ms | **14.313 ms** | **15.26x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 800.814 ms | **9.291 ms** | **86.19x** | Exact KKT (`92.91 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `3.418 ms` (`gpu_queue_ms=2.387 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `3.386 ms` (`gpu_queue_ms=2.488 ms`)
- **Fused Permute+XOR Shader (`vsa_batch_permuted_xor.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `6.435 ms` (`gpu_queue_ms=4.628 ms`)
- **Programmable LDS VSA DAG VM (`vsa_batch_dag_vm.spv`, 7 ops):** `VULKAN_WAVE64_LDS_VM (Radeon RX 580 Series)` (`gpu_executed=True`) — `6.282 ms` (`gpu_queue_ms=4.441 ms`)
