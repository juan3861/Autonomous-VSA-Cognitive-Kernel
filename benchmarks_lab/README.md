# 🏛️ AetherMind Bare-Metal LLM Experimental Benchmark Laboratory
### *Open Empirical Evaluation of Ultra-Compact & Medium-Layer Language Models (350M to 7B+) Across Full Quantization Grids (`Q4_K_M` to `F16`/`BF16`) Under Zero-Shot Baseline vs. `Lambda-RLM` Recursive Metacognition & Formal AST/`pytest` Verification*

[![Hardware Testbed](https://img.shields.io/badge/Hardware-AMD_RX_580_8GB_Vulkan_%2B_AVX2_CPU-red?style=for-the-badge)](#2-hardware--software-testbed-specifications)
[![Models Audited](https://img.shields.io/badge/Bare--Metal_Variants-35_Homologated_Checkpoints-blue?style=for-the-badge)](#4-master-telemetry-table--all-35-bare-metal-variants-350m--70b)
[![Cognitive Suite](https://img.shields.io/badge/Cognitive_Suite-13_Areas_%2F_39_Tests_%2B_10_Opus_Hard-emerald?style=for-the-badge)](#5-area-by-area-cognitive-decomposition-matrix-a01--a13-baseline--lambda-rlm)
[![Verification](https://img.shields.io/badge/Verification-Deterministic_AST_%2B_pytest_Zero_Mocks-gold?style=for-the-badge)](#1-laboratory-manifesto--methodology)

---

## 🧭 Quick Repository Navigation

| Resource / Directory | Description | Audience |
| :--- | :--- | :--- |
| 📄 **[`README.md`](README.md)** *(This Document)* | Laboratory Manifesto, Hardware Testbed, Hall of Fame Champions by Weight Class, Full 35-Model Master Telemetry, Area-by-Area (`A01`–`A13`) & Opus Hard (`OPUS_01`–`OPUS_10`) Matrices, Direct `.gguf` Download Catalog, and Empirical Laws. | Engineers, Researchers & Autonomous AI Agents |
| 🧪 **[`TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md`](TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md)** | Complete verbatim prompts, formal verification schemas, AST inspection rules, and `pytest` unit assertions for all **13 Cognitive Areas (39 tests)** and all **10 Opus Hard Algorithmic Challenges**. | Benchmark Reproducers & Autonomous Evaluators |
| 📊 **[`FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md`](FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md)** | Exhaustive model-by-model dossier, teacher/distiller lineage, exact quantization trade-off curves, and deep architectural diagnostics. | Model Curators & Systems Architects |
| ⚙️ **[`suite/`](suite/)** | Executable Python benchmark harnesses (`benchmark_13_areas_39_testes.py`, `duelo_nivel_opus_8b_vs_9b.py`, `tournament_pesos_mosca.py`, `tournament_k2_horizon.py`) and strict empirical auditors (`test_audit_pesos_mosca_completo.py`, `test_audit_k2_horizon.py`). | Bare-Metal Automation & CI/CD Verification |
| 🔐 **[`proofs/`](proofs/)** | Raw immutable JSON telemetry logs (`proof_k2_horizon_completo.json`, `proof_pesos_mosca_completo.json`) and the historical benchmark ledger (`MASTER_LIVRO_SAGRADO_BENCHMARKS.md`). | Cryptographic / Empirical Audit & Citation |

---

## 1. Laboratory Manifesto & Methodology

The **AetherMind Bare-Metal LLM Experimental Benchmark Laboratory** was established to answer a fundamental systems engineering question:

> *"What is the true Pareto frontier of cognitive intelligence, algorithmic synthesis, memory footprint, and hardware throughput (tokens/second) for local Language Models ranging from 350 Million to 7 Billion parameters when evaluated on real consumer/workstation silicon without cloud APIs, synthetic LLM-as-a-judge biases, or cherry-picked prompts?"*

### Core Principles of the AetherMind Protocol

1. **Zero LLM-as-a-Judge Bias (100% Deterministic & Formal Verification):**
   Every single response across our **39 Cognitive Tests (13 Areas)** and **10 Opus Hard Challenges (LeetCode Hard)** is verified by deterministic Python validators, Abstract Syntax Tree (`ast`) structural inspection, isolated subprocess execution, and strict `pytest` assertion suites (`formal_verifier`). Banning `eval()` or `re` in a prompt is enforced by parsing the generated AST before executing a single line of code.
2. **Dual-Pass Evaluation (`Zero-Shot Baseline` vs. `Lambda-RLM` Recursive Metacognition):**
   Every model variant is tested in two distinct operational regimes:
   - **Pass 1 — Zero-Shot Baseline:** Direct inference (`temperature=0.0`) measuring raw native capability out-of-the-box.
   - **Pass 2 — `Lambda-RLM` Rescue Loop:** When a baseline generation fails formal verification, the exact failure trace or assertion counterexample is captured and routed into **`Lambda-RLM`**, a recursive metacognitive engine backed by a local execution environment (`LocalREPL`) that prompts the model to self-correct its logic or edge-case handling. Both scores (`Baseline ➔ Final`) and the exact rescue delta (`+RLM`) are recorded transparently.
3. **Full Quantization Grid Auditing (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, `F16`, `BF16`):**
   Rather than testing a single arbitrary quantization per model, we map the complete bit-depth curve across 4-bit, 5-bit, 6-bit, 8-bit, and 16-bit precision to uncover non-linear quantization phenomena, bit-starvation thresholds in sub-1B models, and memory-bandwidth saturation cliffs on 8 GB VRAM.
4. **Dual-Backend Physical Telemetry (Vulkan GPU vs. AVX2 CPU):**
   Every checkpoint is benchmarked both on **GPU Vulkan** (`llama-server.exe -ngl 99`) and in **Pure CPU AVX2** (`llama-bench.exe -ngl 0 --device none`), recording cold boot time (`s`), Prompt Processing speed (`PP tok/s`), and continuous Text Generation speed (`TG tok/s`).

---

## 2. Hardware & Software Testbed Specifications

All 35 bare-metal variants in the primary 350M–7.0B matrix (plus historical 100M–35B reference tiers) were executed under strictly controlled, isolated local conditions:

| Subsystem | Specification & Configuration |
| :--- | :--- |
| **Primary GPU (Vulkan Backend)** | **AMD Radeon RX 580 Series** — `8192 MiB (8.0 GB) GDDR5 VRAM`, `256-bit` bus, `224 GB/s` peak memory bandwidth, Vulkan Compute API, `-ngl 99` (full layer offload for all models fitting within 8 GB VRAM). |
| **Host CPU (AVX2 Backend)** | **x86_64 Multi-Core AVX2 Processor** (Dual Intel Xeon E5-2696 v4 testbed / 8-thread & 14-thread isolated AVX2 execution workers, `--device none -ngl 0` for pure CPU throughput telemetry). |
| **System Memory & Storage** | **32 GB DDR4 System RAM** | High-speed NVMe SSD (`F:\`) for rapid GGUF cold-boot loading. |
| **Operating System** | **Windows 11 Pro 64-bit** (Build 26200 / Native Win32 process isolation). |
| **Inference Engine** | **`llama.cpp`** (`llama-server.exe` & `llama-bench.exe`, build `b12420+` Vulkan/AVX2) running on isolated localhost port `8089`, `--cont-batching`, `-c 4096` (up to `8192` for extended thinking audits), `temperature = 0.0`. |
| **Flash Attention Policy** | **`-fa on` (`-fa 1`)** for standard Dense Transformer architectures (`Qwen3`, `K2-Horizon`, `MiniCPM4/5`, `QwQ`); **`-fa off` (`-fa 0`)** mandatory for **IBM Granite 4.0 Hybrid Mamba-2 + Attention** architectures (`Granite-4.0-H-350M`, `Granite-350M-Gemini3`, `IBM-GPT-5.4-Coder-1B`) to prevent Vulkan FP16 state-space recurrence degradation. |
| **Metacognitive Engine** | **`Lambda-RLM`** (`F:\rotor-llm\lambda_rlm`) — Recursive Language Model orchestrator with deterministic AST extraction, `<think>...</think>` reasoning trace stripping, and automated counterexample feedback. |
| **Empirical Auditor** | **`AetherMind_Strict_Auditor.py`** — Zero-tolerance automated verification harness validating JSON cryptographic integrity, non-zero throughput metrics, and 100% test completion before certification. |

---

## 3. Hall of Fame — Champions by Weight Class & Pareto Frontier

Below are the undisputed champions of each weight class, selected by empirical dominance across **13 Cognitive Areas (39 questions)**, **10 Opus Hard Challenges (AST/`pytest`)**, and **GPU/CPU tokens-per-second throughput**.

---

### 👑 3.1 Medium-Layer King (3.7B vs. 7B): `IFM/K2-Horizon-3.7B` (`[Q6_K]` & `[Q5_K_M]`)

* **Architecture:** Dense Transformer (`3.7B` parameters, native **512,000-token** context window, native `<think>` chain-of-thought reasoning).
* **Origin / Lineage:** **Institute of Foundation Models (IFM)** — K2-Horizon long-horizon pretraining & reasoning mid-training (`IFM/K2-Horizon-3.7B-GGUF`).
* **Direct Hugging Face `.gguf` Downloads:**
  * 🏆 **`Q6_K` (Pareto King — 3.88 GB):** [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf)
  * ⚡ **`Q5_K_M` (Baseline Autonomy & Speed King — 3.39 GB):** [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf)
  * 🎯 **`Q8_0` (8-Bit Reference — 5.02 GB):** [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf)
  * 🪶 **`Q4_K_M` (Lightweight — 2.94 GB):** [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf)
* **Empirical Performance:**
  * **`[Q6_K]` (`3968.6 MB`):** **`37/39 (94.87%)`** on the 13 Cognitive Areas (`31/39` Baseline + `6` `Lambda-RLM` rescues, **11/13 Perfect 3/3 Areas**), **`3/10 (30.0%)` Opus Hard Zero-Shot** (`OPUS_04` 2D Monotonic Stack Maximal Rectangle, `OPUS_05` Bitmask DP Open TSP, `OPUS_07` Longest Valid Parentheses Trap), running at **`19.53 tok/s` GPU TG** (`76.80 tok/s` PP) and **`10.48 tok/s` CPU TG** (`109.97 tok/s` PP).
  * **`[Q5_K_M]` (`3475.0 MB`):** **`36/39 (92.31%)` Pure Zero-Shot Baseline** (highest unaided baseline score of all 35 models!) ➔ **`37/39 (94.87%)` Final** (`+1 RLM`), **`2/10` Opus Hard** (`OPUS_04`, `OPUS_07`), running at **`20.11 tok/s` GPU TG** and **`11.37 tok/s` CPU TG**.
  * *(Note: In extended 3B–4B unquantized ceiling tests in Section 17 of the Livro Sagrado, `K2-Horizon-3.7B [BF16]` reached `38/39 (97.44%)` and `4/10 Opus Hard`, but required hybrid CPU/GPU offload `-ngl 12` at `5.66 tok/s`).*
* **Why `3.7B` Beats `7B` on 8 GB VRAM (The Bandwidth Saturation Proof):**
  When **`IFM/K2-Horizon-7B [Q4_K_M]`** (`5333.1 MB`) was loaded onto the same 8 GB RX 580 (`-ngl 99`), it achieved the exact same **`37/39 (94.87%)`** cognitive score as the `3.7B`, but its GPU generation speed collapsed from **`20.11 tok/s` down to `6.89 tok/s` (a 2.92x slowdown)**, even trailing pure CPU execution (`8.06 tok/s`). Because `5.33 GB` of weights plus the 512K-architecture KV cache and Vulkan buffers saturate the RX 580's 8 GB GDDR5 capacity and `224 GB/s` bus, the `7B` model timed out (`240s` limit) on 9 out of 10 `<think>` chains in the Opus Hard suite (scoring only `1/10` vs. `3/10` on `3.7B [Q6_K]`). **Result:** `K2-Horizon-3.7B [Q6_K]` and `[Q5_K_M]` strictly dominate `7B` on 8 GB hardware.

---

### 👑 3.2 Sub-1B Flyweight King (0.9B): `IFM/K2-Horizon-0.9B` (`[Q6_K]`, `[Q8_0]`, `[Q5_K_M]`)

* **Architecture:** Ultra-Compact Dense Transformer (`0.9B` / `900M` parameters, native **512,000-token** context window, direct non-thinking fast execution `thinking: False`).
* **Origin / Lineage:** **Institute of Foundation Models (IFM)** — Native sub-1B counterpart of the K2-Horizon family (`IFM/K2-Horizon-0.9B-GGUF`).
* **Direct Hugging Face `.gguf` Downloads:**
  * 🏆 **`Q6_K` (Opus Hard Flyweight King — 846.4 MB):** [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf)
  * 👑 **`Q8_0` (13-Areas Sub-1B Record Holder — 1095.4 MB):** [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf)
  * ⚡ **`Q5_K_M` (Ultra-Compact 4-Opus Solver — 737.6 MB):** [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf)
  * 🪶 **`Q4_K_M` (High-Speed Entry — 635.3 MB):** [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf)
* **Empirical Performance:**
  * **`[Q6_K]` (`846.4 MB`):** **`34/39 (87.18%)`** on 13 Areas (`25/39` Baseline + `9` `Lambda-RLM` rescues, `9/13` Perfect Areas) and an unprecedented **`4/10 (40.0%)` on Opus Hard Zero-Shot** (`OPUS_05` Bitmask DP TSP, `OPUS_06` Partitioned Median of Two Sorted Arrays, `OPUS_08` Two-Pointers Trapping Rain Water, and `OPUS_09` Binary Tree Any-to-Any Max Path Sum with Negatives). Generates at **`34.29 tok/s` on GPU Vulkan** and **`36.60 tok/s` on CPU AVX2** (`312.45 tok/s` CPU PP) with a **`2.57s` cold boot**!
  * **`[Q8_0]` (`1095.4 MB`):** **`35/39 (89.74%)`** on 13 Areas (`27/39` Baseline + `8` `Lambda-RLM` rescues, **`10/13` Perfect Areas**) and **`3/10 (30.0%)` on Opus Hard** (`OPUS_06` & `OPUS_08` on Baseline + `OPUS_05` rescued by `Lambda-RLM`), running at **`28.39 tok/s` GPU** and **`28.46 tok/s` CPU** (`1.52s` boot).
  * **`[Q5_K_M]` (`737.6 MB`):** **`33/39 (84.62%)`** on 13 Areas and **`4/10 (40.0%)` on Opus Hard** (`OPUS_05`, `OPUS_06`, `OPUS_07` on Baseline + `OPUS_08` rescued by `Lambda-RLM`) at **`33.35 tok/s` GPU / `38.57 tok/s` CPU**.
* **Why It Dethroned Every Sub-1B & 1.0B Model:**
  By combining IFM's high-density algorithmic pretraining with direct non-thinking synthesis (`>34 tok/s`), `K2-Horizon-0.9B` avoids `<think>` token budget exhaustion while outscoring 1.0B–1.7B models on LeetCode Hard formal verification (`4/10` Opus in `846 MB`). Furthermore, its pure CPU AVX2 throughput (`36.60 tok/s`) exceeds its Vulkan GPU speed (`34.29 tok/s`), allowing it to run 100% on CPU with **zero VRAM consumption**.

---

### 👑 3.3 Intermediate Flyweight King (1.7B): `Qwen3-1.7B` (`[Q8_0]` & `[Q5_K_M]`)

* **Architecture:** Dense Transformer (`1.7B` parameters, `32,768` context window, native `<think>` mode active).
* **Origin / Lineage:** **Alibaba Cloud Qwen Team** — Native `Qwen3-1.7B` Thinking architecture, quantized with importance matrix by `bartowski` (`bartowski/Qwen_Qwen3-1.7B-GGUF`).
* **Direct Hugging Face `.gguf` Downloads:**
  * 🏆 **`Q8_0` (Accuracy & Dual-Opus King — 2064.7 MB):** [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf)
  * ⚡ **`Q5_K_M` (1.4 GB Pareto Sweet Spot — 1403.6 MB):** [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf)
  * 🪶 **`Q4_K_M` (High-Speed 1.2 GB — 1223.0 MB):** [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf)
  * 🔬 **`BF16` (16-Bit Reference — 3881.2 MB):** [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf)
* **Empirical Performance:**
  * **`[Q8_0]` (`2064.7 MB`):** **`36/39 (92.31%)`** (`34/39` Baseline + `2` `Lambda-RLM` rescues, **11/13 Perfect Areas**) and **`2/10 (20.0%)` Opus Hard** (`OPUS_06` Median of Two Sorted Arrays, `OPUS_07` Longest Valid Parentheses) at **`31.07 tok/s` GPU TG** (`159.50 tok/s` PP) and **`19.64 tok/s` CPU TG**.
  * **`[Q5_K_M]` (`1403.6 MB` / `1.4 GB`):** Matches the **`36/39 (92.31%)`** ceiling (`32/39` Baseline + `4` RLM rescues, **11/13 Perfect Areas**) with **`1/10` Opus Hard** (`OPUS_06`) while boosting GPU speed to **`31.22 tok/s`** and CPU speed to **`24.92 tok/s`** in just `1.4 GB`!
  * *(Note: Unquantized `BF16` at `3.88 GB` dropped to `35/39` and `25.88 tok/s`, proving that 5-bit and 8-bit quantizations outperform raw 16-bit floats on both speed and cognitive accuracy).*

---

### 👑 3.4 1.0B Champions: `IBM-GPT-5.4-Coder-1B` & `MiniCPM5-1B-Claude-Opus`

* **1. `IBM-GPT-5.4-Coder-1B` (`[Q6_K]`, `[Q4_K_M]`, `[F16]`):**
  * **Architecture & Teacher:** IBM Granite Hybrid 1.0B (`128K` context, `-fa off`) distilled from **OpenAI GPT-5.4 Coder** (`bartowski` / `mradermacher`).
  * **Direct `.gguf` Downloads:**
    * 🏆 **`Q6_K` (Opus Dual-Solver Sweet Spot — 1.25 GB):** [`https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q6_K.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q6_K.gguf)
    * 👑 **`Q4_K_M` (13-Areas Cognitive Leader — 0.95 GB):** [`https://huggingface.co/bartowski/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B-Q4_K_M.gguf`](https://huggingface.co/bartowski/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B-Q4_K_M.gguf)
    * 🔬 **`F16` (16-Bit Reference — 3116.0 MB):** [`https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf)
  * **Empirical Highlights:** Reaches **`33/39 (84.62%)`** in `Q4_K_M` (`23.4 tok/s`), **`32/39 (82.05%)` + `1/10 Opus` (`OPUS_08`)** in `F16` (`17.34 tok/s` GPU), and unlocks **`2/10 Opus Hard` (`OPUS_01` Pure Regex Engine with `.`/`*`/`+` and `OPUS_08` Trapping Rain Water)** in **`Q6_K`** (`31/39`, `18.9 tok/s`).
* **2. `MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic` (`[Q4_K_M]`, `[Q8_0]`, `[F16]`):**
  * **Architecture & Teacher:** OpenBMB MiniCPM5 1.0B Dense (`128K` context, `<think>` active, `-fa on`) distilled from **Anthropic Claude Opus + Fable 5 V2 Thinking** (`mradermacher`).
  * **Direct `.gguf` Downloads:**
    * ⚡ **`Q4_K_M` (Speed & Operational Pareto King — 0.64 GB):** [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q4_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q4_K_M.gguf)
    * 🎯 **`Q8_0` (Max Cognitive Precision — 1.07 GB):** [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q8_0.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q8_0.gguf)
    * 🔬 **`F16` (16-Bit Bare-Metal Audit — 2066.2 MB):** [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf)
  * **Empirical Highlights:** Blazing **`42.0 tok/s` TG (`203.8 tok/s` PP)** in `Q4_K_M` with **`32/39 (82.05%)`** and **`1/10 Opus Hard`** (`OPUS_06` Partitioned Median of Two Sorted Arrays); **`33/39 (84.62%)`** in `Q8_0`; and **`32/39 (82.05%)` + `1/10 Opus` (`OPUS_06`)** at **`38.69 tok/s` GPU** in `F16`.

---

### 👑 3.5 600M Champions (The Implicit Regularization Triad): `TinyQwen3-Distill-0.6B`, `Qwen3-0.6B-Distill-30B`, `Qwen3-0.6B-Opus4.6`

Evaluated across a full 15-configuration Pareto grid (`Q4_K_M` to `F16`, Sections 8–12 of the Sacred Ledger), these three 600M models demonstrated how teacher lineage interacts with quantization bit-depth:

1. **`TinyQwen3-Distill-0.6B [Q5_K_M]` & `[Q6_K]` (Teacher: DeepSeek-R1):**
   * **Repository & Direct Download (`Q5_K_M` — 423.6 MB):** [`https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q5_K_M.gguf)
   * **Performance:** **`34/39 (87.18%)`** under `Lambda-RLM` (`24/39` Baseline + **`+10 RLM rescues`**, **9/13 Perfect Areas**) at **`41.23 tok/s` TG** (`214.46 tok/s` PP) in `Q5_K_M`, and **`33/39 (84.62%)`** at **`40.72 tok/s`** in `Q6_K` (`472.0 MB`). Moving from 4-bit (`28/39`) to 5-bit unlocked DeepSeek-R1's multi-step reasoning chains under `Lambda-RLM`, while unquantized `F16` (`1142.2 MB`) degraded to `30/39` and `15.98 tok/s`.
2. **`Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT [Q4_K_M]` (Teacher: Qwen3-30B-A3B-Thinking SFT):**
   * **Repository & Direct Download (`Q4_K_M` — 420.3 MB):** [`https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q4_K_M.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q4_K_M.gguf)
   * **Performance:** **`32/39 (82.05%)`** (`29/39` Zero-Shot Baseline — highest zero-shot accuracy in the 600M class, **9/13 Perfect Areas**) at **`43.30 tok/s` TG** and **`291.60 tok/s` PP** (`2.09s` boot). Famous for proving **Implicit Discretization Regularization**: its `Q4_K_M` (`32/39`, `43.3 tok/s`) systematically defeated its own unquantized `F16` (`29/39`, `24.1 tok/s`) by filtering high-frequency distillation tail noise.
3. **`Qwen3-0.6B-Opus4.6-Abliterated [Q8_0]` & `[Q5_K_M]` (Teacher: Anthropic Claude 4.6 Opus):**
   * **Repository & Direct Download (`Q8_0` — 609.8 MB):** [`https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf)
   * **Performance:** **`32/39 (82.05%)`** (`29/39` Baseline, `8/13` Perfect Areas) at `30.43 tok/s` in `Q8_0`, and **`30/39 (76.92%)`** (`29/39` Baseline) with a `2.03s` boot at `36.87 tok/s` in `Q5_K_M` (`423.8 MB`).

---

### 👑 3.6 500M Champion (Sub-600M Record Holder): `MiniCPM4-0.5B [Q8_0]`

* **Architecture:** OpenBMB MiniCPM4 Dense Transformer (`500M` parameters, `32,768` context window, direct non-thinking inference, `-fa on`).
* **Origin / Lineage:** **OpenBMB (`openbmb/MiniCPM4-0.5B`)** — GGUF quantizations by `mradermacher` (`mradermacher/MiniCPM4-0.5B-GGUF`).
* **Direct Hugging Face `.gguf` Downloads:**
  * 🏆 **`Q8_0` (Sub-600M Cognitive Record Holder — 441.4 MB):** [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf)
  * ⚡ **`Q6_K` (56 tok/s CPU Speed King — 341.2 MB):** [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf)
  * 🪶 **`Q5_K_M` (302 MB Compact — 302.3 MB):** [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf)
  * 🔬 **`F16` (16-Bit Reference — 829.3 MB):** [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf)
* **Empirical Performance:**
  * **`[Q8_0]` (`441.4 MB`):** First model in history with half a billion parameters to break the 30-point barrier, scoring **`31/39 (79.49%)`** (`24/39` Baseline + `7` `Lambda-RLM` rescues, `7/13` Perfect Areas) while generating at **`38.60 tok/s` on GPU Vulkan** (`311.56 tok/s` PP) and **`49.99 tok/s` on CPU AVX2** (`556.24 tok/s` CPU PP)!
  * **`[Q6_K]` (`341.2 MB`):** Scores **`30/39 (76.92%)`** (`27/39` Baseline + `3` RLM rescues) at **`37.33 tok/s` GPU** and **`56.02 tok/s` CPU AVX2**.

---

### 👑 3.7 350M Champions (Hybrid Mamba-2 Ultra-Lightweights): `Granite-350M-Gemini3-Think [F16]` & `Granite-4.0-H-350M [Q8_0]`

* **Architecture:** **IBM Granite 4.0 Hybrid (Mamba-2 State-Space Model + Multi-Head Attention)** — `350M` parameters, `128,000` context window, **mandatory `-fa off` (`-fa 0`)** on Vulkan/CPU to preserve Mamba-2 recurrence precision.
* **Champions & Direct Hugging Face `.gguf` Downloads:**
  1. 🏆 **`Granite-350M-Gemini3-Think [F16]` (Teacher: Google Gemini 3 Pro Thinking — 653.2 MB):**
     * **Download:** [`https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf)
     * **Other Quants:** [`Q8_0` (349.2 MB)](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf) | [`Q6_K` (270.7 MB)](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf) | [`Q5_K_M` (240.6 MB)](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf)
     * **Performance:** **`29/39 (74.36%)`** (`25/39` Baseline + `4` RLM rescues, `7/13` Perfect Areas) and **`1/10 (10.0%)` Opus Hard** (`OPUS_06` Partitioned Median of Two Sorted Arrays in $O(\log(\min(N,M)))$, rescued via `Lambda-RLM` in `F16` and `Q6_K`, and solved Zero-Shot in `Q8_0`!). Runs at **`23.08 tok/s` GPU TG** (`105.24 tok/s` PP) and **`10.01 tok/s` CPU TG** (`380.88 tok/s` CPU PP). **The smallest model on Earth (`350M`) ever verified to pass an Opus Hard formal challenge.**
  2. 👑 **`Granite-4.0-H-350M [Q8_0]` (Teacher: IBM Granite 4.0 Hybrid Foundation — 349.2 MB):**
     * **Download:** [`https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf)
     * **Other Quants:** [`Q6_K` (270.7 MB)](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q6_K.gguf) | [`Q5_K_M` (240.6 MB)](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q5_K_M.gguf) | [`Q4_K_M` (212.3 MB)](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q4_K_M.gguf)
     * **Performance:** Matches **`29/39 (74.36%)`** (`18/39` Baseline + **`+11 Lambda-RLM rescues`**, `6/13` Perfect Areas) in **`349.2 MB`** (half the footprint of `F16`) at **`21.80 tok/s` GPU TG** and **`10.54 tok/s` CPU TG** (`399.75 tok/s` CPU PP). Its `Q4_K_M` (`212.3 MB`) achieves **`28/39 (71.79%)`** at `22.18 tok/s` GPU / `12.43 tok/s` CPU.

---

## 4. Master Telemetry Table — All 35 Bare-Metal Variants (350M – 7.0B)

*Sorted by Final 13-Area Cognitive Score (`Lambda-RLM`), then Opus Hard Score, then GPU Generation Throughput (`TG tok/s`).*
*Legend: `Ctx` = Native Context Window | `T:S` = Thinking (`<think>`) Active, `T:N` = Direct Non-Thinking | `FA` = Flash Attention (`on` vs `off`) | `NGL` = GPU Offloaded Layers (`99` = 100% in RX 580 VRAM).*

| Rank | Tier | Model Family | Quant | Config (`Ctx / Think / FA / NGL`) | Size (MB) | Boot (s) | GPU PP (t/s) | GPU TG (t/s) | CPU PP (t/s) | CPU TG (t/s) | 13 Areas: `Base ➔ Final` (`%`) | `+RLM` (13A) | Perfect Areas (`3/3`) | Opus Hard: `Base ➔ Final` | `+RLM` (Opus) | Opus Hard Challenges Solved (`Origin`) |
| :-: | :-: | :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :--- |
| **1** | **3.7B** | **`K2-Horizon-3.7B`** | `Q8_0` | `512K / T:S / FA:on / NGL:99` | 5136.9 | 10.76s | 94.17 | **19.91** | 110.55 | 9.14 | `32/39` ➔ **`37/39` (94.87%)** | **`+5`** | 11/13 | `3/10` ➔ **`3/10` (30%)** | `+0` | `OPUS_04`(Base), `OPUS_05`(Base), `OPUS_09`(Base) |
| **2** | **3.7B** | **`K2-Horizon-3.7B`** 👑 | `Q6_K` | `512K / T:S / FA:on / NGL:99` | 3968.6 | 9.26s | 76.80 | **19.53** | 109.97 | 10.48 | `31/39` ➔ **`37/39` (94.87%)** | **`+6`** | 11/13 | `3/10` ➔ **`3/10` (30%)** | `+0` | `OPUS_04`(Base), `OPUS_05`(Base), `OPUS_07`(Base) |
| **3** | **3.7B** | **`K2-Horizon-3.7B`** ⚡ | `Q5_K_M` | `512K / T:S / FA:on / NGL:99` | 3475.0 | 9.79s | 80.90 | **20.11** | 119.21 | 11.37 | **`36/39`** ➔ **`37/39` (94.87%)** | **`+1`** | 11/13 | `2/10` ➔ **`2/10` (20%)** | `+0` | `OPUS_04`(Base), `OPUS_07`(Base) |
| **4** | **7.0B** | **`K2-Horizon-7B`** ⚠️ | `Q4_K_M` | `512K / T:S / FA:on / NGL:99` | 5333.1 | 5.05s | 15.82 | **6.89** | 41.73 | 8.06 | **`36/39`** ➔ **`37/39` (94.87%)** | **`+1`** | 11/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_08`(Base) *(9 timeouts @ 6.89 t/s)* |
| **5** | **1.7B** | **`Qwen3-1.7B`** 👑 | `Q8_0` | `32K / T:S / FA:on / NGL:99` | 2064.7 | 5.64s | 159.50 | **31.07** | 225.57 | 19.64 | `34/39` ➔ **`36/39` (92.31%)** | **`+2`** | 11/13 | `2/10` ➔ **`2/10` (20%)** | `+0` | `OPUS_06`(Base), `OPUS_07`(Base) |
| **6** | **1.7B** | **`Qwen3-1.7B`** ⚡ | `Q5_K_M` | `32K / T:S / FA:on / NGL:99` | 1403.6 | 5.25s | 182.62 | **31.22** | 243.24 | 24.92 | `32/39` ➔ **`36/39` (92.31%)** | **`+4`** | 11/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_06`(Base) |
| **7** | **3.7B** | **`K2-Horizon-3.7B`** | `Q4_K_M` | `512K / T:S / FA:on / NGL:99` | 3010.4 | 8.19s | 82.57 | **22.59** | 126.38 | 12.54 | `34/39` ➔ **`36/39` (92.31%)** | **`+2`** | 10/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_04`(Base) |
| **8** | **900M** | **`K2-Horizon-0.9B`** 👑 | `Q8_0` | `512K / T:N / FA:on / NGL:99` | 1095.4 | 1.52s | 44.20 | **28.39** | 119.05 | 28.46 | `27/39` ➔ **`35/39` (89.74%)** | **`+8`** | 10/13 | `2/10` ➔ **`3/10` (30%)** | **`+1`** | `OPUS_05`(**RLM**), `OPUS_06`(Base), `OPUS_08`(Base) |
| **9** | **1.7B** | **`Qwen3-1.7B`** | `Q4_K_M` | `32K / T:S / FA:on / NGL:99` | 1223.0 | 5.74s | 174.51 | **33.08** | 252.07 | 26.38 | `34/39` ➔ **`35/39` (89.74%)** | **`+1`** | 10/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_05`(Base) |
| **10** | **1.7B** | **`Qwen3-1.7B`** | `BF16` | `32K / T:S / FA:on / NGL:99` | 3881.2 | 9.73s | 55.68 | **25.88** | 153.65 | 11.06 | `33/39` ➔ **`35/39` (89.74%)** | **`+2`** | 10/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_07`(Base) |
| **11** | **900M** | **`K2-Horizon-0.9B`** 🏆 | `Q6_K` | `512K / T:N / FA:on / NGL:99` | 846.4 | 2.57s | 121.33 | **34.29** | 312.45 | **36.60** | `25/39` ➔ **`34/39` (87.18%)** | **`+9`** | 9/13 | `4/10` ➔ **`4/10` (40%)** | `+0` | `OPUS_05`(Base), `OPUS_06`(Base), `OPUS_08`(Base), `OPUS_09`(Base) |
| **12** | **900M** | **`K2-Horizon-0.9B`** ⚡ | `Q5_K_M` | `512K / T:N / FA:on / NGL:99` | 737.6 | 2.55s | 242.11 | **33.35** | 335.64 | **38.57** | `26/39` ➔ **`33/39` (84.62%)** | **`+7`** | 8/13 | `3/10` ➔ **`4/10` (40%)** | **`+1`** | `OPUS_05`(Base), `OPUS_06`(Base), `OPUS_07`(Base), `OPUS_08`(**RLM**) |
| **13** | **1.0B** | **`MiniCPM5-1B-Opus`** | `F16` | `128K / T:S / FA:on / NGL:99` | 2066.2 | 6.04s | 149.18 | **38.69** | 293.67 | 21.38 | `30/39` ➔ **`32/39` (82.05%)** | **`+2`** | 7/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_06`(Base) |
| **14** | **900M** | **`K2-Horizon-0.9B`** | `Q4_K_M` | `512K / T:N / FA:on / NGL:99` | 635.3 | 2.58s | 183.37 | **37.65** | 354.40 | **43.01** | `21/39` ➔ **`32/39` (82.05%)** | **`+11`** | 7/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_06`(Base) |
| **15** | **1.0B** | **`IBM-GPT-5.4-Coder-1B`** | `F16` | `128K / T:N / FA:off / NGL:99` | 3116.0 | 8.06s | 66.95 | **17.34** | 148.28 | 11.57 | `28/39` ➔ **`32/39` (82.05%)** | **`+4`** | 8/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_08`(Base) |
| **16** | **500M** | **`MiniCPM4-0.5B`** 👑 | `Q8_0` | `32K / T:N / FA:on / NGL:99` | 441.4 | 3.61s | 311.56 | **38.60** | 556.24 | **49.99** | `24/39` ➔ **`31/39` (79.49%)** | **`+7`** | 7/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **17** | **500M** | **`MiniCPM4-0.5B`** | `Q6_K` | `32K / T:N / FA:on / NGL:99` | 341.2 | 3.24s | 267.18 | **37.33** | 524.86 | **56.02** | `27/39` ➔ **`30/39` (76.92%)** | **`+3`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **18** | **500M** | **`MiniCPM4-0.5B`** | `F16` | `32K / T:N / FA:on / NGL:99` | 829.3 | 4.05s | 303.32 | **36.75** | 394.17 | 36.18 | `26/39` ➔ **`30/39` (76.92%)** | **`+4`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **19** | **500M** | **`MiniCPM4-0.5B`** | `Q5_K_M` | `32K / T:N / FA:on / NGL:99` | 302.3 | 4.04s | 295.45 | **32.53** | 569.83 | **54.99** | `22/39` ➔ **`30/39` (76.92%)** | **`+8`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **20** | **350M** | **`Granite-350M-Gemini3`** 👑 | `F16` | `128K / T:S / FA:off / NGL:99` | 653.2 | 4.46s | 105.24 | **23.08** | 380.88 | 10.01 | `25/39` ➔ **`29/39` (74.36%)** | **`+4`** | 7/13 | `0/10` ➔ **`1/10` (10%)** | **`+1`** | `OPUS_06`(**RLM**) |
| **21** | **350M** | **`Granite-4.0-H-350M`** 👑 | `Q8_0` | `128K / T:N / FA:off / NGL:99` | 349.2 | 3.61s | 124.18 | **21.80** | 399.75 | 10.54 | `18/39` ➔ **`29/39` (74.36%)** | **`+11`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **22** | **500M** | **`QwQ-0.5B-Distilled`** | `Q6_K` | `32K / T:S / FA:on / NGL:99` | 482.3 | 3.62s | 290.94 | **48.29** | 424.22 | 30.34 | `24/39` ➔ **`28/39` (71.79%)** | **`+4`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **23** | **350M** | **`Granite-4.0-H-350M`** | `Q4_K_M` | `128K / T:N / FA:off / NGL:99` | 212.3 | 3.26s | 139.12 | **22.18** | 428.20 | 12.43 | `19/39` ➔ **`28/39` (71.79%)** | **`+9`** | 5/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **24** | **500M** | **`QwQ-0.5B-Distilled`** | `Q5_K_M` | `32K / T:S / FA:on / NGL:99` | 400.6 | 6.07s | 63.31 | **50.15** | 405.40 | 46.78 | `24/39` ➔ **`27/39` (69.23%)** | **`+3`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **25** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `F16` | `32K / T:S / FA:on / NGL:99` | 948.1 | 4.49s | 234.72 | **43.91** | 440.34 | 30.34 | `23/39` ➔ **`27/39` (69.23%)** | **`+4`** | 7/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **26** | **350M** | **`Granite-4.0-H-350M`** | `Q6_K` | `128K / T:N / FA:off / NGL:99` | 270.7 | 4.02s | 109.38 | **21.92** | 164.61 | 2.07 | `17/39` ➔ **`27/39` (69.23%)** | **`+10`** | 4/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **27** | **350M** | **`Granite-350M-Gemini3`** | `Q8_0` | `128K / T:S / FA:off / NGL:99` | 349.2 | 3.63s | 111.19 | **21.99** | 420.63 | 10.68 | `21/39` ➔ **`26/39` (66.67%)** | **`+5`** | 5/13 | `1/10` ➔ **`1/10` (10%)** | `+0` | `OPUS_06`(Base) |
| **28** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `Q6_K` | `32K / T:S / FA:on / NGL:99` | 482.3 | 4.02s | 254.96 | **50.18** | 494.02 | 43.08 | `23/39` ➔ **`26/39` (66.67%)** | **`+3`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **29** | **500M** | **`QwQ-0.5B-Distilled`** | `Q8_0` | `32K / T:S / FA:on / NGL:99` | 506.5 | 2.56s | 220.00 | **50.03** | 510.16 | 43.39 | `22/39` ➔ **`26/39` (66.67%)** | **`+4`** | 5/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **30** | **500M** | **`QwQ-0.5B-Distilled`** | `F16` | `32K / T:S / FA:on / NGL:99` | 948.1 | 3.83s | 182.50 | **43.80** | 389.69 | 23.50 | `22/39` ➔ **`26/39` (66.67%)** | **`+4`** | 5/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **31** | **350M** | **`Granite-350M-Gemini3`** | `Q6_K` | `128K / T:S / FA:off / NGL:99` | 270.7 | 2.15s | 123.05 | **21.88** | 375.06 | 6.33 | `23/39` ➔ **`25/39` (64.10%)** | **`+2`** | 4/13 | `0/10` ➔ **`1/10` (10%)** | **`+1`** | `OPUS_06`(**RLM**) |
| **32** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `Q8_0` | `32K / T:S / FA:on / NGL:99` | 506.5 | 4.04s | 260.23 | **50.60** | 522.88 | 46.63 | `22/39` ➔ **`25/39` (64.10%)** | **`+3`** | 5/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **33** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `Q5_K_M` | `32K / T:S / FA:on / NGL:99` | 400.6 | 3.63s | 287.10 | **47.81** | 469.97 | 45.54 | `18/39` ➔ **`24/39` (61.54%)** | **`+6`** | 6/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **34** | **350M** | **`Granite-4.0-H-350M`** | `Q5_K_M` | `128K / T:N / FA:off / NGL:99` | 240.6 | 3.22s | 134.09 | **14.10** | 142.47 | 2.33 | `16/39` ➔ **`24/39` (61.54%)** | **`+8`** | 2/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |
| **35** | **350M** | **`Granite-350M-Gemini3`** | `Q5_K_M` | `128K / T:S / FA:off / NGL:99` | 240.6 | 3.27s | 131.78 | **21.87** | 407.37 | 11.03 | `9/39` ➔ **`19/39` (48.72%)** | **`+10`** | 2/13 | `0/10` ➔ **`0/10` (0%)** | `+0` | — |

---

## 5. Area-by-Area Cognitive Decomposition Matrix (`A01` – `A13`, `Baseline ➔ Lambda-RLM`)

Each cell reports `Baseline_Passed ➔ Final_Lambda_RLM_Passed` out of `3` formal tests per cognitive area. Bold cells highlight **`Lambda-RLM` cognitive rescues** where recursive metacognition repaired a zero-shot failure.

* **A01:** Reflex & Triage (Intent Routing & Dispatch) | **A02:** Software Engineering (Code, Refactor, Patches) | **A03:** Mathematics & Proofs | **A04:** OS Automation & RPA | **A05:** Perennial Memory & Knowledge Graphs | **A06:** Metacognition & LTI Stability | **A07:** Red-Team Crucible (Fuzzing & Security) | **A08:** Vocal Synthesis & Phonetic TTS Normalization | **A09:** Multimodal & Vision Geometry (SVG/OCR) | **A10:** Deliberative Planning & PDDL | **A11:** Scientific Reasoning | **A12:** Language & Discourse Logic | **A13:** Hardware Governor (Clocks, Temps & VRAM).

| # | Model & Quant | A01 Triage | A02 Code | A03 Math | A04 RPA | A05 Mem | A06 Meta | A07 RedT | A08 Vocal | A09 Vis | A10 PDDL | A11 Sci | A12 Lang | A13 Hdw | Total (`Base ➔ RLM`) |
| :-: | :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **1** | **`K2-Horizon-3.7B`** `Q8_0` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`0➔3`** | `2➔2` | `3➔3` | `3➔3` | **`2➔3`** | **`2➔3`** | **`32➔37` (+5)** |
| **2** | **`K2-Horizon-3.7B`** `Q6_K` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | **`2➔3`** | `3➔3` | `3➔3` | **`0➔3`** | `2➔2` | `3➔3` | `3➔3` | **`2➔3`** | **`2➔3`** | **`31➔37` (+6)** |
| **3** | **`K2-Horizon-3.7B`** `Q5_K_M` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`2➔3`** | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`36➔37` (+1)** |
| **4** | **`K2-Horizon-7B`** `Q4_K_M` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | **`2➔3`** | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`36➔37` (+1)** |
| **5** | **`Qwen3-1.7B`** `Q8_0` | `3➔3` | **`2➔3`** | `1➔1` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | `2➔2` | **`2➔3`** | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`34➔36` (+2)** |
| **6** | **`Qwen3-1.7B`** `Q5_K_M` | `3➔3` | **`2➔3`** | `1➔1` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`1➔2`** | `3➔3` | **`2➔3`** | `3➔3` | **`2➔3`** | `3➔3` | **`32➔36` (+4)** |
| **7** | **`K2-Horizon-3.7B`** `Q4_K_M` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`1➔2`** | `2➔2` | `3➔3` | `3➔3` | `3➔3` | **`2➔3`** | **`34➔36` (+2)** |
| **8** | **`K2-Horizon-0.9B`** `Q8_0` | **`2➔3`** | `3➔3` | `2➔2` | `3➔3` | **`2➔3`** | **`2➔3`** | `3➔3` | `1➔1` | `2➔2` | **`2➔3`** | **`2➔3`** | **`1➔3`** | **`2➔3`** | **`27➔35` (+8)** |
| **9** | **`Qwen3-1.7B`** `Q4_K_M` | `3➔3` | `2➔2` | `1➔1` | **`2➔3`** | `3➔3` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`34➔35` (+1)** |
| **10** | **`Qwen3-1.7B`** `BF16` | `3➔3` | `2➔2` | `1➔1` | **`2➔3`** | `3➔3` | `3➔3` | `3➔3` | `2➔2` | **`2➔3`** | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`33➔35` (+2)** |
| **11** | **`K2-Horizon-0.9B`** `Q6_K` | `2➔2` | `3➔3` | `2➔2` | `3➔3` | **`1➔3`** | **`2➔3`** | `3➔3` | `1➔1` | **`1➔2`** | **`2➔3`** | **`2➔3`** | **`1➔3`** | **`2➔3`** | **`25➔34` (+9)** |
| **12** | **`K2-Horizon-0.9B`** `Q5_K_M` | `2➔2` | `3➔3` | **`1➔2`** | `3➔3` | **`2➔3`** | `3➔3` | `3➔3` | `1➔1` | `2➔2` | **`1➔3`** | **`2➔3`** | **`1➔2`** | **`2➔3`** | **`26➔33` (+7)** |
| **13** | **`MiniCPM5-1B-Opus`** `F16` | **`2➔3`** | **`2➔3`** | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | `1➔1` | `2➔2` | `2➔2` | `3➔3` | `2➔2` | `2➔2` | **`30➔32` (+2)** |
| **14** | **`K2-Horizon-0.9B`** `Q4_K_M` | **`1➔3`** | `3➔3` | `2➔2` | `3➔3` | **`1➔2`** | **`2➔3`** | `3➔3` | `1➔1` | **`1➔2`** | **`1➔3`** | **`1➔3`** | **`1➔2`** | **`1➔2`** | **`21➔32` (+11)** |
| **15** | **`IBM-GPT-5.4-Coder-1B`** `F16` | `3➔3` | `3➔3` | `2➔2` | **`2➔3`** | `3➔3` | `3➔3` | `3➔3` | **`0➔1`** | `1➔1` | `2➔2` | **`1➔2`** | `3➔3` | **`2➔3`** | **`28➔32` (+4)** |
| **16** | **`MiniCPM4-0.5B`** `Q8_0` | `3➔3` | `2➔2` | `2➔2` | `3➔3` | `3➔3` | **`2➔3`** | **`2➔3`** | **`0➔1`** | `2➔2` | `1➔1` | **`2➔3`** | **`1➔2`** | **`1➔3`** | **`24➔31` (+7)** |
| **17** | **`MiniCPM4-0.5B`** `Q6_K` | `3➔3` | `2➔2` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `1➔1` | **`0➔1`** | `2➔2` | `2➔2` | `3➔3` | `2➔2` | **`1➔3`** | **`27➔30` (+3)** |
| **18** | **`MiniCPM4-0.5B`** `F16` | `3➔3` | `2➔2` | `2➔2` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | **`0➔1`** | `2➔2` | `1➔1` | **`2➔3`** | `2➔2` | **`1➔3`** | **`26➔30` (+4)** |
| **19** | **`MiniCPM4-0.5B`** `Q5_K_M` | `3➔3` | `2➔2` | `2➔2` | **`2➔3`** | `3➔3` | **`1➔2`** | **`1➔3`** | **`0➔1`** | `2➔2` | **`0➔1`** | **`2➔3`** | `2➔2` | **`2➔3`** | **`22➔30` (+8)** |
| **20** | **`Granite-350M-Gemini3`** `F16` | **`2➔3`** | `0➔0` | **`0➔1`** | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `1➔1` | `2➔2` | **`2➔3`** | **`2➔3`** | `2➔2` | `3➔3` | **`25➔29` (+4)** |
| **21** | **`Granite-4.0-H-350M`** `Q8_0` | **`1➔3`** | **`1➔2`** | `3➔3` | `2➔2` | `3➔3` | `2➔2` | **`1➔3`** | **`0➔1`** | `1➔1` | **`0➔1`** | **`2➔3`** | **`1➔2`** | **`1➔3`** | **`18➔29` (+11)** |
| **22** | **`QwQ-0.5B-Distilled`** `Q6_K` | `3➔3` | `0➔0` | **`0➔1`** | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `1➔1` | **`1➔2`** | **`1➔2`** | **`2➔3`** | `2➔2` | `3➔3` | **`24➔28` (+4)** |
| **23** | **`Granite-4.0-H-350M`** `Q4_K_M` | **`0➔3`** | `2➔2` | **`1➔3`** | `2➔2` | `2➔2` | **`2➔3`** | **`1➔2`** | `0➔0` | `2➔2` | **`1➔2`** | `3➔3` | **`0➔1`** | `3➔3` | **`19➔28` (+9)** |
| **24** | **`QwQ-0.5B-Distilled`** `Q5_K_M` | `3➔3` | `0➔0` | `0➔0` | `2➔2` | `3➔3` | `3➔3` | **`2➔3`** | `1➔1` | **`1➔2`** | **`2➔3`** | `2➔2` | `2➔2` | `3➔3` | **`24➔27` (+3)** |
| **25** | **`Qwen2.5-0.5B-OpenR1`** `F16` | `3➔3` | `2➔2` | `0➔0` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `1➔1` | **`0➔1`** | **`2➔3`** | `0➔0` | **`2➔3`** | **`2➔3`** | **`23➔27` (+4)** |
| **26** | **`Granite-4.0-H-350M`** `Q6_K` | **`1➔3`** | **`1➔2`** | `3➔3` | `2➔2` | `2➔2` | `2➔2` | **`2➔3`** | **`0➔1`** | `1➔1` | **`0➔1`** | `2➔2` | **`0➔2`** | **`1➔3`** | **`17➔27` (+10)** |
| **27** | **`Granite-350M-Gemini3`** `Q8_0` | **`1➔3`** | `0➔0` | **`0➔2`** | `2➔2` | `3➔3` | `1➔1` | `3➔3` | `1➔1` | `2➔2` | `2➔2` | **`2➔3`** | `1➔1` | `3➔3` | **`21➔26` (+5)** |
| **28** | **`Qwen2.5-0.5B-OpenR1`** `Q6_K` | `3➔3` | `2➔2` | `0➔0` | `2➔2` | `2➔2` | `3➔3` | `3➔3` | `1➔1` | `1➔1` | **`2➔3`** | `0➔0` | **`2➔3`** | **`2➔3`** | **`23➔26` (+3)** |
| **29** | **`QwQ-0.5B-Distilled`** `Q8_0` | `3➔3` | **`0➔1`** | `0➔0` | `2➔2` | `3➔3` | **`2➔3`** | `3➔3` | `1➔1` | `2➔2` | **`1➔2`** | `1➔1` | `2➔2` | **`2➔3`** | **`22➔26` (+4)** |
| **30** | **`QwQ-0.5B-Distilled`** `F16` | `3➔3` | **`0➔1`** | `0➔0` | `2➔2` | `2➔2` | **`2➔3`** | `3➔3` | `1➔1` | **`1➔2`** | **`2➔3`** | `1➔1` | `2➔2` | `3➔3` | **`22➔26` (+4)** |
| **31** | **`Granite-350M-Gemini3`** `Q6_K` | **`2➔3`** | `0➔0` | `0➔0` | `2➔2` | **`2➔3`** | `2➔2` | `3➔3` | `1➔1` | `2➔2` | `2➔2` | `3➔3` | `2➔2` | `2➔2` | **`23➔25` (+2)** |
| **32** | **`Qwen2.5-0.5B-OpenR1`** `Q8_0` | `3➔3` | `2➔2` | `0➔0` | `2➔2` | `2➔2` | `3➔3` | `3➔3` | `1➔1` | `1➔1` | **`2➔3`** | `0➔0` | **`1➔2`** | **`2➔3`** | **`22➔25` (+3)** |
| **33** | **`Qwen2.5-0.5B-OpenR1`** `Q5_K_M` | `3➔3` | `1➔1` | `0➔0` | `2➔2` | `1➔1` | `3➔3` | `3➔3` | `1➔1` | **`0➔1`** | **`1➔3`** | `0➔0` | **`1➔3`** | **`2➔3`** | **`18➔24` (+6)** |
| **34** | **`Granite-4.0-H-350M`** `Q5_K_M` | **`1➔3`** | `2➔2` | **`1➔3`** | `2➔2` | `2➔2` | `2➔2` | `2➔2` | **`0➔1`** | `1➔1` | **`0➔1`** | `1➔1` | **`1➔2`** | **`1➔2`** | **`16➔24` (+8)** |
| **35** | **`Granite-350M-Gemini3`** `Q5_K_M` | **`0➔1`** | `0➔0` | **`0➔1`** | **`1➔2`** | **`1➔3`** | **`0➔2`** | `3➔3` | `0➔0` | `2➔2` | **`1➔2`** | **`0➔1`** | `1➔1` | **`0➔1`** | **`9➔19` (+10)** |

---

## 6. Per-Opus Hard Algorithmic Matrix (`OPUS_01` – `OPUS_10`, Formal AST/`pytest`)

Every challenge in the **10 Opus Hard Suite** requires synthesizing a pure Python function that passes strict AST inspection (no forbidden imports or built-ins) and multiple adversarial `pytest` edge-case assertions within an `8.0s` execution sandbox.
*(All 17 remaining 500M and 350M variants not listed in the positive solver rows below scored `0 ➔ 0/10` across `OPUS_01`–`OPUS_10`).*

* **`OPUS_01`:** Pure Regex Engine (`.`, `*`, `+` without `re`) | **`OPUS_02`:** Algebraic Parser (Unary `-` & Right-Associative `^` without `eval`) | **`OPUS_03`:** 2D State-Space Dijkstra (Up to $K$ Free Edges) | **`OPUS_04`:** 2D Monotonic Stack Maximal Binary Rectangle | **`OPUS_05`:** Bitmask DP Open Traveling Salesperson Problem (TSP) | **`OPUS_06`:** Partitioned Binary Search Median of Two Sorted Arrays ($O(\log(\min(N,M)))$) | **`OPUS_07`:** DP/Stack Longest Valid Parentheses Trap | **`OPUS_08`:** Two-Pointers Trapping Rain Water | **`OPUS_09`:** Binary Tree Any-to-Any Maximum Path Sum with Negative Nodes | **`OPUS_10`:** Pure Backtracking DPLL SAT Solver for CNF Formulas.

| Model & Quant | Tier | `OPUS_01` Regex | `OPUS_02` Parser | `OPUS_03` Dijkstra | `OPUS_04` MaxRect 2D | `OPUS_05` Bitmask TSP | `OPUS_06` Median Arrays | `OPUS_07` Parentheses | `OPUS_08` RainWater | `OPUS_09` Tree MaxPath | `OPUS_10` DPLL SAT | Opus Score (`Base ➔ Final`) |
| :--- | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| **`K2-Horizon-0.9B`** `Q6_K` 🏆 | **900M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ✅ **Base** | ❌ Fail | ✅ **Base** | ✅ **Base** | ❌ Fail | **`4 ➔ 4/10` (40%)** |
| **`K2-Horizon-0.9B`** `Q5_K_M` ⚡ | **900M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ✅ **Base** | ✅ **Base** | ✅ **RLM** 🎯 | ❌ Fail | ❌ Fail | **`3 ➔ 4/10` (40%)** |
| **`K2-Horizon-3.7B`** `Q6_K` 👑 | **3.7B** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ✅ **Base** | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | **`3 ➔ 3/10` (30%)** |
| **`K2-Horizon-3.7B`** `Q8_0` | **3.7B** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ✅ **Base** | ⏱️ Timeout | ❌ Fail | ⏱️ Timeout | ✅ **Base** | ❌ Fail | **`3 ➔ 3/10` (30%)** |
| **`K2-Horizon-0.9B`** `Q8_0` 👑 | **900M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **RLM** 🎯 | ✅ **Base** | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | **`2 ➔ 3/10` (30%)** |
| **`K2-Horizon-3.7B`** `Q5_K_M` | **3.7B** | ⏱️ Timeout | ⏱️ Timeout | ❌ Fail | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | **`2 ➔ 2/10` (20%)** |
| **`Qwen3-1.7B`** `Q8_0` 👑 | **1.7B** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | **`2 ➔ 2/10` (20%)** |
| **`K2-Horizon-7B`** `Q4_K_M` | **7.0B** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | **`1 ➔ 1/10` (10%)** |
| **`Qwen3-1.7B`** `Q5_K_M` | **1.7B** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`K2-Horizon-3.7B`** `Q4_K_M` | **3.7B** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | **`1 ➔ 1/10` (10%)** |
| **`Qwen3-1.7B`** `Q4_K_M` | **1.7B** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`Qwen3-1.7B`** `BF16` | **1.7B** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`MiniCPM5-1B-Opus`** `F16` | **1.0B** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`K2-Horizon-0.9B`** `Q4_K_M` | **900M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`IBM-GPT-5.4-Coder-1B`** `F16` | **1.0B** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`Granite-350M-Gemini3`** `F16` 👑 | **350M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **RLM** 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 1/10` (10%)** |
| **`Granite-350M-Gemini3`** `Q8_0` | **350M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **`Granite-350M-Gemini3`** `Q6_K` | **350M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **RLM** 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 1/10` (10%)** |
| *(17 Other 500M/350M Variants)* | **350M/500M** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |

> **Historical Note on 1.0B Quantization Duels (Section 8 of the Sacred Ledger):** In addition to the `F16` checks above, **`IBM-GPT-5.4-Coder-1B [Q6_K]`** (`1.25 GB`) solved **`2/10` Opus Hard Zero-Shot** (`OPUS_01` Pure Regex Engine and `OPUS_08` Trapping Rain Water), and **`MiniCPM5-1B-Claude-Opus [Q4_K_M]`** (`0.64 GB`) solved **`1/10` Opus Hard** (`OPUS_06` Median of Two Sorted Arrays) at `42.0 tok/s`.

---

## 7. Complete Direct Hugging Face `.gguf` Download Catalog

Every checkpoint below was verified via HTTP 200 direct download and bare-metal execution.

| # | Model ID | Weight Class | Teacher / Distiller Lineage | Quant | Size (MB) | Direct Hugging Face `.gguf` Download URL |
| :-: | :--- | :-: | :--- | :-: | :-: | :--- |
| 1 | `k2_horizon_3_7b__q8_0` | 3.7B | IFM K2-Horizon Native 512K | `Q8_0` | 5136.9 | [`K2-Horizon-4B-Q8_0.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf) |
| 2 | `k2_horizon_3_7b__q6_k` | 3.7B | IFM K2-Horizon Native 512K | `Q6_K` | 3968.6 | [`K2-Horizon-4B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf) |
| 3 | `k2_horizon_3_7b__q5_k_m` | 3.7B | IFM K2-Horizon Native 512K | `Q5_K_M` | 3475.0 | [`K2-Horizon-4B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf) |
| 4 | `k2_horizon_3_7b__q4_k_m` | 3.7B | IFM K2-Horizon Native 512K | `Q4_K_M` | 3010.4 | [`K2-Horizon-4B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf) |
| 5 | `k2_horizon_7b__q4_k_m` | 7.0B | IFM K2-Horizon Native 512K | `Q4_K_M` | 5333.1 | [`K2-Horizon-7B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q4_K_M.gguf) |
| 6 | `qwen3_1_7b__bf16` | 1.7B | Alibaba Qwen3 Native Thinking | `BF16` | 3881.2 | [`Qwen_Qwen3-1.7B-bf16.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf) |
| 7 | `qwen3_1_7b__q8_0` | 1.7B | Alibaba Qwen3 Native Thinking | `Q8_0` | 2064.7 | [`Qwen_Qwen3-1.7B-Q8_0.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf) |
| 8 | `qwen3_1_7b__q5_k_m` | 1.7B | Alibaba Qwen3 Native Thinking | `Q5_K_M` | 1403.6 | [`Qwen_Qwen3-1.7B-Q5_K_M.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf) |
| 9 | `qwen3_1_7b__q4_k_m` | 1.7B | Alibaba Qwen3 Native Thinking | `Q4_K_M` | 1223.0 | [`Qwen_Qwen3-1.7B-Q4_K_M.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf) |
| 10 | `ibm_gpt54_coder_1b__f16` | 1.0B | OpenAI GPT-5.4 Coder Distill | `F16` | 3116.0 | [`IBM-GPT-5.4-Coder-1B.f16.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf) |
| 11 | `minicpm5_1b_opus__f16` | 1.0B | Claude Opus + Fable 5 V2 Thinking | `F16` | 2066.2 | [`MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf) |
| 12 | `k2_horizon_0_9b__q8_0` | 900M | IFM K2-Horizon Native 512K | `Q8_0` | 1095.4 | [`K2-Horizon-1B-Q8_0.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf) |
| 13 | `k2_horizon_0_9b__q6_k` | 900M | IFM K2-Horizon Native 512K | `Q6_K` | 846.4 | [`K2-Horizon-1B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf) |
| 14 | `k2_horizon_0_9b__q5_k_m` | 900M | IFM K2-Horizon Native 512K | `Q5_K_M` | 737.6 | [`K2-Horizon-1B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf) |
| 15 | `k2_horizon_0_9b__q4_k_m` | 900M | IFM K2-Horizon Native 512K | `Q4_K_M` | 635.3 | [`K2-Horizon-1B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf) |
| 16 | `minicpm4_05b__f16` | 500M | OpenBMB MiniCPM4 Base | `F16` | 829.3 | [`MiniCPM4-0.5B.f16.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf) |
| 17 | `minicpm4_05b__q8_0` | 500M | OpenBMB MiniCPM4 Base | `Q8_0` | 441.4 | [`MiniCPM4-0.5B.Q8_0.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf) |
| 18 | `minicpm4_05b__q6_k` | 500M | OpenBMB MiniCPM4 Base | `Q6_K` | 341.2 | [`MiniCPM4-0.5B.Q6_K.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf) |
| 19 | `minicpm4_05b__q5_k_m` | 500M | OpenBMB MiniCPM4 Base | `Q5_K_M` | 302.3 | [`MiniCPM4-0.5B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf) |
| 20 | `qwq_05b_distilled__f16` | 500M | Alibaba QwQ / OpenAI o1 SFT | `F16` | 948.1 | [`QwQ-0.5B-Distilled-SFT.f16.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.f16.gguf) |
| 21 | `qwq_05b_distilled__q8_0` | 500M | Alibaba QwQ / OpenAI o1 SFT | `Q8_0` | 506.5 | [`QwQ-0.5B-Distilled-SFT.Q8_0.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q8_0.gguf) |
| 22 | `qwq_05b_distilled__q6_k` | 500M | Alibaba QwQ / OpenAI o1 SFT | `Q6_K` | 482.3 | [`QwQ-0.5B-Distilled-SFT.Q6_K.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q6_K.gguf) |
| 23 | `qwq_05b_distilled__q5_k_m` | 500M | Alibaba QwQ / OpenAI o1 SFT | `Q5_K_M` | 400.6 | [`QwQ-0.5B-Distilled-SFT.Q5_K_M.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q5_K_M.gguf) |
| 24 | `qwen25_05b_openr1__f16` | 500M | DeepSeek-R1 Distill | `F16` | 948.1 | [`Qwen2.5-0.5B-Open-R1-Distill_f16.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_f16.gguf) |
| 25 | `qwen25_05b_openr1__q8_0` | 500M | DeepSeek-R1 Distill | `Q8_0` | 506.5 | [`Qwen2.5-0.5B-Open-R1-Distill_Q8_0.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q8_0.gguf) |
| 26 | `qwen25_05b_openr1__q6_k` | 500M | DeepSeek-R1 Distill | `Q6_K` | 482.3 | [`Qwen2.5-0.5B-Open-R1-Distill_Q6_K.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q6_K.gguf) |
| 27 | `qwen25_05b_openr1__q5_k_m` | 500M | DeepSeek-R1 Distill | `Q5_K_M` | 400.6 | [`Qwen2.5-0.5B-Open-R1-Distill_Q5_K_M.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q5_K_M.gguf) |
| 28 | `granite_gemini3_350m__f16` | 350M | Google Gemini 3 Pro Thinking | `F16` | 653.2 | [`granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf) |
| 29 | `granite_gemini3_350m__q8_0` | 350M | Google Gemini 3 Pro Thinking | `Q8_0` | 349.2 | [`granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf) |
| 30 | `granite_gemini3_350m__q6_k` | 350M | Google Gemini 3 Pro Thinking | `Q6_K` | 270.7 | [`granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf) |
| 31 | `granite_gemini3_350m__q5_k_m` | 350M | Google Gemini 3 Pro Thinking | `Q5_K_M` | 240.6 | [`granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf) |
| 32 | `granite_h_350m__q8_0` | 350M | IBM Granite 4.0 Hybrid Base | `Q8_0` | 349.2 | [`granite-4.0-h-350m-Q8_0.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf) |
| 33 | `granite_h_350m__q6_k` | 350M | IBM Granite 4.0 Hybrid Base | `Q6_K` | 270.7 | [`granite-4.0-h-350m-Q6_K.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q6_K.gguf) |
| 34 | `granite_h_350m__q5_k_m` | 350M | IBM Granite 4.0 Hybrid Base | `Q5_K_M` | 240.6 | [`granite-4.0-h-350m-Q5_K_M.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q5_K_M.gguf) |
| 35 | `granite_h_350m__q4_k_m` | 350M | IBM Granite 4.0 Hybrid Base | `Q4_K_M` | 212.3 | [`granite-4.0-h-350m-Q4_K_M.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q4_K_M.gguf) |

---

## 8. Four Empirical Laws Discovered in the Laboratory

### Law 1: The Bit-Depth Sensitivity Regime Inversion (Sub-1B vs. Above 1.7B)
* **Below 1.0B (`350M` – `900M`):** Ultra-compact models possess low parameter redundancy per attention/SSM head. Increasing quantization precision from `Q4_K_M` to `Q6_K` or `Q8_0` yields massive cognitive and algorithmic jumps without hurting throughput:
  * `MiniCPM4-0.5B` jumps from `29/39` (`Q4_K_M`) to **`31/39` (`Q8_0`)** at `49.99 tok/s` CPU.
  * `K2-Horizon-0.9B` jumps from `32/39 & 1/10 Opus` (`Q4_K_M`) to **`34/39 & 4/10 Opus` (`Q6_K`)** and **`35/39 & 3/10 Opus` (`Q8_0`)**.
  * `Granite-350M-Gemini3` unlocks **`1/10 Opus Hard`** only at `Q6_K`, `Q8_0`, and `F16` (`0/10` at `Q4_K_M`/`Q5_K_M`).
* **The Implicit Discretization Regularization Exception in High-Ratio SFT Distills (`600M`):** When a `600M` student is heavily SFT-distilled from a `30B+` teacher (`Qwen3-0.6B-Distill-30B`), unquantized `F16` retains high-frequency residual tail noise that causes attention dispersion (`29/39` at `24.1 tok/s`), whereas `Q4_K_M` (`Qwen-30B` teacher, `32/39` at `43.3 tok/s`) and `Q5_K_M` (`TinyQwen3-R1` teacher, `34/39` at `41.2 tok/s`) act as an optimal low-pass spectral filter.
* **Above 1.7B (`1.7B` – `4.0B`):** **`Q5_K_M` and `Q6_K` represent the absolute Pareto optimum.** Moving to unquantized `F16`/`BF16` degrades generation speed by **44% to 71%** and can even reduce score (`Qwen3-1.7B [BF16]` scores `35/39` at `25.88 tok/s` vs. `36/39` at `31.22 tok/s` in `Q5_K_M`).

### Law 2: Hybrid Mamba-2 + Attention Flash Attention Numerical Degradation on Vulkan
* In hybrid State-Space Model (SSM / Mamba-2) + Attention architectures (`IBM Granite 4.0 Hybrid`: `Granite-4.0-H-350M`, `Granite-350M-Gemini3`, `IBM-GPT-5.4-Coder-1B`), enabling Vulkan Flash Attention (`-fa on`) introduces numerical precision drift across recurrent state updates.
* Explicitly disabling Flash Attention (**`-fa off` / `-fa 0`**) immediately restores mathematical and syntactic stability, propelling `Granite-4.0-H-350M [Q8_0]` to **`29/39 (74.36%)`** in just `349 MB` and allowing `Granite-350M-Gemini3` to solve `OPUS_06`.

### Law 3: The 8 GB GDDR5 VRAM Bandwidth & Reasoning Timeout Cliff on 7B Models
* On an 8 GB GDDR5 GPU (`224 GB/s` bandwidth), a `3.7B` model in `Q5_K_M` (`3.47 GB`) or `Q6_K` (`3.97 GB`) leaves over `4 GB` of headroom for KV cache and compute buffers, sustaining **`19.5 to 20.1 tok/s`** and completing deep `<think>` chains well within timeout limits (`3/10 Opus Hard`).
* A `7.0B` model in `Q4_K_M` (`5.33 GB`), despite fitting in VRAM (`-ngl 99`), saturates memory bandwidth and KV cache capacity, collapsing generation speed to **`6.89 tok/s`** (slower than 8-thread CPU AVX2 at `8.06 tok/s`). In long-horizon `<think>` tasks like Opus Hard, this 3x throughput penalty causes `240s` timeouts on 90% of problems (`1/10 Opus Hard`), proving that **a well-quantized `3.7B` (`Q6_K`/`Q5_K_M`) outperforms `7B` (`Q4_K_M`) in real-world autonomous coding on 8 GB GPUs**.

### Law 4: `Lambda-RLM` Recursive Metacognition Rescue Mechanics
* Across the 35 bare-metal variants in Table 4, **`Lambda-RLM` executed `+173` verified cognitive rescues** in the 13 Cognitive Areas (`+127` across the 26 Flyweight variants and `+46` across the 9 K2-Horizon variants), plus **4 formal LeetCode Hard rescues** in the Opus Hard suite (`OPUS_05` on `K2-Horizon-0.9B [Q8_0]`, `OPUS_08` on `K2-Horizon-0.9B [Q5_K_M]`, and `OPUS_06` on `Granite-350M-Gemini3 [F16]` & `[Q6_K]`).
* **Mechanism:** Small models frequently understand the core algorithm or domain concept on Pass 1 but fail on a boundary condition, off-by-one index, or output formatting constraint. By feeding the deterministic `pytest` / validator failure trace back into `Lambda-RLM`, compact models (`350M` to `3.7B`) achieve final verification accuracy rivaling models 3x to 10x their parameter count.

---

## 📖 Citation & Reproducibility

To reproduce any benchmark in this laboratory on your own hardware:
1. Download the desired `.gguf` checkpoint from [Section 7](#7-complete-direct-hugging-face-gguf-download-catalog).
2. Inspect the exact prompts and formal AST/`pytest` verifiers in [`TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md`](TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md).
3. Run the tournament and audit scripts in [`suite/`](suite/) against your local `llama-server` and `llama-bench` binaries, and compare against the immutable telemetry proofs in [`proofs/`](proofs/).

```bibtex
@techreport{aethermind2026benchmarks,
  title       = {AetherMind Bare-Metal LLM Experimental Benchmark Laboratory: Full Quantization Grid & Lambda-RLM Formal Verification (350M to 7B+)},
  author      = {Ruan, Mestre and AetherMind Autonomous Research Lab},
  year        = {2026},
  month       = {November},
  institution = {AetherMind Apotheosis Laboratory},
  note        = {35 Bare-Metal GGUF Variants Audited across 13 Cognitive Areas (39 Tests) and 10 Opus Hard AST/pytest Challenges on AMD RX 580 8GB Vulkan & AVX2 CPU}
}
```
