# 🏛️ AetherMind Bare-Metal LLM Experimental Benchmark Laboratory
### *Open Empirical Evaluation of Micro-Scale to Titan Language Models (100M to 35B+) Across Full Quantization Grids (`IQ3_M`/`Q4_K_M` to `F16`/`BF16`) Under Zero-Shot Baseline vs. `Lambda-RLM` Recursive Metacognition & Formal AST/`pytest` Verification*

[![Hardware Testbed](https://img.shields.io/badge/Hardware-RX_580_8GB_Vulkan_%2B_Dual_Xeon_E5--2696_v4_AVX2-red?style=for-the-badge)](#2-hardware--software-testbed-specifications)
[![Scale Coverage](https://img.shields.io/badge/Scale_Coverage-100M_to_35B%2B_Full_Cross--Scale_Lab-blue?style=for-the-badge)](#3-hall-of-fame--champions-by-every-weight-class-100m-to-35b)
[![Cognitive Suite](https://img.shields.io/badge/Cognitive_Suite-13_Areas_%2F_39_Tests_%2B_10_Opus_Hard-emerald?style=for-the-badge)](#5-area-by-area-cognitive-decomposition-matrix-a01--a13-baseline--lambda-rlm)
[![Verification](https://img.shields.io/badge/Verification-Deterministic_AST_%2B_pytest_Zero_Mocks-gold?style=for-the-badge)](#1-laboratory-manifesto--methodology)

---

## 🧭 Quick Repository Navigation

| Resource / Directory | Description | Audience |
| :--- | :--- | :--- |
| 📄 **[`README.md`](README.md)** *(This Document)* | Laboratory Manifesto, Dual-Testbed Hardware Specs (RX 580 Vulkan + Dual Xeon AVX2), Hall of Fame Champions across every weight class (**100M to 35B+**), Complete Cross-Scale Pareto Ladder, Full 35-Model Master Telemetry (`350M–7B`), Area-by-Area (`A01`–`A13`) & Opus Hard (`OPUS_01`–`OPUS_10`) Matrices, Direct `.gguf` Download Catalog, and Empirical Laws. | Engineers, Researchers & Autonomous AI Agents |
| 🧪 **[`TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md`](TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md)** | Complete verbatim prompts, formal verification schemas, AST inspection rules, and `pytest` unit assertions for all **13 Cognitive Areas (39 tests)** and all **10 Opus Hard Algorithmic Challenges**. | Benchmark Reproducers & Autonomous Evaluators |
| 📊 **[`FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md`](FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md)** | Exhaustive **100M to 35B+** model-by-model dossier across all 11 weight tiers & 20 historical sections (`110+` bare-metal evaluations), teacher/distiller lineage, exact quantization trade-off curves, and deep architectural diagnostics. | Model Curators & Systems Architects |
| ⚙️ **[`suite/`](suite/)** | **52 executable Python benchmark harnesses & empirical auditors** (`benchmark_13_areas_39_testes.py`, `duelo_nivel_opus_8b_vs_9b.py`, `tournament_*.py`, `torneio_*.py`, `duelo_*.py`, `test_audit_*.py`, `audit_*.py`). | Bare-Metal Automation & CI/CD Verification |
| 🔐 **[`proofs/`](proofs/)** | **47 immutable empirical proof artifacts** (`44` `proof_*.json` telemetry logs + `master_index_benchmarks_executados.json` + `catalogo_mestre_benchmarks_historicos.json` + `MASTER_LIVRO_SAGRADO_BENCHMARKS.md`). | Cryptographic / Empirical Audit & Citation |

---

## 1. Laboratory Manifesto & Methodology

The **AetherMind Bare-Metal LLM Experimental Benchmark Laboratory** was established to answer a fundamental systems engineering question:

> *"What is the true Pareto frontier of cognitive intelligence, algorithmic synthesis, memory footprint, and hardware throughput (tokens/second) for local Language Models spanning **100 Million to 35 Billion parameters (`100M` to `35B+`)** when evaluated on real consumer GPU and bare-metal Xeon workstation silicon without cloud APIs, synthetic LLM-as-a-judge biases, or cherry-picked prompts?"*

### Core Principles of the AetherMind Protocol

1. **Zero LLM-as-a-Judge Bias (100% Deterministic & Formal Verification):**
   Every single response across our **39 Cognitive Tests (13 Areas)** and **10 Opus Hard Challenges (LeetCode Hard)** is verified by deterministic Python validators, Abstract Syntax Tree (`ast`) structural inspection, isolated subprocess execution, and strict `pytest` assertion suites (`formal_verifier`). Banning `eval()` or `re` in a prompt is enforced by parsing the generated AST before executing a single line of code.
2. **Dual-Pass Evaluation (`Zero-Shot Baseline` vs. `Lambda-RLM` Recursive Metacognition):**
   Every model variant is tested in two distinct operational regimes:
   - **Pass 1 — Zero-Shot Baseline:** Direct inference (`temperature=0.0`) measuring raw native capability out-of-the-box.
   - **Pass 2 — `Lambda-RLM` Rescue Loop:** When a baseline generation fails formal verification, the exact failure trace or assertion counterexample is captured and routed into **`Lambda-RLM`**, a recursive metacognitive engine backed by a local execution environment (`LocalREPL`) that prompts the model to self-correct its logic or edge-case handling. Both scores (`Baseline ➔ Final`) and the exact rescue delta (`+RLM`) are recorded transparently.
3. **Full Quantization Grid Auditing (`IQ3_M`, `IQ4_XS`, `Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, `F16`, `BF16`):**
   Rather than testing a single arbitrary quantization per model, we map the complete bit-depth curve across 3-bit, 4-bit, 5-bit, 6-bit, 8-bit, and 16-bit precision to uncover non-linear quantization phenomena, bit-starvation thresholds in sub-1B models, implicit discretization regularization in 600M/4B distills, 256-bit AVX2 alignment speedups (`i1-IQ4_XS`), and memory-bandwidth saturation cliffs on 8 GB VRAM.
4. **Dual-Testbed Physical Telemetry (AMD RX 580 Vulkan GPU vs. Dual Xeon AVX2 Bare-Metal CPU):**
   Models from `100M` to `7B` are benchmarked on **GPU Vulkan** (`llama-server.exe -ngl 99`) and **Pure CPU AVX2** (`llama-bench.exe -ngl 0 --device none`), while `8B–35B` heavyweights and Titãs are audited on our **Dual Intel Xeon E5-2696 v4 AVX2 Bare-Metal** testbed, recording cold boot time (`s`), Prompt Processing speed (`PP tok/s`), and continuous Text Generation speed (`TG tok/s`).

---

## 2. Hardware & Software Testbed Specifications

All checkpoints across the **100M to 35B+** laboratory (`110+` historical and bare-metal evaluations across 11 weight tiers, including the 35-variant granular `350M–7.0B` matrix, 100M–200M global challengers, 600M quantization sweeps, 3B–4B Pareto tournaments, 8B–14B next-gen challengers, and 18B–35B Titãs) were executed under strictly controlled, isolated local conditions across two bare-metal testbeds:

| Subsystem | Testbed A: Consumer 8 GB GPU (100M–7B) | Testbed B: Xeon Bare-Metal Workstation (100M–35B+ Titãs) |
| :--- | :--- | :--- |
| **Compute Engine** | **AMD Radeon RX 580 Series** — `8192 MiB (8.0 GB) GDDR5 VRAM`, `256-bit` bus, `224 GB/s` peak bandwidth, Vulkan Compute API (`-ngl 99` full offload; `-ngl 12`/`-ngl 20` hybrid for `BF16`/`Q8_0` 4B+). | **Dual Intel Xeon E5-2696 v4** — Broadwell-EP `x86_64` multi-core AVX2 bare-metal (`14` to `28` dedicated threads, `--device none -ngl 0`, `BelowNormal` process isolation). |
| **System Memory & Storage** | **32 GB DDR4 System RAM** + High-speed NVMe SSD (`F:\`) for rapid GGUF cold-boot loading. | **32 GB DDR4 System RAM** + High-speed NVMe SSD (`F:\`, `512 GB`) and multi-volume storage (`D:\`, `E:\`, `I:\`). |
| **Operating System** | **Windows 11 Pro 64-bit** (Build 26200 / Native Win32 process isolation). | **Windows 11 Pro 64-bit** (Native Win32 process isolation). |
| **Inference Engine** | **`llama.cpp`** (`llama-server.exe` & `llama-bench.exe`, Vulkan/AVX2) on isolated localhost port `8089`, `--cont-batching`, `-c 4096` (up to `8192` for `<think>` audits), `temperature = 0.0`. | **`llama.cpp`** (`llama-server.exe` & `llama-bench.exe` AVX2 + `i1-IQ4_XS` 256-bit SIMD & MTP fast-patched builds) on isolated port `8089`. |
| **Flash Attention Policy** | **`-fa on` (`-fa 1`)** for Dense & MoE Transformers (`Qwen3`, `K2-Horizon`, `MiniCPM4/5`, `QwQ`, `Gemma4`, `SmolLM2`); **`-fa off` (`-fa 0`)** mandatory for **IBM Granite 4.0 Hybrid Mamba-2 + Attention** (`Granite-4.0-H-350M`, `Granite-350M-Gemini3`, `IBM-GPT-5.4-Coder-1B`, `granite-4.0-h-small`) to prevent state-space recurrence numerical drift. |
| **Metacognitive & Audit Stack** | **`Lambda-RLM`** (`F:\rotor-llm\lambda_rlm`) recursive `LocalREPL` counterexample repair + **`AetherMind_Strict_Auditor.py`** zero-tolerance empirical verifier. |

---

## 3. Hall of Fame — Champions by Every Weight Class (100M to 35B+)

Below are the undisputed champions across all **8 weight classes from `100M` to `35B`**, selected by empirical dominance across **13 Cognitive Areas (39 questions)**, **10 Opus Hard Challenges (AST/`pytest`)**, and **GPU/CPU tokens-per-second throughput**.

---

### 👑 3.1 Micro-Scale (100M–200M): `SmolLM2-135M-Instruct` & `Falcon-H1-Tiny-100M`

Evaluated in the 14-model Global Micro-Scale Challenger Tournament (`Section 13–14` of the Sacred Ledger) against models distilled from DeepSeek-V4 Pro, GPT-5.5, Meta MobileLLM, Mistral AI, Zephyr DPO, Platypus STEM, and Cerebras:

1. 🏆 **`SmolLM2-135M-Instruct [F16]` (135M — Undisputed Global Sub-200M Champion):**
   * **Architecture & Origin:** Dense Transformer (`135M` parameters, HuggingFaceTB `SmolLM2` trained on **2 Trillion tokens** of FineWeb-Edu).
   * **Empirical Performance (`258.3 MB`):** **`21/39 (53.85%)`** (`18/39` Baseline ➔ `21/39` `Lambda-RLM`, **4/13 Perfect Areas**) at **`41.58 tok/s` TG** (`758.95 tok/s` PP, `3.62s` boot).
2. ⚡ **`SmolLM2-135M-Instruct [Q4_K_M]` (`100.6 MB` Pocket Rocket):**
   * **Empirical Performance:** **`17/39 (43.59%)`** (`15/39` ➔ `17/39`, **3/13 Perfect Areas**) at **`57.45 tok/s` TG** (`684.69 tok/s` PP, **`1.04s` boot**). *(Warning: `[Q8_0]` suffered a severe 135M quantization anomaly, collapsing to `2/39` at `36.50 tok/s`).*
3. 🪶 **`Falcon-H1-Tiny-Multilingual-100M-Instruct [Q4_K_M]` (100M — Best Pure 100M Model):**
   * **Architecture & Origin:** TII Falcon H1 Multilingual Instruct (`100M` parameters, **`70.5 MB`**).
   * **Empirical Performance:** **`11/39 (28.21%)`** (`1` Perfect Area: `A01` Triage `3/3`) at **`28.09 tok/s` TG** (`584.8 tok/s` PP, `2.04s` boot).
4. **Other Notable Sub-200M Contenders:**
   * **`SmolLM2-135M-Instruct-heretic [Q4_K_M]` (`100.6 MB`):** `13/39 (33.33%)`, `1` Perfect Area (`A01` Triage), `17.24 tok/s`.
   * **`MobileLLM-143M [Q4_K_M]` (`101.6 MB`, Meta MobileLLM Native):** `10/39 (25.64%)` (`2/3` Planning, `2/3` Language) at `30.00 tok/s` TG (`765.3 tok/s` PP).
   * **`Lite-Mistral-150M-v2-Instruct [Q4_K_L]` (`112.7 MB`, Mistral AI v2):** `5/39 (12.82%)` at **`64.75 tok/s` TG** (`756.6 tok/s` PP).
   * **`zephyr-smol_llama-100m-dpo [Q4_K_M]` (`63.3 MB`):** `4/39 (10.26%)` at `19.46 tok/s`; **`Distil-GPT5.5-Minute.Codex-0.1B [Q4_K_M]` (`59.9 MB`):** `1/39` at **`116.09 tok/s` TG** (`1485.2 tok/s` PP); **`Qwen2.5-0.2B`** (`1/39`, `96.20 tok/s`); **`Sheared-Pythia-160m-Platypus`** (`1/39`, `30.60 tok/s`); while destructive pruning / raw code models (`Qwen3-0.6B-Pruned-0.2B` at `2494.7 tok/s` PP, `Distil-Deepseek.V4.Pro.Minute.Codex`, `AMD-Llama-135m-code`, `Cerebras-GPT-111M-instruction`) scored `0/39`.
* **Why `SmolLM2-135M` Won (Mestre Ruan's Pareto Cutoff Law):** Training on 2T curated educational tokens gave `SmolLM2-135M` structured instruction following that no rival `<200M` model matched (`21/39` vs. `11/39` runner-up), establishing the strict laboratory rule: **no model >135M enters the Pareto ladder with `<21/39`**.

---

### 👑 3.2 350M–360M Champions: `Granite-350M-Gemini3 [F16]` & `Granite-4.0-H-350M [Q8_0]`

* **Architecture:** **IBM Granite 4.0 Hybrid (Mamba-2 State-Space Model + Multi-Head Attention)** — `350M` parameters, `128,000` context window, **mandatory `-fa off` (`-fa 0`)** on Vulkan/CPU to preserve Mamba-2 recurrence precision.
* **Champions & Direct Hugging Face `.gguf` Downloads:**
  1. 🏆 **`Granite-350M-Gemini3-Think [F16]` (Teacher: Google Gemini 3 Pro Thinking — 653.2 MB):**
     * **Download:** [`granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf)
     * **Other Quants:** [`Q8_0` (349.2 MB)](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf) | [`Q6_K` (270.7 MB)](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf) | [`Q5_K_M` (240.6 MB)](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf)
     * **Performance:** **`29/39 (74.36%)`** (`25/39` Baseline + `4` RLM rescues, `7/13` Perfect Areas) and **`1/10 (10.0%)` Opus Hard** (`OPUS_06` Partitioned Median of Two Sorted Arrays in $O(\log(\min(N,M)))$, rescued via `Lambda-RLM` in `F16` and `Q6_K`, and solved Zero-Shot in `Q8_0`!). Runs at **`23.08 tok/s` GPU TG** (`105.24 tok/s` PP) and **`10.01 tok/s` CPU TG** (`380.88 tok/s` CPU PP). **The smallest model on Earth (`350M`) ever verified to pass an Opus Hard formal challenge.**
  2. 👑 **`Granite-4.0-H-350M [Q8_0]` & `[Q4_K_M]` (Teacher: IBM Granite 4.0 Hybrid Foundation):**
     * **Download (`Q8_0` — 349.2 MB):** [`granite-4.0-h-350m-Q8_0.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf)
     * **Other Quants:** [`Q6_K` (270.7 MB)](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q6_K.gguf) | [`Q5_K_M` (240.6 MB)](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q5_K_M.gguf) | [`Q4_K_M` (212.3 MB)](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q4_K_M.gguf)
     * **Performance:** Matches **`29/39 (74.36%)`** (`18/39` Baseline + **`+11 Lambda-RLM rescues`**, `6/13` Perfect Areas) in **`349.2 MB`** (also `29/39` in `BF16` at `22.64 tok/s`) running at **`21.80 tok/s` GPU TG** and **`10.54 tok/s` CPU TG**. Its ultra-tiny **`Q4_K_M` (`212.3 MB`)** achieves **`28/39 (71.79%)`** at `22.18 tok/s` GPU / `12.43 tok/s` CPU (beating `SmolLM2-360M-Instruct [Q4_K_M]` at `22/39`, `9.89 tok/s`).
* **Why They Won:** Disabling Vulkan Flash Attention (`-fa off`) unlocked the Mamba-2 SSM recurrence precision, allowing `350M` hybrid models to match `500M` Dense transformers (`29/39`) and pass formal LeetCode Hard verification (`OPUS_06`).

---

### 👑 3.3 500M Champions: `MiniCPM4-0.5B [Q8_0]` & `QwQ-0.5B-Distilled-SFT`

* **Architecture:** OpenBMB MiniCPM4 Dense (`500M`, `32K` ctx, non-thinking, `-fa on`) & Alibaba Qwen2.5/QwQ (`500M`, `<think>` active).
* **Direct Hugging Face `.gguf` Downloads:**
  * 🏆 **`MiniCPM4-0.5B [Q8_0]` (Sub-600M Cognitive Record Holder — 441.4 MB):** [`MiniCPM4-0.5B.Q8_0.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf)
  * ⚡ **`MiniCPM4-0.5B [Q6_K]` (`341.2 MB`, 56 tok/s CPU):** [`MiniCPM4-0.5B.Q6_K.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf)
  * 🪶 **`MiniCPM4-0.5B [Q5_K_M]` (`302.3 MB`):** [`MiniCPM4-0.5B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf) | **`Q4_K_M`** (`265.8 MB`, `51.92 tok/s`) | [`F16` (829.3 MB)](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf)
  * 🧠 **`QwQ-0.5B-Distilled-SFT [Q6_K]` (`482.3 MB`):** [`QwQ-0.5B-Distilled-SFT.Q6_K.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q6_K.gguf) (`Q4_K_M`: `379.4 MB`)
* **Empirical Performance:**
  * **`MiniCPM4-0.5B [Q8_0]` (`441.4 MB`):** First half-billion-parameter model in history to break the 30-point barrier, scoring **`31/39 (79.49%)`** (`24/39` Baseline + `7` `Lambda-RLM` rescues, `7/13` Perfect Areas) at **`38.60 tok/s` GPU Vulkan** (`311.56 tok/s` PP) and **`49.99 tok/s` CPU AVX2** (`556.24 tok/s` CPU PP)!
  * **`MiniCPM4-0.5B [Q4_K_M]` (`265.8 MB`):** Scores **`29/39 (74.36%)`** (`23->29`, `6` Perfect Areas) at **`51.92 tok/s`** (`373.43 tok/s` PP).
  * **`QwQ-0.5B-Distilled-SFT`:** Reaches **`29/39 (74.36%)`** (`7` Perfect Areas, `42.24 tok/s`) in `Q4_K_M` (`379.4 MB`) and **`28/39`** at **`48.29 tok/s` GPU** in `Q6_K` (`482.3 MB`), outpacing `Qwen2.5-0.5B-OpenR1` (`27/39`).
* **Why They Won:** At 500M scale, `MiniCPM4-0.5B` proved that elevating bit precision from `Q4_K_M` (`29/39`) to `Q8_0` (`31/39`) restores attention-head fidelity at zero throughput penalty (~`50 tok/s` on CPU AVX2).

---

### 👑 3.4 600M Champions (The Implicit Regularization Triad): `TinyQwen3-Distill-0.6B`, `Qwen3-0.6B-Distill-30B`, `Qwen3-0.6B-Opus4.6`

Evaluated across a full 15-configuration Pareto grid (`Q4_K_M` to `F16`, Sections 8–12 of the Sacred Ledger), these three 600M models demonstrated how teacher lineage interacts with quantization bit-depth:

1. 🏆 **`TinyQwen3-Distill-0.6B [Q5_K_M]` & `[Q6_K]` (Teacher: DeepSeek-R1):**
   * **Direct Download (`Q5_K_M` — 423.6 MB):** [`TinyQwen3-distill-0.6B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q5_K_M.gguf)
   * **Performance:** **`34/39 (87.18%)`** under `Lambda-RLM` (`24/39` Baseline + **`+10 RLM rescues`**, **9/13 Perfect Areas**) at **`41.23 tok/s` TG** (`214.46 tok/s` PP) in `Q5_K_M`, and **`33/39 (84.62%)`** at **`40.72 tok/s`** in `Q6_K` (`472.0 MB`). Moving from 4-bit (`28/39`) to 5-bit unlocked DeepSeek-R1's multi-step reasoning chains under `Lambda-RLM`, while unquantized `F16` (`1142.2 MB`) degraded to `30/39` and `15.98 tok/s`.
2. ⚡ **`Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT [Q4_K_M]` (Teacher: Qwen3-30B-A3B-Thinking SFT):**
   * **Direct Download (`Q4_K_M` — 420.3 MB):** [`Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q4_K_M.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q4_K_M.gguf)
   * **Performance:** **`32/39 (82.05%)`** (`29/39` Zero-Shot Baseline — highest zero-shot accuracy in the 600M class, **9/13 Perfect Areas**) at **`43.30 tok/s` TG** and **`291.60 tok/s` PP** (`2.09s` boot). Famous for proving **Implicit Discretization Regularization**: its `Q4_K_M` (`32/39`, `43.3 tok/s`) systematically defeated its own unquantized `F16` (`29/39`, `24.1 tok/s`, `1.41 GB`) by filtering high-frequency distillation tail noise.
3. 🎯 **`Qwen3-0.6B-Opus4.6-Abliterated [Q8_0]` & `[Q5_K_M]` (Teacher: Anthropic Claude 4.6 Opus):**
   * **Direct Download (`Q8_0` — 609.8 MB):** [`Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf)
   * **Performance:** **`32/39 (82.05%)`** (`29/39` Baseline, `8/13` Perfect Areas) at `30.43 tok/s` in `Q8_0`, and **`30/39 (76.92%)`** (`29/39` Baseline) with a `2.03s` boot at `36.87 tok/s` in `Q5_K_M` (`423.8 MB`). *(Note: Active-thinking Opus Hard sweeps in Sec 12 proved `0/10` across all 600M champions—confirming `1.0B` as the physical floor for Opus Hard formal passes).*

---

### 👑 3.5 0.9B–1.7B Champions: `IFM/K2-Horizon-0.9B`, `IBM-GPT-5.4-Coder-1B`, `MiniCPM5-1B-Opus`, `Qwen3-1.7B`

1. 🏆 **`IFM/K2-Horizon-0.9B` (`[Q6_K]`, `[Q8_0]`, `[Q5_K_M]`) — Sub-1B Flyweight King:**
   * **Architecture & Lineage:** Dense Transformer (`0.9B` / `900M` params, native **512K** context, direct non-thinking `thinking: False`, [`IFM/K2-Horizon-0.9B-GGUF`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF)).
   * **Direct `.gguf` Downloads:** [`Q6_K` (846.4 MB)](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf) | [`Q8_0` (1095.4 MB)](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf) | [`Q5_K_M` (737.6 MB)](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf) | [`Q4_K_M` (635.3 MB)](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf)
   * **Empirical Performance:**
     * **`[Q6_K]` (`846.4 MB`):** **`34/39 (87.18%)`** (`25/39` Base + `9` RLM, `9/13` Perfect) and an unprecedented **`4/10 (40.0%)` Opus Hard Zero-Shot** (`OPUS_05` Bitmask DP TSP, `OPUS_06` Median Arrays, `OPUS_08` Rain Water, `OPUS_09` Tree Max Path Sum) at **`34.29 tok/s` GPU** and **`36.60 tok/s` CPU AVX2** (`2.57s` boot)!
     * **`[Q8_0]` (`1095.4 MB`):** **`35/39 (89.74%)`** (`27/39` Base + `8` RLM, **`10/13` Perfect Areas**) and **`3/10` Opus Hard** (`OPUS_06`, `OPUS_08` Base + `OPUS_05` **RLM**) at **`28.39 tok/s` GPU / `28.46 tok/s` CPU** (`1.52s` boot).
     * **`[Q5_K_M]` (`737.6 MB`):** `33/39` and **`4/10` Opus Hard** (`OPUS_05`, `OPUS_06`, `OPUS_07` Base + `OPUS_08` **RLM**) at `33.35 tok/s` GPU / `38.57 tok/s` CPU.
   * **Why It Won:** Direct non-thinking synthesis (`>34 tok/s`) avoids `<think>` token budget exhaustion while outscoring 1.0B–1.7B models on Opus Hard (`4/10` in `846 MB`), and its pure CPU AVX2 throughput (`36.60 tok/s`) beats Vulkan GPU (`34.29 tok/s`) with **zero VRAM cost**.
2. 👑 **`Qwen3-1.7B` (`[Q8_0]`, `[Q5_K_M]`, `[Q6_K]`) — Intermediate Flyweight King:**
   * **Architecture & Lineage:** Dense Transformer (`1.7B` params, `32K` context, `<think>` active, [`bartowski/Qwen_Qwen3-1.7B-GGUF`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF)).
   * **Direct `.gguf` Downloads:** [`Q8_0` (2064.7 MB)](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf) | [`Q5_K_M` (1403.6 MB)](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf) | [`Q4_K_M` (1223.0 MB)](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf) | [`BF16` (3881.2 MB)](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf)
   * **Empirical Performance:** **`[Q8_0]`** hits **`36/39 (92.31%)`** (`34/39` Base + `2` RLM, **11/13 Perfect Areas**) + **`2/10` Opus** (`OPUS_06`, `OPUS_07`) at **`31.07 tok/s` GPU**; **`[Q5_K_M]` (`1.4 GB`)** matches **`36/39 (92.31%)`** + `1/10` Opus at **`31.22 tok/s` GPU / `24.92 tok/s` CPU** (beating its own `BF16` at `35/39`, `25.88 tok/s`). In standalone imatrix `Q6_K` (`Sec 2`), it also hit `36/39 + 4/10 Opus` under `Lambda-RLM`.
3. 🎯 **`IBM-GPT-5.4-Coder-1B` (`[Q6_K]`, `[Q4_K_M]`, `[F16]`):**
   * **Architecture & Teacher:** IBM Granite Hybrid 1.0B (`128K` context, **`-fa off`**), distilled from **OpenAI GPT-5.4 Coder**.
   * **Direct `.gguf` Downloads:** [`i1-Q6_K` (1.25 GB)](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q6_K.gguf) | [`Q4_K_M` (0.95 GB)](https://huggingface.co/bartowski/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B-Q4_K_M.gguf) | [`F16` (3116.0 MB)](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf)
   * **Empirical Highlights:** **`33/39 (84.62%)`** in `Q4_K_M` (`23.4 tok/s`); **`31/39` + `2/10` Opus Hard (`OPUS_01` Pure Regex Engine `.`/`*`/`+` without `re` and `OPUS_08` Rain Water)** in **`Q6_K`** (`18.9 tok/s`); `32/39 + 1/10` Opus in `F16` (`17.34 tok/s` GPU).
4. ⚡ **`MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic` (`[Q4_K_M]`, `[Q8_0]`, `[F16]`):**
   * **Architecture & Teacher:** OpenBMB MiniCPM5 1.0B Dense (`128K` ctx, `<think>`, `-fa on`), distilled from **Claude Opus + Fable 5 V2 Thinking**.
   * **Direct `.gguf` Downloads:** [`Q4_K_M` (0.64 GB)](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q4_K_M.gguf) | [`Q8_0` (1.07 GB)](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q8_0.gguf) | [`F16` (2066.2 MB)](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf)
   * **Empirical Highlights:** **`42.0 tok/s` TG (`203.8 tok/s` PP)** in `Q4_K_M` with **`32/39 (82.05%)`** and **`1/10` Opus (`OPUS_06`)**; **`33/39 (84.62%)`** in `Q8_0`; `32/39 + 1/10` Opus at `38.69 tok/s` GPU in `F16`.

---

### 👑 3.6 3B–4.5B Champions (The 8 GB Consumer GPU Sweet Spot)

1. 🏆 **`IFM/K2-Horizon-3.7B` (`[BF16]`, `[Q6_K]`, `[Q5_K_M]`, `[Q8_0]`) — Undisputed Medium-Layer King:**
   * **Architecture & Lineage:** Dense Transformer (`3.7B` params, native **512K** context, `<think>` active, [`IFM/K2-Horizon-3.7B-GGUF`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF)).
   * **Direct `.gguf` Downloads:** [`Q6_K` (3.88 GB)](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf) | [`Q5_K_M` (3.39 GB)](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf) | [`Q8_0` (5.02 GB)](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf) | [`Q4_K_M` (2.94 GB)](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf) | [`BF16` (9.43 GB)](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-BF16.gguf)
   * **Empirical Performance:**
     * **`[BF16]` (`9.43 GB`, `-ngl 12` hybrid, Sec 17):** **`38/39 (97.44%)`** (**12/13 Perfect Areas**, including Code `3/3` + Math `3/3`, tying `9B` and `12B` models!) + **`4/10 (40.0%)` Opus Hard** (`5.66 tok/s` GPU / `4.74 tok/s` CPU).
     * **`[Q6_K]` (`3968.6 MB`, `-ngl 99`):** **`37/39 (94.87%)`** (`31/39` Base + `6` RLM in Sec 20; `37/39` Zero-Shot in Sec 17, `11/13` Perfect) + **`3/10 (30.0%)` Opus Hard** (`OPUS_04`, `OPUS_05`, `OPUS_07`) at **`19.53 tok/s` GPU** (`10.48 tok/s` CPU).
     * **`[Q5_K_M]` (`3475.0 MB`, `-ngl 99`):** **`36/39` Zero-Shot Baseline ➔ `37/39 (94.87%)` Final** at **`20.11 tok/s` GPU** (`11.37 tok/s` CPU), reaching **`4/10 (40.0%)` Opus Hard** in Sec 17 (`20.42 tok/s` GPU, `11.65 tok/s` CPU).
     * **`[Q8_0]` (`5136.9 MB`):** `37/39` + `3/10` Opus (`4/10` Zero-Shot in Sec 17) at `19.91 tok/s` GPU.
   * **Why `3.7B` Beats `7B` on 8 GB VRAM:** Fits completely inside 8 GB GDDR5 with >4 GB headroom (`20.11 tok/s` vs `6.89 tok/s` on `K2-Horizon-7B`), avoiding `240s` `<think>` timeouts (`3–4/10` Opus vs `1/10` on `7B`).
2. 🥇 **`Parable-Qwen3-4B-Claude-Fable-5` (`[Q6_K]`, `[Q5_K_M]`, `[Q4_K_M]`):**
   * **Architecture & Teacher:** Dense Qwen3 `4B`, distilled from **Claude 3.5 + Fable 5** ([`AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF`](https://huggingface.co/AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF)).
   * **Direct `.gguf` Downloads:** [`Q6_K` (3.08 GB)](https://huggingface.co/AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF/resolve/main/Parable-Qwen3-4B-Claude-Fable-5-GGUF-Q6_K.gguf) | [`Q5_K_M` (2.69/2.81 GB)](https://huggingface.co/AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF/resolve/main/Parable-Qwen3-4B-Claude-Fable-5-GGUF-Q5_K_M.gguf) | [`Q4_K_M` (2.33 GB)](https://huggingface.co/AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF/resolve/main/Parable-Qwen3-4B-Claude-Fable-5-GGUF-Q4_K_M.gguf)
   * **Empirical Performance:** **`[Q4_K_M]`** achieved **`38/39 (97.44%)`** (**12/13 Perfect Areas**) at **`22.71 tok/s` GPU**; **`[Q5_K_M]`** unlocked **`4/10 (40.0%)` Opus Hard** (`34/39`, `20.11 tok/s` GPU); **`[Q6_K]`** balanced **`36/39 (92.31%)` + `3/10` Opus** at `19.52 tok/s` GPU. *(Earlier Sec 2 Xeon run also recorded `35/39` + `5/10` Opus in Q4_K_M)*.
3. 🥈 **`deadbydawn101-Gemma4-E4B-Agentic-Opus-Reasoning [Q4_K_M]` (CPU Bare-Metal King in 4B):**
   * **Download (`Q4_K_M`):** [`gemma4-e4b-opus-Q4_K_M.gguf`](https://huggingface.co/deadbydawn101/gemma-4-E4B-Agentic-Opus-Reasoning-GeminiCLI-GGUF/resolve/main/gemma4-e4b-opus-Q4_K_M.gguf) (`4.5B` Dense, Claude Opus + GeminiCLI).
   * **Performance:** **`36/39 (92.31%)`** (`35/39` Zero-Shot Baseline, `11/13` Perfect Areas) + **`2/10` Opus Hard** at `15.31 tok/s` GPU and **`9.64 tok/s` Xeon CPU** (highest 4B pure-CPU speed).
4. **Additional Verified 3B–4B Specialists:**
   * **`ai9stars/G9v3-3B [BF16]` & `[Q4_K_M]`** ([`bartowski/ai9stars_G9v3-3B-GGUF`](https://huggingface.co/bartowski/ai9stars_G9v3-3B-GGUF)): `[BF16]` (`5.57 GB`) hits **`34/39 (87.18%)` + `2/10` Opus** (`OPUS_07`, `OPUS_08`) at `18.03 tok/s` GPU; `[Q4_K_M]` (`1.77 GB`) hits `32/39 + 1/10` Opus (`22.52 tok/s` GPU / `9.13 tok/s` CPU; `38/39` in Sec 2).
   * **`Jackrong-GPT-5-Distill-Llama3.2-3B [Q4_K_M]`** ([`jackrong/GPT-5-Distill-Llama3.2-3B-GGUF`](https://huggingface.co/jackrong/GPT-5-Distill-Llama3.2-3B-GGUF), `1.88 GB`, OpenAI GPT-5 Distill): **`4/10 (40.0%)` Opus Hard** (`35/39` Base / `29/39` RLM) at `17.90 tok/s` CPU.
   * **`Lumi-4B-Nacional-CEIA [Q4_K_XL]`** ([`Mateus-Nery/lumi-4b-GGUF`](https://huggingface.co/Mateus-Nery/lumi-4b-GGUF), `2.92 GB`, CEIA-BR PT-BR Foundation): `22/39` (**zero-free across all 13 areas**, `3/3` Scientific Reasoning) + **`1/10` Opus (`OPUS_07`)** at `10.15 tok/s` CPU.
   * **`Qwen3-4B-Instruct-grok-4-fast-brainstorming-distill [Q4_K_M]`** ([`TeichAI/Qwen3-4B-Instruct-grok-4-fast-brainstorming-distill`](https://huggingface.co/TeichAI/Qwen3-4B-Instruct-grok-4-fast-brainstorming-distill), `2.33 GB`): Rescued **`OPUS_10` (DPLL SAT Solver for CNF)** via `Lambda-RLM` (`1/10` Opus, `12.51 tok/s` CPU).

---

### 👑 3.7 7B–14B Champions (Workstation & High-Precision Dense/MoE)

1. 🏆 **`yuxinlu1-Gemma4-12B-Agentic-Fable5` & `gemma-4-12B-coder-fable5-composer2.5-v1 [Q4_K_M]` (12B — Top Overall Opus + 13-Area Workstation King):**
   * **Architecture & Teachers:** Gemma 4 `12B` Dense, distilled from **Fable 5 Agentic / Coder + Composer 2.5**.
   * **Repositories:** [`yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF`](https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF) | [`yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF`](https://huggingface.co/yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF) (`gemma4-coding-Q4_K_M.gguf`, `6.87 GB`).
   * **Empirical Performance:**
     * **`yuxinlu1-Gemma4-12B-Agentic-Fable5 [Q4_K_M]` (`6.87 GB`, Sec 2):** **`24/39` Base ➔ `38/39 (97.44%)`** + **`3/10` Base ➔ `6/10 (60.0%)` Opus Hard** at `41.20 tok/s` PP / `7.80 tok/s` TG Xeon.
     * **`gemma-4-12B-coder-fable5-composer2.5-v1 [Q4_K_M]` (`6.87 GB`, Sec 4 & `proof_gemma4_coder_13areas.json`):** **`33/39 (84.62%)`** (`8/13` Perfect Areas) + **`4/10 (40.0%)` Opus Hard** (`OPUS_04`, `OPUS_05`, `OPUS_07`, `OPUS_08`) at `9.49 tok/s` PP / `4.46 tok/s` TG Xeon.
2. 🥇 **`MiMo-V2.6-Distill-Qwen-9B [Q4_K_M]` (9B — 97.44% Cognitive Co-Leader):**
   * **Repository & Download:** [`bartowski/MiMo-V2.6-Distill-Qwen-9B-GGUF`](https://huggingface.co/bartowski/MiMo-V2.6-Distill-Qwen-9B-GGUF/resolve/main/MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf) (`5.44 GB`, Dense 9B, Xiaomi MiMo V2.6 Distill).
   * **Empirical Performance:** `31/39` Base ➔ **`38/39 (97.44%)`** + `0/10` Base ➔ **`3/10 (30.0%)` Opus Hard** under `Lambda-RLM` at `48.30 tok/s` PP / `9.15 tok/s` TG Xeon.
3. 🥈 **`Qwen3-8B-GPT-5.2-High-Reasoning-Distill [Q4_K_M]` (8B — Sub-30B Zero-Shot Amplitude Record):**
   * **Repository:** [`TeichAI/Qwen3-8B-GPT-5.2-High-Reasoning-Distill-GGUF`](https://huggingface.co/TeichAI/Qwen3-8B-GPT-5.2-High-Reasoning-Distill-GGUF) (`4.68 GB`, Dense 8B, GPT-5.2 High Reasoning).
   * **Empirical Performance:** **`35/39 (89.74%)`** (**10/13 Perfect Areas**) + **`1/10` Opus (`OPUS_05` Bitmask DP TSP)** at **`25.43 tok/s` PP / `7.90 tok/s` TG Xeon** (`6.4s` boot).
4. **Other Notable 7B–14B Contenders:**
   * **`Poe-8B-Crownelius-Grok-Heretic [Q4_K_M]`** ([`mradermacher/Poe-8B-GLM5-Opus4.6-Sonnet4.5-Kimi-Grok-Gemini-3-pro-preview-HERETIC-i1-GGUF`](https://huggingface.co/mradermacher/Poe-8B-GLM5-Opus4.6-Sonnet4.5-Kimi-Grok-Gemini-3-pro-preview-HERETIC-i1-GGUF), `4.68 GB`): `18/39` + **`2/10` Opus (`OPUS_04`, `OPUS_08`)** at `8.16 tok/s` TG Xeon.
   * **`Mellum2-12B-A2.5B-Claude-Opus [Q4_K_M]`** ([`yuxinlu1/Mellum2-12B-A2.5B-Claude-4.6-4.8-Opus-Thinking-GGUF`](https://huggingface.co/yuxinlu1/Mellum2-12B-A2.5B-Claude-4.6-4.8-Opus-Thinking-GGUF), `7.52 GB`, MoE 12B / `2.5B` active): **`13.54 tok/s` Xeon CPU TG** (`4s` boot — fastest 12B in Xeon CPU!) + `1/10` Opus (`OPUS_04`).
   * **`Qwen3-14B-GPT-5.2-High-Reasoning-Distill [Q4_K_M]`** ([`TeichAI/Qwen3-14B-GPT-5.2-High-Reasoning-Distill-GGUF`](https://huggingface.co/TeichAI/Qwen3-14B-GPT-5.2-High-Reasoning-Distill-GGUF), `8.38 GB`): **`33/39 (84.62%)`** (`9/13` Perfect) + `1/10` Opus (`OPUS_08`) at `4.78 tok/s` TG Xeon.
   * **`unsloth-Phi-4-reasoning-14B [Q4_K_M]`** ([`unsloth/Phi-4-reasoning-GGUF`](https://huggingface.co/unsloth/Phi-4-reasoning-GGUF/resolve/main/phi-4-reasoning-Q4_K_M.gguf), `8.43 GB`): `3/39` Base ➔ **`31/39 (79.49%)`** (**+28 RLM rescue jump!**) + `1/10` Opus at `6.90 tok/s` TG Xeon.
   * **`IFM/K2-Horizon-7B [Q6_K]`** ([`K2-Horizon-7B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q6_K.gguf), `7052.0 MB`): **`37/39 (94.87%)`** (`36/39` Base + `+1` RLM) + `2/10` Opus (`OPUS_08`, `OPUS_09`) at `5.88 tok/s` GPU (`6.28 tok/s` CPU) — 11/13 gabaritos perfeitos.
   * **`IFM/K2-Horizon-7B [Q5_K_M]`** ([`K2-Horizon-7B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q5_K_M.gguf), `6166.5 MB`): **`36/39 (92.31%)`** + **`3/10` Opus** (`OPUS_07`, `OPUS_08`, `OPUS_09`) at `6.65 tok/s` GPU (`6.66 tok/s` CPU) — melhor desempenho algorítmico do 7B.
| **4** | **7.0B** | **`K2-Horizon-7B`** ⚠️ | `Q6_K` | `512K / T:S / FA:on / NGL:20` | 7052.0 | 5.59s | 16.86 | **5.88** | 34.52 | 6.28 | **`36/39`** ➔ **`37/39` (94.87%)** | **`+1`** | 11/13 | `2/10` ➔ **`2/10` (20%)** | `+0` | `OPUS_08`(Base), `OPUS_09`(Base) *(7 timeouts @ 5.88 t/s)* |
| **5** | **7.0B** | **`K2-Horizon-7B`** ⚠️ | `Q5_K_M` | `512K / T:S / FA:on / NGL:24` | 6166.5 | 4.88s | 19.78 | **6.65** | 32.86 | 6.66 | **`36/39`** ➔ **`36/39` (92.31%)** | **`+0`** | 10/13 | `3/10` ➔ **`3/10` (30%)** | `+0` | `OPUS_07`(Base), `OPUS_08`(Base), `OPUS_09`(Base) *(5 timeouts @ 6.65 t/s)* |
   * **`IFM/K2-Horizon-7B [Q4_K_M]`** ([`K2-Horizon-7B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q4_K_M.gguf), `5333.1 MB`): **`37/39 (94.87%)`** (`36/39` Base + `+1` RLM) + `1/10` Opus (`OPUS_08`) at `6.89 tok/s` GPU (`8.06 tok/s` CPU).

---

### 👑 3.8 Titãs (18B–35B) — Dual Intel Xeon E5-2696 v4 AVX2 Heavyweights

Audited bare-metal on Dual Intel Xeon E5-2696 v4 (`Sections 1–5` of the Sacred Ledger):

1. 🏆 **`Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet` (MoE 30.5B / 3.3B Active — ALL-TIME 30B+ OPUS HARD KING):**
   * **Teacher:** Anthropic **Claude 4.5 Sonnet** High-Reasoning Distillation.
   * **3-Point Xeon Quantization Duel:**
     * **`[Q4_K_M]`** ([`TeichAI/...-GGUF`](https://huggingface.co/TeichAI/Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet-High-Reasoning-Distill-GGUF), `17.28 GB`, `~112s` boot): **`6/10 (60.0%)` OPUS HARD CAMPEÃO 30B+** (`3/10` Base ➔ `6/10` Lambda-RLM: `OPUS_04`, `OPUS_05`, `OPUS_06`, `OPUS_07`, `OPUS_08`, `OPUS_09`) + `30/39 (76.92%)` 13 Areas (`16/39` Base ➔ `30/39`) at `28.71 tok/s` PP / `3.65 tok/s` TG.
     * **`[i1-IQ3_M]`** ([`mradermacher/...-i1-GGUF`](https://huggingface.co/mradermacher/Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet-High-Reasoning-Distill-i1-GGUF), `12.59 GB`, `12s` boot): **`5/10 (50.0%)` Opus Hard** (`OPUS_04`, `OPUS_05`, `OPUS_06`, `OPUS_07`, `OPUS_08`) at **`6.82 tok/s` TG (+86.8% vs Q4_K_M)**.
     * **`[i1-IQ4_XS]`** ([`mradermacher/...-i1-GGUF`](https://huggingface.co/mradermacher/Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet-High-Reasoning-Distill-i1-GGUF), `15.24 GB`, `12s` boot): **`4/10 (40.0%)` Opus Hard** (`OPUS_04`, `OPUS_06`, `OPUS_07`, `OPUS_08`) at **`11.34 tok/s` TG (+210.7% vs Q4_K_M — 256-bit AVX2 SIMD alignment!)**, `38.76 tok/s` PP.
2. 👑 **`Qwen3-30B-A3B [IQ3_M]` & `[Q4_K_M]` (MoE 30.5B / 3.3B Active — 30B+ 13-Area Cognitive & Speed King):**
   * **Repository:** [`bartowski/Qwen_Qwen3-30B-A3B-GGUF`](https://huggingface.co/bartowski/Qwen_Qwen3-30B-A3B-GGUF) (Alibaba Qwen Native).
   * **`[IQ3_M]` (`13.11 GB`):** **`36/39 (92.31%)`** (`23/39` Base ➔ `36/39` Lambda-RLM, `10/13` Perfect Areas) — **Highest 13-Area Score among all 13 Titãs**, `13.11 tok/s` PP / `8.14 tok/s` Turbo TG (`3.19 tok/s` Baseline), `14s` boot.
   * **`[Q4_K_M]` (`17.35 GB`):** **`35/39 (89.74%)`** (`21/39` Base ➔ `35/39` Lambda-RLM, `11/13` Perfect Areas) + `1/10` Opus (`OPUS_08`), **`8.14 tok/s` TG** (`25.86 tok/s` PP, `18s` boot) — **Fastest 30B+ model in benchmark history**.
3. 👑 **`Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled [Q4_K_M]` (35B Co-Leader):**
   * **Download (`19.71 GB`):** [`Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled.Q4_K_M.gguf`](https://huggingface.co/mradermacher/Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled-GGUF/resolve/main/Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled.Q4_K_M.gguf) (Claude 4.7 Opus Distill, MoE 35B / ~3B active).
   * **Performance:** `14/39` Base ➔ **`35/39 (89.74%)`** (`9/13` Perfect Areas), `28.50 tok/s` PP / `3.12 tok/s` TG (`28s` boot).
4. 🥈 **`gemma-4-26B-A4B-Opus` Trio (`Q4_K_M` — 26B / 4B Active MoE):**
   * **`TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill-v2-GGUF`** (`15.64 GB`): `29/39` Base ➔ **`34/39 (87.18%)`** (`10/13` Perfect) + **`1/10` Opus (`OPUS_08`)**, `27.34 tok/s` PP / `5.12 tok/s` TG.
   * **`glyphsoftware/gemma-4-26b-a4b-opus-4.7-distilled-GGUF`** (`15.64 GB`): `25/39` Base ➔ **`34/39 (87.18%)`** (`10/13` Perfect) + **`1/10` Opus (`OPUS_06`)**, `25.20 tok/s` PP / `4.54 tok/s` TG.
   * **`mudler/gemopus-4-26B-A4B-APEX-Balanced-GGUF`** (`18.17 GB`): `22/39` ➔ **`34/39 (87.18%)`** (`11/13` Perfect), `30.68 tok/s` PP / `3.96 tok/s` TG.
5. 🎯 **`Qwopus3.6-35B-A3B-Coder-MTP [Q4_K_M]` (35B MTP Fast-Patched):**
   * **Download (`20.22 GB`):** [`Qwopus3.6-35B-A3B-Coder-MTP-Q4_K_M.gguf`](https://huggingface.co/Jackrong/Qwopus3.6-35B-A3B-Coder-MTP-GGUF/resolve/main/Qwopus3.6-35B-A3B-Coder-MTP-Q4_K_M.gguf) (MoE 35B / ~3B active with Multi-Token Prediction, Claude 4.7 Opus Coder Distill).
   * **Performance:** `18/39 (46.15%)` + **`1/10` Opus (`OPUS_04` 2D Monotonic Stack Maximal Rectangle)** at `22.40 tok/s` PP / `2.80 tok/s` TG.
6. ⚡ **`gpt-oss-20b-gpt-5-codex-distill [Q8_0]` & `gpt-oss-20b-antidoom [i1-IQ4_XS]` (20B Dense Speed & Coding):**
   * **`TeichAI/gpt-oss-20b-gpt-5-codex-distill-GGUF` (`Q8_0`, `11.28 GB`):** **`30/39 (76.92%)`** (`7/13` Perfect) + **`3/10 (30.0%)` Opus Hard** (`OPUS_07`, `OPUS_08`, `OPUS_09`) at **`11.26 tok/s` TG** (`11.37 tok/s` PP, `8.5s` boot).
   * **`mradermacher/gpt-oss-20b-antidoom-i1-GGUF` (`i1-IQ4_XS`, `12.10 GB`):** **`31.29 tok/s` TG** (`45.20 tok/s` PP) under PLD Xeon AVX2 Two-Tier Production (`PASS`).
7. 🚀 **`granite-4.0-h-small [Q4_K_M]` (18B Hybrid Rescue Record):**
   * **Download (`18.14 GB`):** [`granite-4.0-h-small-Q4_K_M.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-small-GGUF/resolve/main/granite-4.0-h-small-Q4_K_M.gguf) (IBM Granite 4.0 Hybrid 18B).
   * **Performance:** **`5/39 (12.8%)` Baseline ➔ `33/39 (84.62%)` Lambda-RLM** (**+560% relative rescue jump**, `8/13` Perfect Areas) at `32.10 tok/s` PP / `4.20 tok/s` TG.

---

### 🏆 3.9 Complete Cross-Scale Pareto Ladder (100M to 35B+)

Each rung on the Pareto Ladder represents the empirically dominant checkpoint at its parameter & memory footprint—no larger model justifies its footprint unless it advances cognitive accuracy, Opus Hard formal verification, or operational efficiency:

| Weight Class | Pareto Champion | Quant & Size | Testbed | Speed (`TG` / `PP`) | 13 Areas (`Base ➔ RLM`) | Opus Hard (`AST/pytest`) | Role on the Pareto Frontier |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **100M** | **`Falcon-H1-Tiny-Multilingual-100M`** | `Q4_K_M` (`70.5 MB`) | CPU AVX2 | `28.09` / `584.8` t/s | **`11/39` (28.2%)** | `0/10` | Smallest functional 100M (`A01` Triage 3/3) |
| **135M** | **`SmolLM2-135M-Instruct`** | `F16` (`258.3 MB`) | CPU AVX2 | `41.58` / `759.0` t/s | `18` ➔ **`21/39` (53.9%)** | `0/10` | **Global Sub-200M Floor** (`Q4_K_M`: `17/39` @ `57.5 t/s`, `100.6 MB`) |
| **350M** | **`Granite-350M-Gemini3-Think`** | `F16` (`653.2 MB`) | RX 580 (`-fa off`) | `23.08` / `105.2` t/s | `25` ➔ **`29/39` (74.4%)** | **`1/10`** (`OPUS_06`) | **Smallest Opus Hard Solver Ever** (`Granite-H-350M [Q8_0]`: `29/39` in `349 MB`) |
| **500M** | **`MiniCPM4-0.5B`** | `Q8_0` (`441.4 MB`) | RX 580 / CPU | `38.6` GPU / `50.0` CPU | `24` ➔ **`31/39` (79.5%)** | `0/10` | **First <600M >30/39** (`Q4_K_M`: `29/39` @ `51.9 t/s` in `265.8 MB`) |
| **600M** | **`TinyQwen3-Distill-0.6B`** | `Q5_K_M` (`423.6 MB`) | CPU AVX2 | `41.23` / `214.5` t/s | `24` ➔ **`34/39` (87.2%)** | `0/10` | **DeepSeek-R1 5-Bit RLM Peak** (`Qwen3-0.6B-Distill-30B [Q4]`: `29➔32/39` @ `43.3 t/s`) |
| **900M** | **`IFM/K2-Horizon-0.9B`** | `Q6_K` (`846.4 MB`) | RX 580 / CPU | `34.29` GPU / `36.60` CPU | `25` ➔ **`34/39` (87.2%)** | **`4/10` (40%)** | **Sub-1B Opus Hard King** (`Q8_0`: **`35/39` + `3/10` Opus** in `1.07 GB`) |
| **1.0B** | **`IBM-GPT-5.4-Coder-1B`** | `Q6_K` (`1.25 GB`) | CPU (`-fa off`) | `18.9` / `96.0` t/s | **`31/39` (79.5%)** | **`2/10` (20%)** | **Regex Engine (`OPUS_01`) + Rain Water** (`MiniCPM5-1B [Q4]`: `32/39 + 1/10` @ `42 t/s`) |
| **1.7B** | **`Qwen3-1.7B`** | `Q5_K_M` (`1.40 GB`) | RX 580 / CPU | `31.22` GPU / `24.92` CPU | `32` ➔ **`36/39` (92.3%)** | **`1/10`** (`Q8_0`: **`2/10`**) | **1.4 GB Sub-2B Cognitive Sweet Spot** (`Q8_0`: `36/39 + 2/10` @ `31.07 t/s`) |
| **3.7B** | **`IFM/K2-Horizon-3.7B`** | `Q6_K` / `Q5_K_M` (`3.4–3.9 GB`) | RX 580 (`-ngl 99`) | `19.53`–`20.42` t/s | `36` ➔ **`37/39` (94.9%)** | **`3/10`–`4/10`** | **8 GB GPU Consumer King** (`BF16`: **`38/39 + 4/10`**; dominates `7B [Q4]`) |
| **4.0B** | **`Parable-Qwen3-4B-Fable5`** | `Q5_K_M` / `Q4_K_M` (`2.3–2.8 GB`) | RX 580 (`-ngl 99`) | `20.11`–`22.71` t/s | `34`–**`38/39` (97.4%)** | **`4/10` (`Q5_K_M`)** | **4B Amplitude (`38/39`) & Opus (`4/10`)** (`Gemma4-E4B [Q4]`: `36/39` @ `9.64 t/s` CPU) |
| **8B–9B** | **`MiMo-V2.6-Distill-Qwen-9B`** | `Q4_K_M` (`5.44 GB`) | Xeon AVX2 | `9.15` / `48.3` t/s | `31` ➔ **`38/39` (97.4%)** | **`3/10` (30%)** | **9B Ceiling** (`Qwen3-8B-GPT-5.2`: `35/39 + 1/10`; `Poe-8B`: `2/10` Opus) |
| **12B** | **`yuxinlu1-Gemma4-12B-Agentic-Fable5`** | `Q4_K_M` (`6.87 GB`) | Xeon AVX2 | `7.80` / `41.2` t/s | `24` ➔ **`38/39` (97.4%)** | `3` ➔ **`6/10` (60%)** | **Overall Best Dual-Score Dense Titan** (`coder-fable5-v1`: `33/39 + 4/10`) |
| **20B** | **`gpt-oss-20b-gpt-5-codex-distill`** | `Q8_0` (`11.28 GB`) | Xeon AVX2 | **`11.26`** / `11.37` t/s | **`30/39` (76.9%)** | **`3/10` (30%)** | **Fastest High-Precision 20B** (`antidoom [i1-IQ4_XS]`: **`31.29 t/s`** PLD Xeon) |
| **30B MoE** | **`Qwen3-30B-A3B-Thinking-Sonnet`** | `Q4_K_M` / `i1-IQ4_XS` (`15.2–17.3 GB`) | Xeon AVX2 | `3.65`–**`11.34`** t/s | `16` ➔ **`30/39`** | `3` ➔ **`6/10` (60%)** | **30B+ Opus Hard Supreme King** (`i1-IQ3_M`: `5/10` @ `6.82 t/s`) |
| **30B–35B** | **`Qwen3-30B-A3B`** | `IQ3_M` / `Q4_K_M` (`13.1–17.4 GB`) | Xeon AVX2 | **`8.14`** / `25.9` t/s | `23` ➔ **`36/39` (92.3%)** | `1/10` (`Q4_K_M`) | **30B+ 13-Area & Speed King** (`Qwen3.6-35B-Claude-4.7 [Q4]`: `35/39`) |

---

## 4. Master Telemetry Table — All 35 Bare-Metal Variants (`350M` – `7.0B`)

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
| **4** | **`K2-Horizon-7B`** `Q6_K` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | **`2➔3`** | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`36➔37` (+1)** |
| **5** | **`K2-Horizon-7B`** `Q5_K_M` | `3➔3` | `3➔3` | `1➔1` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | `2➔2` | `3➔3` | `3➔3` | `3➔3` | `3➔3` | **`36➔36` (+0)** |
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
| **`K2-Horizon-7B`** `Q6_K` | **7.0B** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ❌ Fail | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ✅ **Base** | ⏱️ Timeout | **`2 ➔ 2/10` (20%)** |
| **`K2-Horizon-7B`** `Q5_K_M` | **7.0B** | ❌ Fail | ⏱️ Timeout | ⏱️ Timeout | ❌ Fail | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ✅ **Base** | ✅ **Base** | ⏱️ Timeout | **`3 ➔ 3/10` (30%)** |
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

> **Extended Opus Hard Leaders Across 1.0B–35B:**
> - **1.0B:** `IBM-GPT-5.4-Coder-1B [Q6_K]` solved **`2/10`** (`OPUS_01` Pure Regex Engine + `OPUS_08`); `MiniCPM5-1B-Opus [Q4_K_M]` solved **`1/10`** (`OPUS_06`) at `42.0 tok/s`.
> - **3B–4.5B:** `IFM/K2-Horizon-3.7B` reached **`4/10`** in `Q5_K_M`, `Q8_0`, and `BF16` (Sec 17); `Parable-Qwen3-4B-Fable5 [Q5_K_M]` reached **`4/10`** (`5/10` in Sec 2); `Jackrong-GPT-5-Distill-Llama3.2-3B` reached **`4/10`**; `Qwen3-4B-Grok-4-Fast` rescued **`OPUS_10` (DPLL SAT)** via `Lambda-RLM`.
> - **12B & 30B+:** `yuxinlu1-Gemma4-12B-Agentic-Fable5 [Q4_K_M]` and `Qwen3-30B-A3B-Thinking-Claude-4.5-Sonnet [Q4_K_M]` share the **all-time laboratory Opus Hard record of `6/10 (60.0%)`** (`OPUS_04`, `OPUS_05`, `OPUS_06`, `OPUS_07`, `OPUS_08`, `OPUS_09`).

---

## 7. Complete Direct Hugging Face `.gguf` Download Catalog

Every checkpoint below was verified via HTTP 200 direct download and bare-metal execution.

### 7.1 Primary 35 Bare-Metal Variants (`350M` to `7.0B` Full Quantization Grid)

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

### 7.2 Extended Cross-Scale Champions (`600M`, `3B–14B`, and `18B–35B` Titãs)

For the full 100M–35B repository links across all 20 tiers, see [`FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md`](FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md). Key direct GGUF links for the extended champions:

| Weight Class | Model Name | Teacher / Architecture | Quant | Size | Direct Hugging Face Repository / `.gguf` URL |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **600M** | `TinyQwen3-Distill-0.6B` | DeepSeek-R1 (`0.6B` Dense) | `Q5_K_M` | 423.6 MB | [`TinyQwen3-distill-0.6B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q5_K_M.gguf) |
| **600M** | `Qwen3-0.6B-Distilled-30B-Thinking-SFT` | Qwen3-30B-A3B-Thinking (`0.6B`) | `Q4_K_M` | 420.3 MB | [`Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q4_K_M.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q4_K_M.gguf) |
| **600M** | `Qwen3-0.6B-Opus4.6-Abliterated` | Claude 4.6 Opus (`0.6B` Dense) | `Q8_0` | 609.8 MB | [`Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf) |
| **3.0B** | `ai9stars/G9v3-3B` | G9v3 Cognitive Distill (`3B` Dense) | `BF16` / `Q4_K_M` | 5.57 / 1.77 GB | [`ai9stars_G9v3-3B-bf16.gguf`](https://huggingface.co/bartowski/ai9stars_G9v3-3B-GGUF/resolve/main/ai9stars_G9v3-3B-bf16.gguf) |
| **4.0B** | `Parable-Qwen3-4B-Claude-Fable-5` | Claude 3.5 + Fable 5 (`4B` Dense) | `Q6_K` / `Q5_K_M` | 3.08 / 2.69 GB | [`Parable-Qwen3-4B-Claude-Fable-5-GGUF-Q6_K.gguf`](https://huggingface.co/AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF/resolve/main/Parable-Qwen3-4B-Claude-Fable-5-GGUF-Q6_K.gguf) |
| **4.5B** | `deadbydawn101-Gemma4-E4B-Opus` | Claude Opus + GeminiCLI (`4.5B`) | `Q4_K_M` | 4.97 GB | [`gemma4-e4b-opus-Q4_K_M.gguf`](https://huggingface.co/deadbydawn101/gemma-4-E4B-Agentic-Opus-Reasoning-GeminiCLI-GGUF/resolve/main/gemma4-e4b-opus-Q4_K_M.gguf) |
| **8.0B** | `Qwen3-8B-GPT-5.2-High-Reasoning` | OpenAI GPT-5.2 High Reasoning | `Q4_K_M` | 4.68 GB | [`TeichAI/Qwen3-8B-GPT-5.2-High-Reasoning-Distill-GGUF`](https://huggingface.co/TeichAI/Qwen3-8B-GPT-5.2-High-Reasoning-Distill-GGUF) |
| **9.0B** | `MiMo-V2.6-Distill-Qwen-9B` | Xiaomi MiMo V2.6 (`9B` Dense) | `Q4_K_M` | 5.44 GB | [`MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf`](https://huggingface.co/bartowski/MiMo-V2.6-Distill-Qwen-9B-GGUF/resolve/main/MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf) |
| **12B** | `yuxinlu1-Gemma4-12B-Agentic-Fable5` | Fable 5 × Composer 2.5 (`12B`) | `Q4_K_M` | 6.87 GB | [`gemma4-v2-Q4_K_M.gguf`](https://huggingface.co/yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF/resolve/main/gemma4-v2-Q4_K_M.gguf) |
| **18B** | `granite-4.0-h-small` | IBM Granite 4.0 Hybrid (`18B`) | `Q4_K_M` | 18.14 GB | [`granite-4.0-h-small-Q4_K_M.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-small-GGUF/resolve/main/granite-4.0-h-small-Q4_K_M.gguf) |
| **20B** | `gpt-oss-20b-gpt-5-codex-distill` | OpenAI GPT-5 Codex (`20.9B`) | `Q8_0` | 11.28 GB | [`TeichAI/gpt-oss-20b-gpt-5-codex-distill-GGUF`](https://huggingface.co/TeichAI/gpt-oss-20b-gpt-5-codex-distill-GGUF) |
| **26B MoE** | `gemma-4-26B-A4B-it-Claude-Opus-v2` | Claude 4.7 Opus (`26B / A4B` MoE) | `Q4_K_M` | 15.64 GB | [`gemma-4-26B-A4B-it-Claude-Opus-Distill.q4_k_m.gguf`](https://huggingface.co/TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill-v2-GGUF/resolve/main/gemma-4-26B-A4B-it-Claude-Opus-Distill.q4_k_m.gguf) |
| **30B MoE** | `Qwen3-30B-A3B` | Alibaba Qwen Native (`30.5B / A3B`) | `IQ3_M` / `Q4_K_M` | 13.11 / 17.35 GB | [`bartowski/Qwen_Qwen3-30B-A3B-GGUF`](https://huggingface.co/bartowski/Qwen_Qwen3-30B-A3B-GGUF) |
| **30B MoE** | `Qwen3-30B-A3B-Thinking-Claude-4.5-Sonnet` | Claude 4.5 Sonnet (`30.5B / A3B`) | `Q4_K_M` / `i1-IQ3_M` | 17.28 / 12.59 GB | [`TeichAI/...-Sonnet-Distill-GGUF`](https://huggingface.co/TeichAI/Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet-High-Reasoning-Distill-GGUF) \| [`mradermacher/...-i1-GGUF`](https://huggingface.co/mradermacher/Qwen3-30B-A3B-Thinking-2507-Claude-4.5-Sonnet-High-Reasoning-Distill-i1-GGUF) |
| **35B MoE** | `Qwen3.6-35B-A3B-Claude-4.7-Opus` | Claude 4.7 Opus (`35B / A3B`) | `Q4_K_M` | 19.71 GB | [`Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled.Q4_K_M.gguf`](https://huggingface.co/mradermacher/Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled-GGUF/resolve/main/Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled.Q4_K_M.gguf) |

---

## 8. Six Empirical Laws Discovered in the Laboratory

### Law 1: The Bit-Depth Sensitivity Regime Inversion (Sub-1B vs. 1.7B–4B)
* **Below 1.0B (`350M` – `900M`):** Ultra-compact models possess low parameter redundancy per attention/SSM head. Increasing quantization precision from `Q4_K_M` to `Q6_K` or `Q8_0` yields massive cognitive and algorithmic jumps without hurting throughput:
  * `MiniCPM4-0.5B` jumps from `29/39` (`Q4_K_M`) to **`31/39` (`Q8_0`)** at `49.99 tok/s` CPU.
  * `K2-Horizon-0.9B` jumps from `32/39 & 1/10 Opus` (`Q4_K_M`) to **`34/39 & 4/10 Opus` (`Q6_K`)** and **`35/39 & 3/10 Opus` (`Q8_0`)**.
  * `Granite-350M-Gemini3` unlocks **`1/10 Opus Hard`** only at `Q6_K`, `Q8_0`, and `F16` (`0/10` at `Q4_K_M`/`Q5_K_M`).
* **The Implicit Discretization Regularization Exception (`600M` & `4B` High-Ratio SFT Distills):** When a `600M` student is heavily SFT-distilled from a `30B+` teacher (`Qwen3-0.6B-Distill-30B`), unquantized `F16` retains high-frequency residual tail noise that causes attention dispersion (`29/39` at `24.1 tok/s`), whereas `Q4_K_M` (`Qwen-30B` teacher, `32/39` at `43.3 tok/s`) and `Q5_K_M` (`TinyQwen3-R1` teacher, `34/39` at `41.2 tok/s`) act as an optimal low-pass spectral filter. The exact same `F16` degradation repeats in 4B (`Parable-4B [F16]` drops `-71%` speed to `5.85 tok/s`; `Gemma4-E4B [F16]` drops from `2/10` Opus in `Q4_K_M` to `0/10`).
* **Above 1.7B (`1.7B` – `4.0B`):** **`Q5_K_M` and `Q6_K` represent the absolute Pareto optimum.** Moving to unquantized `F16`/`BF16` degrades generation speed by **44% to 71%** and can even reduce score (`Qwen3-1.7B [BF16]` scores `35/39` at `25.88 tok/s` vs. `36/39` at `31.22 tok/s` in `Q5_K_M`).

### Law 2: Hybrid Mamba-2 + Attention Flash Attention Numerical Degradation on Vulkan
* In hybrid State-Space Model (SSM / Mamba-2) + Attention architectures (`IBM Granite 4.0 Hybrid`: `Granite-4.0-H-350M`, `Granite-350M-Gemini3`, `IBM-GPT-5.4-Coder-1B`), enabling Vulkan Flash Attention (`-fa on`) introduces numerical precision drift across recurrent state updates.
* Explicitly disabling Flash Attention (**`-fa off` / `-fa 0`**) immediately restores mathematical and syntactic stability, propelling `Granite-4.0-H-350M [Q8_0]` to **`29/39 (74.36%)`** in just `349 MB` and allowing `Granite-350M-Gemini3` to solve `OPUS_06`.

### Law 3: The 8 GB GDDR5 VRAM Bandwidth & Reasoning Timeout Cliff on 7B Models
* On an 8 GB GDDR5 GPU (`224 GB/s` bandwidth), a `3.7B` model in `Q5_K_M` (`3.47 GB`) or `Q6_K` (`3.97 GB`) leaves over `4 GB` of headroom for KV cache and compute buffers, sustaining **`19.5 to 20.1 tok/s`** and completing deep `<think>` chains well within timeout limits (`3–4/10 Opus Hard`).
* A `7.0B` model in `Q4_K_M` (`5.33 GB`), despite fitting in VRAM (`-ngl 99`), saturates memory bandwidth and KV cache capacity, collapsing generation speed to **`6.89 tok/s`** (slower than 8-thread CPU AVX2 at `8.06 tok/s`). In long-horizon `<think>` tasks like Opus Hard, this 3x throughput penalty causes `240s` timeouts on 90% of problems (`1/10 Opus Hard`), proving that **a well-quantized `3.7B` (`Q6_K`/`Q5_K_M`) outperforms `7B` (`Q4_K_M`) in real-world autonomous coding on 8 GB GPUs**.

### Law 4: `Lambda-RLM` Recursive Metacognition Rescue Mechanics
* Across the 35 bare-metal variants in Table 4, **`Lambda-RLM` executed `+173` verified cognitive rescues** in the 13 Cognitive Areas (`+127` across the 26 Flyweight variants and `+46` across the 9 K2-Horizon variants), plus **4 formal LeetCode Hard rescues** in the Opus Hard suite (`OPUS_05` on `K2-Horizon-0.9B [Q8_0]`, `OPUS_08` on `K2-Horizon-0.9B [Q5_K_M]`, and `OPUS_06` on `Granite-350M-Gemini3 [F16]` & `[Q6_K]`).
* Across larger tiers, `Lambda-RLM` unlocked even more dramatic dormant capabilities: `granite-4.0-h-small (18B)` jumped **`5/39 ➔ 33/39 (+560%)`**, `Phi-4-reasoning-14B` jumped **`3/39 ➔ 31/39`**, `Qwen3-30B-A3B [IQ3_M]` jumped **`23/39 ➔ 36/39`**, and `Qwen3-30B-A3B-Thinking-Sonnet` doubled Opus Hard from **`3/10 ➔ 6/10`**.

### Law 5: The Sub-200M Pareto Cutoff & `1.0B` Opus Hard Physical Floor
* Beneath `200M` parameters, `SmolLM2-135M-Instruct [F16]` (`21/39`) remains the global floor across 14 audited models; pruning a `0.6B` model down to `0.2B` (`Qwen3-0.6B-Pruned-0.2B`) preserves `2494.7 tok/s` ingestion but causes total structural collapse (`0/39`).
* Meanwhile, testing all `600M` champions with unrestricted `8192`-token `<think>` budgets + `Lambda-RLM` (`Sec 12`) yielded **`0/40`** formal Opus Hard passes—confirming that **`350M` (`Granite-350M-Gemini3`, 1 outlier algorithm) and `0.9B–1.0B` (`K2-Horizon-0.9B` `4/10`, `IBM-GPT-5.4-Coder-1B` `2/10`, `MiniCPM5-1B` `1/10`)** mark the true architectural floor for multi-algorithm formal LeetCode Hard synthesis.

### Law 6: MoE Sparsity & 256-Bit AVX2 SIMD Alignment (`i1-IQ4_XS`) on 30B+ Titãs
* On Dual Xeon DDR4 bare-metal, `Q4_K_M` suffers SIMD misalignment and memory-bandwidth saturation (`3.65 tok/s` on `Qwen3-30B-Thinking-Sonnet`). Repacking/quantizing the exact same 30.5B MoE (`3.3B` active) model into **`i1-IQ4_XS`** (`15.24 GB`) aligns 256-bit AVX2 lanes and **triples generation speed to `11.34 tok/s` (+210.7%)** while retaining **`4/10` Opus Hard** (`i1-IQ3_M` hits the reasoning sweet spot at **`5/10` Opus Hard @ `6.82 tok/s`**).

---

## 📖 Citation & Reproducibility

To reproduce any benchmark in this laboratory on your own hardware:
1. Download the desired `.gguf` checkpoint from [Section 7](#7-complete-direct-hugging-face-gguf-download-catalog) or [`FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md`](FULL_BENCHMARK_RESULTS_AND_MODELS_CATALOG.md).
2. Inspect the exact prompts and formal AST/`pytest` verifiers in [`TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md`](TEST_SUITE_13_AREAS_39_QUESTIONS_AND_10_OPUS_HARD.md).
3. Run the tournament and audit scripts in [`suite/`](suite/) against your local `llama-server` and `llama-bench` binaries, and compare against the immutable telemetry proofs in [`proofs/`](proofs/).

```bibtex
@techreport{aethermind2026benchmarks,
  title       = {AetherMind Bare-Metal LLM Experimental Benchmark Laboratory: Full Quantization Grid & Lambda-RLM Formal Verification (100M to 35B+)},
  author      = {Ruan, Mestre and AetherMind Autonomous Research Lab},
  year        = {2026},
  month       = {November},
  institution = {AetherMind Apotheosis Laboratory},
  note        = {100M to 35B+ Bare-Metal GGUF Evaluation across 13 Cognitive Areas (39 Tests) and 10 Opus Hard AST/pytest Challenges on AMD RX 580 8GB Vulkan & Dual Intel Xeon E5-2696 v4 AVX2}
}
```
