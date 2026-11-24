# HDC-Arena / VSA-Bench Reproducible Results (`v7.4.0`)

**Generated:** `2026-11-24T16:02:07.842502`  
**Kernel Version:** `8.0.0-APEX-MODULAR-AGI-GPU-DAG-CEGIS-SOVEREIGN`  
**Environment:** Single-thread BLAS (`OMP/OPENBLAS/MKL=1`)

## 1. 10,240-bit Chained VSA Workload (`permute -> bind -> bind -> unpermute -> hamming`, 2000 iters)

| Backend | Wall Time (ms) | Speedup vs NumPy | Speedup vs TorchHD |
|---|---:|---:|---:|
| **Pure NumPy (`int8` bipolar)** | 110.053 ms | 1.0x | — |
| **PyTorch CPU (`torch 2.11`, `int8`)** | 171.456 ms | 0.64x | — |
| **TorchHD (`torch_hd 5.8.4`, BSC)** | 600.163 ms | — | 1.0x |
| **Rust C-ABI via Python `ctypes`** | 64.68 ms | 1.7x | — |
| **Cython Zero-Copy (`CYTHON_ZERO_COPY`)** | **162.55 ms** | **0.68x** | **3.69x** |
| **Fused AVX2 Graph VM (`vsa_eval_graph_bytecode`)** | **80.68 ms** | **1.36x** | **7.44x** |

- *Native x86_64 AVX2 W^X JIT (5-way XOR chain, 2000 iters):* **`2.042 ms`**
- *Native x86_64 AVX2 W^X JIT Permute (shift=199, 2000 iters):* **`1.879 ms`**
- *Native x86_64 AVX2 W^X Fused Permute+XOR (4-way route, 2000 iters):* **`2.351 ms`**
- *Cython vs `ctypes` speedup:* **`0.4x`** | *Fused Graph latency:* **`40.34 µs/graph`**

## 2. Mathematical & Control Solver Benchmarks vs Scientific Python Baselines

| Benchmark Workload | Baseline Time (ms) | Autonomous Kernel Time (ms) | Speedup | Numerical Parity Error |
|---|---:|---:|---:|---:|
| **Discrete Lyapunov 16×16** (`scipy.linalg` vs Cython+Rust Fast-Path) | 66.086 ms | **14.306 ms** | **4.62x** | `3.553e-15` |
| **Simplex LP** (`scipy.linprog` HiGHS vs `RevisedSimplex`) | 248.604 ms | **15.92 ms** | **15.62x** | `2.857e-07` |
| **CBF-QP Safety Filter** (`cvxpy` CLARABEL vs `CBFControlBarrierShield`) | 853.27 ms | **9.939 ms** | **85.85x** | Exact KKT (`99.39 µs/step`) |

## 3. Massive Batch VSA & Cosine Search (4096 candidates)
- **Hamming 10,240-bit Shader (`vsa_batch_hamming.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `343.645 ms` (`gpu_queue_ms=2.828 ms`)
- **Dense Cosine Shader (`batch_cosine_sim.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `321.311 ms` (`gpu_queue_ms=2.625 ms`)
- **Fused Permute+XOR Shader (`vsa_batch_permuted_xor.spv`):** `VULKAN_WAVE64 (Radeon RX 580 Series)` (`gpu_executed=True`) — `283.4 ms` (`gpu_queue_ms=4.762 ms`)
- **Programmable LDS VSA DAG VM (`vsa_batch_dag_vm.spv`, 7 ops):** `VULKAN_WAVE64_LDS_VM (Radeon RX 580 Series)` (`gpu_executed=True`) — `280.87 ms` (`gpu_queue_ms=4.683 ms`)
