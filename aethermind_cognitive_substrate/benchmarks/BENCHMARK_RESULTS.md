# HDC-Arena / VSA-Bench Reproducible Results (`v9.0.0`)

**Generated:** `2026-11-24T20:48:22.973818`  
**Kernel Version:** `9.0.0-APEX-MODULAR-AGI-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 106.879 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 174.796 ms | 0.61x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 591.2 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 60.912 ms | 1.75x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **7.652 ms** | **13.97x** | **77.27x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **9.376 ms** | **11.4x** | **63.06x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`2.05 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`2.182 ms`**
- *Native x86_64 AVX2 W^X Fused Permute+XOR (4-way route, 2000 iters):* **`2.401 ms`**
- *Cython vs `ctypes` speedup:* **`7.96x`** | *Fused Graph latency:* **`4.688 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 60.704 ms | **14.068 ms** | **4.31x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 201.619 ms | **16.312 ms** | **12.36x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 1023.346 ms | **11.397 ms** | **89.79x** | Exact KKT (`113.97 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `3.713 ms` (`gpu_queue_ms=2.489 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `3.234 ms` (`gpu_queue_ms=2.255 ms`)
- **Fused Permute+XOR Shader (`vsa_batch_permuted_xor.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `6.564 ms` (`gpu_queue_ms=4.588 ms`)
- **Programmable LDS VSA DAG VM (`vsa_batch_dag_vm.spv`, 7 ops):** `VULKAN_WAVE64_LDS_VM (Radeon RX 580 Series)` (`gpu_executed=True`) — `6.431 ms` (`gpu_queue_ms=4.497 ms`)
