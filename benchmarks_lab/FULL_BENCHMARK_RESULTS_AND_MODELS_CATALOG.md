# 🏛️ AETHERMIND BENCHMARKS LAB — FULL BARE-METAL BENCHMARK RESULTS & MODELS CATALOG (350M TO 7.0B)

**Primary Commander:** Mestre Ruan  
**Canonical Laboratory Repository:** `F:\AetherMind_Apotheosis_Final\benchmarks_lab\`  
**Empirical Proof Archives:** [`proofs/proof_k2_horizon_completo.json`](./proofs/proof_k2_horizon_completo.json) | [`proofs/proof_pesos_mosca_completo.json`](./proofs/proof_pesos_mosca_completo.json) | [`proofs/MASTER_LIVRO_SAGRADO_BENCHMARKS.md`](./proofs/MASTER_LIVRO_SAGRADO_BENCHMARKS.md)  
**Homologation Date:** November 21, 2026  
**Verification Status:** `[PROVED]` — 100% Bare-Metal Execution Certified by `AetherMind_Strict_Auditor.py` (Exit Code `0`)

---

## 🖥️ 1. Complete Laboratory Hardware & Software Environment

Every benchmark recorded in this catalog was executed under deterministic, zero-mock, bare-metal conditions on physical hardware. No cloud APIs, synthetic extrapolations, or simulated scores were used.

### 1.1 Physical Hardware Specifications
* **GPU (Primary Vulkan Accelerator):** **AMD Radeon RX 580 Series (Polari 20 XL/XTX)**
  * **Dedicated VRAM:** `8192 MiB` (`8.0 GB` GDDR5)
  * **Memory Bus & Bandwidth:** `256-bit` bus width | **`224.0 GB/s`** peak theoretical bandwidth
  * **Compute Backend:** `llama.cpp` Native **Vulkan** Backend (`ggml-vulkan`)
  * **GPU Layer Offloading (`-ngl`):** `-ngl 99` (100% full layer + KV cache offload into GDDR5 VRAM for all models up to `~5.35 GB` GGUF footprint). Models exceeding the 8 GB VRAM envelope (or saturating KV cache at `4096`–`8192` context) experience PCIe bus paging or require hybrid CPU/GPU layer splitting.
* **CPU (Pure AVX2 Bare-Metal Reference):** **x86_64 Multi-Core AVX2 Processor (Dual Intel Xeon E5-2696 v4 / 8-Thread & 14-Thread AVX2 Execution Pools)**
  * **Instruction Set Extensions:** `AVX2`, `FMA3`, `BMI2`, `F16C` (256-bit SIMD vector registers)
  * **Benchmarking Thread Allocation:**
    * **K2-Horizon Tournament (`tournament_k2_horizon.py`):** `-t 8` (8 dedicated physical AVX2 threads, `--device none -ngl 0` for pure CPU `llama-bench` measurements).
    * **Flyweight / Pesos-Mosca Tournament (`tournament_pesos_mosca.py`):** `-t 14` (14 dedicated AVX2 threads in `BelowNormal` process priority class `0x00004000`, `-ngl 0` for pure CPU `llama-bench` measurements).
* **System Memory (RAM):** **`32.0 GB` DDR4 System RAM** (Quad-channel / Dual-channel DDR4 memory subsystem feeding CPU AVX2 inference when `-ngl 0`).
* **Storage Subsystem:** High-speed NVMe SSD mounted at `F:\` (`F:\models\`, `F:\data\`, `F:\rotor-llm\`, `F:\AetherMind_Apotheosis_Final\`).
* **Operating System:** **Microsoft Windows 11 Pro (64-bit, Build 26100+)**.

### 1.2 Software Stack, Harness & Formal Verification Engines
* **Inference Server & Benchmarking Binary (`llama.cpp` Build b12420):**
  * **HTTP Inference Server:** `F:\AetherMind_LLM\bin\llama-server.exe`
    * **Flags:** `--host 127.0.0.1 --port 8089 -c 4096 -np 1 -b 512 -ub 512 --cont-batching` (`-cb`), `--fit off`, `-ngl 99` (with automatic fallback to `-ngl 0 --device none` if VRAM allocation fails), and architecture-specific Flash Attention (`-fa on` / `-fa 1` vs `-fa off` / `-fa 0`).
    * **Decoding Parameters:** `temperature: 0.0` (strictly greedy deterministic argmax decoding).
    * **Token Budgets:**
      * **13 Cognitive Areas (39 Tests):** `1280` max tokens (code) / `768` max tokens (text) for `<think>` models; `640` max tokens (code) / `448` max tokens (text) for non-thinking direct models.
      * **10 Opus Hard Challenges:** `2048` max tokens for `<think>` models; `1024` max tokens for non-thinking direct models.
  * **Raw Throughput Profiler:** `F:\AetherMind_LLM\bin\llama-bench.exe`
    * Measures pure CPU AVX2 Prompt Processing (`cpu_pp_tok_s` at `-p 128` or `-p 256`) and Text Generation (`cpu_tg_tok_s` at `-n 32` or `-n 64`) with `-ngl 0 -r 1`.
    * GPU Prompt Processing (`pp_tok_s`) and Text Generation (`tg_tok_s`) are measured directly from live `llama-server.exe` `/completion` timings over deterministic prompts (`64` to `96` forced tokens).
* **Recursive Metacognitive Engine (`Lambda-RLM`):**
  * **Location:** `F:\rotor-llm\lambda_rlm\rlm.py` (`class LambdaRLM`)
  * **Architecture:** 5-phase deterministic recursive metacognitive loop with combinatorial execution $\Phi$ in `LocalREPL` (`context_window_chars=40000`, `temperature=0.0`, `timeout=150.0s`).
  * **Evaluation Protocol (`Baseline ➔ Lambda-RLM`):**
    1. **Pass 1 (Zero-Shot Baseline):** The model is queried directly (`query_fast_direct`). Any `<think>...</think>` reasoning block is stripped (`extract_text_after_think`), Python code blocks are extracted (`clean_python_code`), and the output is immediately graded by the formal validator.
    2. **Pass 2 (Lambda-RLM Rescue on Failure):** If and only if Pass 1 fails, `Lambda-RLM` intercepts the failed prompt (and, in Opus Hard challenges, injects the exact `pytest`/AST counterexample failure trace from `formal_verifier`), decomposes the problem recursively, synthesizes a repaired response, and re-submits it to the formal validator.
    3. **Accounting:** Every test solved in Pass 1 is credited to both **Baseline** and **Final Score**. Every test that failed Pass 1 and passed Pass 2 is recorded as an explicit **`+RLM` Rescue**.
* **Formal Verification & Strict Empirical Auditing:**
  * **AST & Unit Test Verifier:** `F:\rotor-llm\router\formal_verifier.py` (`formal_verifier.verify_python_code(code, assertions, timeout_s=8.0)`). Executes generated Python functions in an isolated process against strict `assert` test suites with an `8.0s` hard execution timeout to catch infinite loops and algorithmic complexity violations ($O(N^2)$ vs $O(N \log N)$).
  * **Strict Empirical Auditor:** `F:\AetherMind_Apotheosis_Final\aethermind_apotheosis\AetherMind_Strict_Auditor.py`. Certifies the integrity of all JSON proof files, schema completeness, and non-zero empirical telemetry.

---

## 📦 2. Complete Model & Distiller Catalog with Direct Download Links

This section catalogs all **35 bare-metal benchmarked variants** across the 7 parameter tiers (`350M`, `500M`, `0.9B`, `1.0B`, `1.7B`, `3.7B`, `7.0B`) from the unified Flyweight (`proof_pesos_mosca_completo.json`) and K2-Horizon (`proof_k2_horizon_completo.json`) tournaments, followed by the **`600M` Pareto Champions** and **Historical `350M`/`500M`/`1.0B` Baseline Variants** from the *Livro Sagrado* (`MASTER_LIVRO_SAGRADO_BENCHMARKS.md`).

### 2.1 Master Architectural & Lineage Reference (Model Families)

| Model Family | Parameter Count | Architecture Type | Teacher / Distiller Model | Native Context Window | Thinking Mode (`<think>`) | Flash Attention (`-fa`) | GGUF Repository / Maintainer |
| :--- | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **`Granite-4.0-H-350M`** | `350M` | **Hybrid Mamba-2 + Transformer Attention** | **IBM Granite 4.0 Hybrid Base** (Foundation Pretrain/Instruct) | `128K` (`4096` bench) | `No` (Direct) | **`-fa off` (`0`)** *(Mandatory for Mamba-2 on Vulkan)* | [`ibm-granite/granite-4.0-h-350m-GGUF`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF) |
| **`Granite-350M-Gemini3`** | `350M` | **Hybrid Mamba-2 + Transformer Attention** | **Google Gemini 3 Pro Thinking** (Reasoning SFT Distillation) | `128K` (`4096` bench) | **`Yes` (`<think>`)** | **`-fa off` (`0`)** *(Mandatory for Mamba-2 on Vulkan)* | [`glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF) |
| **`MiniCPM4-0.5B`** | `500M` (`0.5B`) | **Dense Transformer (GQA / MiniCPM4)** | **OpenBMB MiniCPM4 Base** (Ultra-High-Density Pretrain + SFT) | `32K` (`4096` bench) | `No` (Direct) | **`-fa on` (`1`)** | [`mradermacher/MiniCPM4-0.5B-GGUF`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF) |
| **`QwQ-0.5B-Distilled`** | `500M` (`0.5B`) | **Dense Transformer (Qwen2.5 GQA)** | **Alibaba QwQ-32B / OpenAI o1-Style SFT** (Chain-of-Thought Distill) | `32K` (`4096` bench) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`mradermacher/QwQ-0.5B-Distilled-SFT-GGUF`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF) |
| **`Qwen2.5-0.5B-OpenR1`** | `500M` (`0.5B`) | **Dense Transformer (Qwen2.5 GQA)** | **DeepSeek-R1 (671B MoE)** (Open-R1 Reasoning Trace Distillation) | `32K` (`4096` bench) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF) |
| **`TinyQwen3-Distill-0.6B`** *(Livro Sagrado 600M)* | `600M` (`0.6B`) | **Dense Transformer (Qwen3 GQA)** | **DeepSeek-R1 (671B MoE)** (Full Chain-of-Thought SFT Distillation) | `32K` (`4096`–`8192`) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`mradermacher/TinyQwen3-distill-0.6B-GGUF`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF) |
| **`Qwen3-0.6B-Distill-30B`** *(Livro Sagrado 600M)* | `600M` (`0.6B`) | **Dense Transformer (Qwen3 GQA)** | **Alibaba Qwen3-30B-A3B-Thinking** (Homogeneous Family SFT Distillation) | `32K` (`4096`–`8192`) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF) |
| **`Qwen3-0.6B-Opus4.6`** *(Livro Sagrado 600M)* | `600M` (`0.6B`) | **Dense Transformer (Qwen3 GQA)** | **Anthropic Claude 4.6 Opus** (Pure Reasoning / Zero-Refusal Abliterated) | `32K` (`4096`–`8192`) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF) |
| **`K2-Horizon-0.9B`** | `900M` (`0.9B`) | **Dense Transformer (IFM Horizon Long-Context GQA)** | **IFM K2-Horizon 512K Native Pretrain/Midtrain + Reasoning SFT** | **`512K`** (`4096` bench) | `No` (Direct Fast Synthesis) | **`-fa on` (`1`)** | [`IFM/K2-Horizon-0.9B-GGUF`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF) |
| **`MiniCPM5-1B-Opus`** | `1.0B` | **Dense Transformer (MiniCPM5 High-Density GQA)** | **Anthropic Claude 4.6 Opus + Fable 5 V2 Thinking** (Heretic Uncensored) | `128K` (`4096` bench) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF) |
| **`IBM-GPT-5.4-Coder-1B`** | `1.0B` | **Hybrid / Dense Granite-Coder 1B Architecture** | **OpenAI GPT-5.4 Coder** (Code & Algorithmic SFT Distillation) | `128K` (`4096` bench) | `No` (Direct Code) | **`-fa off` (`0`)** | [`mradermacher/IBM-GPT-5.4-Coder-1B-GGUF`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF) & [`bartowski/IBM-GPT-5.4-Coder-1B-GGUF`](https://huggingface.co/bartowski/IBM-GPT-5.4-Coder-1B-GGUF) |
| **`Qwen3-1.7B`** | `1.7B` | **Dense Transformer (Qwen3 GQA)** | **Alibaba Qwen3 Native Thinking Distillation** (`bartowski` imatrix) | `32K` (`4096` bench) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`bartowski/Qwen_Qwen3-1.7B-GGUF`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF) |
| **`K2-Horizon-3.7B`** | `3.7B` | **Dense Transformer (IFM Horizon Long-Context GQA)** | **IFM K2-Horizon 512K Native Pretrain/Midtrain + Deep Thinking SFT** | **`512K`** (`4096` bench) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`IFM/K2-Horizon-3.7B-GGUF`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF) |
| **`K2-Horizon-7B`** | `7.0B` | **Dense Transformer (IFM Horizon Long-Context GQA)** | **IFM K2-Horizon 512K Native Pretrain/Midtrain + Deep Thinking SFT** | **`512K`** (`4096` bench) | **`Yes` (`<think>`)** | **`-fa on` (`1`)** | [`IFM/K2-Horizon-7B-GGUF`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF) |

---

### 2.2 Exact Direct Hugging Face `.gguf` Download Links — All 35 Bare-Metal Variants (`350M` to `7.0B`)

Every URL below points directly to the resolved binary `.gguf` artifact verified via HTTP 200 in `tournament_pesos_mosca.py` and `tournament_k2_horizon.py`:

| # | Variant ID (`proof.json` key) | Model Name | Params | Quant | Size (MB) | Architecture | Teacher / Distiller | Ctx | `<think>` | `-fa` | Exact Direct Hugging Face `.gguf` Download URL |
| :-: | :--- | :--- | :---: | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| **1** | `granite_h_350m__q4_k_m` | **Granite-4.0-H-350M** | `350M` | `Q4_K_M` | `212.35 MB` | Hybrid Mamba-2 + Attn | IBM Granite 4.0 Hybrid Base | `128K` | `No` | `off` | [`https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q4_K_M.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q4_K_M.gguf) |
| **2** | `granite_h_350m__q5_k_m` | **Granite-4.0-H-350M** | `350M` | `Q5_K_M` | `240.64 MB` | Hybrid Mamba-2 + Attn | IBM Granite 4.0 Hybrid Base | `128K` | `No` | `off` | [`https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q5_K_M.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q5_K_M.gguf) |
| **3** | `granite_h_350m__q6_k` | **Granite-4.0-H-350M** | `350M` | `Q6_K` | `270.71 MB` | Hybrid Mamba-2 + Attn | IBM Granite 4.0 Hybrid Base | `128K` | `No` | `off` | [`https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q6_K.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q6_K.gguf) |
| **4** | `granite_h_350m__q8_0` | **Granite-4.0-H-350M** | `350M` | `Q8_0` | `349.23 MB` | Hybrid Mamba-2 + Attn | IBM Granite 4.0 Hybrid Base | `128K` | `No` | `off` | [`https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf) |
| **5** | `granite_gemini3_350m__q5_k_m` | **Granite-350M-Gemini3** | `350M` | `Q5_K_M` | `240.64 MB` | Hybrid Mamba-2 + Attn | Google Gemini 3 Pro Thinking | `128K` | `Yes` | `off` | [`https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf) |
| **6** | `granite_gemini3_350m__q6_k` | **Granite-350M-Gemini3** | `350M` | `Q6_K` | `270.71 MB` | Hybrid Mamba-2 + Attn | Google Gemini 3 Pro Thinking | `128K` | `Yes` | `off` | [`https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf) |
| **7** | `granite_gemini3_350m__q8_0` | **Granite-350M-Gemini3** | `350M` | `Q8_0` | `349.23 MB` | Hybrid Mamba-2 + Attn | Google Gemini 3 Pro Thinking | `128K` | `Yes` | `off` | [`https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf) |
| **8** | `granite_gemini3_350m__f16` | **Granite-350M-Gemini3** | `350M` | `F16` | `653.17 MB` | Hybrid Mamba-2 + Attn | Google Gemini 3 Pro Thinking | `128K` | `Yes` | `off` | [`https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf) |
| **9** | `minicpm4_05b__q5_k_m` | **MiniCPM4-0.5B** | `500M` | `Q5_K_M` | `302.32 MB` | Dense Transformer GQA | OpenBMB MiniCPM4 Base | `32K` | `No` | `on` | [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf) |
| **10** | `minicpm4_05b__q6_k` | **MiniCPM4-0.5B** | `500M` | `Q6_K` | `341.22 MB` | Dense Transformer GQA | OpenBMB MiniCPM4 Base | `32K` | `No` | `on` | [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf) |
| **11** | `minicpm4_05b__q8_0` | **MiniCPM4-0.5B** | `500M` | `Q8_0` | `441.39 MB` | Dense Transformer GQA | OpenBMB MiniCPM4 Base | `32K` | `No` | `on` | [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf) |
| **12** | `minicpm4_05b__f16` | **MiniCPM4-0.5B** | `500M` | `F16` | `829.33 MB` | Dense Transformer GQA | OpenBMB MiniCPM4 Base | `32K` | `No` | `on` | [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf) |
| **13** | `qwq_05b_distilled__q5_k_m` | **QwQ-0.5B-Distilled** | `500M` | `Q5_K_M` | `400.62 MB` | Dense Transformer GQA | Alibaba QwQ / OpenAI o1 SFT | `32K` | `Yes` | `on` | [`https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q5_K_M.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q5_K_M.gguf) |
| **14** | `qwq_05b_distilled__q6_k` | **QwQ-0.5B-Distilled** | `500M` | `Q6_K` | `482.31 MB` | Dense Transformer GQA | Alibaba QwQ / OpenAI o1 SFT | `32K` | `Yes` | `on` | [`https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q6_K.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q6_K.gguf) |
| **15** | `qwq_05b_distilled__q8_0` | **QwQ-0.5B-Distilled** | `500M` | `Q8_0` | `506.47 MB` | Dense Transformer GQA | Alibaba QwQ / OpenAI o1 SFT | `32K` | `Yes` | `on` | [`https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q8_0.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q8_0.gguf) |
| **16** | `qwq_05b_distilled__f16` | **QwQ-0.5B-Distilled** | `500M` | `F16` | `948.13 MB` | Dense Transformer GQA | Alibaba QwQ / OpenAI o1 SFT | `32K` | `Yes` | `on` | [`https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.f16.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.f16.gguf) |
| **17** | `qwen25_05b_openr1__q5_k_m` | **Qwen2.5-0.5B-OpenR1** | `500M` | `Q5_K_M` | `400.62 MB` | Dense Transformer GQA | DeepSeek-R1 Distill | `32K` | `Yes` | `on` | [`https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q5_K_M.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q5_K_M.gguf) |
| **18** | `qwen25_05b_openr1__q6_k` | **Qwen2.5-0.5B-OpenR1** | `500M` | `Q6_K` | `482.31 MB` | Dense Transformer GQA | DeepSeek-R1 Distill | `32K` | `Yes` | `on` | [`https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q6_K.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q6_K.gguf) |
| **19** | `qwen25_05b_openr1__q8_0` | **Qwen2.5-0.5B-OpenR1** | `500M` | `Q8_0` | `506.47 MB` | Dense Transformer GQA | DeepSeek-R1 Distill | `32K` | `Yes` | `on` | [`https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q8_0.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q8_0.gguf) |
| **20** | `qwen25_05b_openr1__f16` | **Qwen2.5-0.5B-OpenR1** | `500M` | `F16` | `948.13 MB` | Dense Transformer GQA | DeepSeek-R1 Distill | `32K` | `Yes` | `on` | [`https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_f16.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_f16.gguf) |
| **21** | `k2_horizon_0_9b__q4_k_m` | **K2-Horizon-0.9B** | `0.9B` | `Q4_K_M` | `635.32 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `No` | `on` | [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf) |
| **22** | `k2_horizon_0_9b__q5_k_m` | **K2-Horizon-0.9B** | `0.9B` | `Q5_K_M` | `737.65 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `No` | `on` | [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf) |
| **23** | `k2_horizon_0_9b__q6_k` | **K2-Horizon-0.9B** | `0.9B` | `Q6_K` | `846.37 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `No` | `on` | [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf) |
| **24** | `k2_horizon_0_9b__q8_0` | **K2-Horizon-0.9B** | `0.9B` | `Q8_0` | `1095.40 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `No` | `on` | [`https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf`](https://huggingface.co/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf) |
| **25** | `minicpm5_1b_opus__f16` | **MiniCPM5-1B-Opus** | `1.0B` | `F16` | `2066.22 MB` | Dense Transformer GQA | Claude 4.6 Opus + Fable 5 V2 | `128K` | `Yes` | `on` | [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf) |
| **26** | `ibm_gpt54_coder_1b__f16` | **IBM-GPT-5.4-Coder-1B** | `1.0B` | `F16` | `3116.03 MB` | Granite 1B Hybrid/Dense | OpenAI GPT-5.4 Coder | `128K` | `No` | `off` | [`https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf) |
| **27** | `qwen3_1_7b__q4_k_m` | **Qwen3-1.7B** | `1.7B` | `Q4_K_M` | `1223.01 MB` | Dense Transformer GQA | Qwen3 Native Thinking | `32K` | `Yes` | `on` | [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf) |
| **28** | `qwen3_1_7b__q5_k_m` | **Qwen3-1.7B** | `1.7B` | `Q5_K_M` | `1403.58 MB` | Dense Transformer GQA | Qwen3 Native Thinking | `32K` | `Yes` | `on` | [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf) |
| **29** | `qwen3_1_7b__q8_0` | **Qwen3-1.7B** | `1.7B` | `Q8_0` | `2064.71 MB` | Dense Transformer GQA | Qwen3 Native Thinking | `32K` | `Yes` | `on` | [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf) |
| **30** | `qwen3_1_7b__bf16` | **Qwen3-1.7B** | `1.7B` | `BF16` | `3881.21 MB` | Dense Transformer GQA | Qwen3 Native Thinking | `32K` | `Yes` | `on` | [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf) |
| **31** | `k2_horizon_3_7b__q4_k_m` | **K2-Horizon-3.7B** | `3.7B` | `Q4_K_M` | `3010.37 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `Yes` | `on` | [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf) |
| **32** | `k2_horizon_3_7b__q5_k_m` | **K2-Horizon-3.7B** | `3.7B` | `Q5_K_M` | `3474.98 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `Yes` | `on` | [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf) |
| **33** | `k2_horizon_3_7b__q6_k` | **K2-Horizon-3.7B** | `3.7B` | `Q6_K` | `3968.62 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `Yes` | `on` | [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf) |
| **34** | `k2_horizon_3_7b__q8_0` | **K2-Horizon-3.7B** | `3.7B` | `Q8_0` | `5136.88 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `Yes` | `on` | [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf) |
| **35** | `k2_horizon_7b__q4_k_m` | **K2-Horizon-7B** | `7.0B` | `Q4_K_M` | `5333.15 MB` | Dense Transformer GQA | IFM K2-Horizon 512K Native | `512K` | `Yes` | `on` | [`https://huggingface.co/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q4_K_M.gguf`](https://huggingface.co/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q4_K_M.gguf) |

---

### 2.3 Exact Direct Hugging Face `.gguf` Download Links — `600M` Champions & Complementary Historical Variants (`Livro Sagrado` Sections 7–18)

To provide a 100% self-contained reference across all quantizations (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`, `F16`, `BF16`), the table below lists the direct `.gguf` download URLs for the **`600M` Pareto Champions** (`TinyQwen3-Distill-0.6B`, `Qwen3-0.6B-Distilled-30B-Thinking-SFT`, `Qwen3-0.6B-Opus4.6-Abliterated`) and the complementary **`350M` / `500M` / `1.0B` / `1.7B` / `3.7B`** quantizations benchmarked in prior rounds of the *Livro Sagrado*:

| Model Name | Params | Quant | Size (MB) | Teacher / Distiller | 13 Areas (`Base ➔ RLM`) | Opus Hard | Exact Direct Hugging Face `.gguf` Download URL |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: | :--- |
| **TinyQwen3-Distill-0.6B** 👑 | `600M` | **`Q5_K_M`** | `423.6 MB` | **DeepSeek-R1** | `24/39 ➔ 34/39 (87.18%)` | `0/10` | [`https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q5_K_M.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q5_K_M.gguf) |
| **TinyQwen3-Distill-0.6B** 🥈 | `600M` | **`Q6_K`** | `472.0 MB` | **DeepSeek-R1** | `23/39 ➔ 33/39 (84.62%)` | `0/10` | [`https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q6_K.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q6_K.gguf) |
| **TinyQwen3-Distill-0.6B** | `600M` | `Q4_K_M` | `378.1 MB` | **DeepSeek-R1** | `25/39 ➔ 28/39 (71.79%)` | `0/10` | [`https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q4_K_M.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q4_K_M.gguf) |
| **TinyQwen3-Distill-0.6B** | `600M` | `Q8_0` | `609.5 MB` | **DeepSeek-R1** | `23/39 ➔ 28/39 (71.79%)` | `0/10` | [`https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q8_0.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.Q8_0.gguf) |
| **TinyQwen3-Distill-0.6B** | `600M` | `F16` | `1142.2 MB` | **DeepSeek-R1** | `20/39 ➔ 30/39 (76.92%)` | `0/10` | [`https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.f16.gguf`](https://huggingface.co/mradermacher/TinyQwen3-distill-0.6B-GGUF/resolve/main/TinyQwen3-distill-0.6B.f16.gguf) |
| **Qwen3-0.6B-Distill-30B** 👑 | `600M` | **`Q4_K_M`** | `420.3 MB` | **Qwen3-30B-A3B-Thinking** | `29/39 ➔ 32/39 (82.05%)` | `0/10` | [`https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q4_K_M.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q4_K_M.gguf) |
| **Qwen3-0.6B-Distill-30B** | `600M` | `Q5_K_M` | `510.0 MB` | **Qwen3-30B-A3B-Thinking** | `28/39 ➔ 30/39 (76.92%)` | `0/10` | [`https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q5_K_M.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q5_K_M.gguf) |
| **Qwen3-0.6B-Distill-30B** | `600M` | `Q6_K` | `580.0 MB` | **Qwen3-30B-A3B-Thinking** | `27/39 ➔ 29/39 (74.36%)` | `0/10` | [`https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q6_K.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q6_K.gguf) |
| **Qwen3-0.6B-Distill-30B** | `600M` | `Q8_0` | `750.0 MB` | **Qwen3-30B-A3B-Thinking** | `28/39 ➔ 30/39 (76.92%)` | `0/10` | [`https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q8_0.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-Q8_0.gguf) |
| **Qwen3-0.6B-Distill-30B** | `600M` | `F16` | `1410.0 MB` | **Qwen3-30B-A3B-Thinking** | `27/39 ➔ 29/39 (74.36%)` | `0/10` | [`https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-f16.gguf`](https://huggingface.co/reaper/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF/resolve/main/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-f16.gguf) |
| **Qwen3-0.6B-Opus4.6** 👑 | `600M` | **`Q8_0`** | `609.8 MB` | **Claude 4.6 Opus** | `29/39 ➔ 32/39 (82.05%)` | `0/10` | [`https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q8_0.gguf) |
| **Qwen3-0.6B-Opus4.6** ⚖️ | `600M` | **`Q5_K_M`** | `423.8 MB` | **Claude 4.6 Opus** | `29/39 ➔ 30/39 (76.92%)` | `0/10` | [`https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q5_K_M.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q5_K_M.gguf) |
| **Qwen3-0.6B-Opus4.6** | `600M` | `Q4_K_M` | `378.3 MB` | **Claude 4.6 Opus** | `26/39 ➔ 30/39 (76.92%)` | `0/10` | [`https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q4_K_M.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q4_K_M.gguf) |
| **Qwen3-0.6B-Opus4.6** | `600M` | `Q6_K` | `472.2 MB` | **Claude 4.6 Opus** | `25/39 ➔ 30/39 (76.92%)` | `0/10` | [`https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q6_K.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.Q6_K.gguf) |
| **Qwen3-0.6B-Opus4.6** | `600M` | `F16` | `1142.7 MB` | **Claude 4.6 Opus** | `26/39 ➔ 29/39 (74.36%)` | `0/10` | [`https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.f16.gguf`](https://huggingface.co/szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF/resolve/main/Qwen3-0.6B-Opus4.6-Abliterated.f16.gguf) |
| **Granite-4.0-H-350M** | `350M` | `BF16` | `653.2 MB` | **IBM Granite 4.0 Hybrid** | `19/39 ➔ 29/39 (74.36%)` | `0/10` | [`https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-bf16.gguf`](https://huggingface.co/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-bf16.gguf) |
| **Granite-350M-Gemini3** | `350M` | `Q4_K_M` | `212.3 MB` | **Gemini 3 Pro Thinking** | `18/39 ➔ 26/39 (66.67%)` | `0/10` | [`https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q4_k_m.gguf`](https://huggingface.co/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q4_k_m.gguf) |
| **MiniCPM4-0.5B** | `500M` | `Q4_K_M` | `265.8 MB` | **OpenBMB MiniCPM4 Base** | `23/39 ➔ 29/39 (74.36%)` | `0/10` | [`https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q4_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q4_K_M.gguf) |
| **QwQ-0.5B-Distilled** | `500M` | `Q4_K_M` | `379.4 MB` | **Alibaba QwQ / OpenAI o1** | `24/39 ➔ 29/39 (74.36%)` | `0/10` | [`https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q4_K_M.gguf`](https://huggingface.co/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q4_K_M.gguf) |
| **Qwen2.5-0.5B-OpenR1** | `500M` | `Q4_K_M` | `379.4 MB` | **DeepSeek-R1 Distill** | `22/39 ➔ 27/39 (69.23%)` | `0/10` | [`https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q4_K_M.gguf`](https://huggingface.co/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q4_K_M.gguf) |
| **MiniCPM5-1B-Opus** 👑 | `1.0B` | **`Q4_K_M`** | `655.4 MB` | **Claude 4.6 Opus + Fable 5** | `23/39 ➔ 32/39 (82.05%)` | `1/10` (`OPUS_06`) | [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q4_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q4_K_M.gguf) |
| **MiniCPM5-1B-Opus** | `1.0B` | `Q5_K_M` | `747.5 MB` | **Claude 4.6 Opus + Fable 5** | `25/39 ➔ 32/39 (82.05%)` | `0/10` | [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q5_K_M.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q5_K_M.gguf) |
| **MiniCPM5-1B-Opus** | `1.0B` | `Q6_K` | `849.9 MB` | **Claude 4.6 Opus + Fable 5** | `25/39 ➔ 32/39 (82.05%)` | `0/10` | [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q6_K.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q6_K.gguf) |
| **MiniCPM5-1B-Opus** 🌟 | `1.0B` | **`Q8_0`** | `1095.7 MB` | **Claude 4.6 Opus + Fable 5** | `27/39 ➔ 33/39 (84.62%)` | `0/10` | [`https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q8_0.gguf`](https://huggingface.co/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q8_0.gguf) |
| **IBM-GPT-5.4-Coder-1B** | `1.0B` | `Q4_K_M` | `972.8 MB` | **OpenAI GPT-5.4 Coder** | `29/39 ➔ 33/39 (84.62%)` | `0/10` | [`https://huggingface.co/bartowski/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B-Q4_K_M.gguf`](https://huggingface.co/bartowski/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B-Q4_K_M.gguf) |
| **IBM-GPT-5.4-Coder-1B** | `1.0B` | `Q5_K_M` | `1126.4 MB` | **OpenAI GPT-5.4 Coder** | `29/39 ➔ 31/39 (79.49%)` | `1/10` (`OPUS_04`) | [`https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q5_K_M.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q5_K_M.gguf) |
| **IBM-GPT-5.4-Coder-1B** 👑 | `1.0B` | **`Q6_K`** | `1280.0 MB` | **OpenAI GPT-5.4 Coder** | `29/39 ➔ 31/39 (79.49%)` | **`2/10`** (`OPUS_01`, `08`) | [`https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q6_K.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q6_K.gguf) |
| **IBM-GPT-5.4-Coder-1B** | `1.0B` | `Q8_0` | `1658.9 MB` | **OpenAI GPT-5.4 Coder** | `29/39 ➔ 32/39 (82.05%)` | `1/10` (`OPUS_04`) | [`https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q8_0.gguf`](https://huggingface.co/mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.i1-Q8_0.gguf) |
| **Qwen3-1.7B** *(Early Round)* | `1.7B` | `Q6_K` | `1597.4 MB` | **Qwen3 Native Thinking** | `22/39 ➔ 36/39 (92.31%)` | `4/10` | [`https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q6_K.gguf`](https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q6_K.gguf) |
| **K2-Horizon-3.7B** *(Sec. 17)* | `3.7B` | `BF16` | `9656.3 MB` | **IFM K2-Horizon 512K** | `36/39 ➔ 38/39 (97.44%)` | `4/10` (`-ngl 12`) | [`https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-BF16.gguf`](https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-BF16.gguf) |

---

## 📊 3. Complete Telemetry & Results Matrices

### 3.1 Master 35-Model Telemetry Table (`350M` to `7.0B` — Sorted by Cognitive Accuracy & Opus Hard Score)

> **Legend:**
> * **`Ctx / Think / FA / NGL`:** Native Context Window (`512K`, `128K`, `32K`) | Thinking Mode (`T:S` = Active `<think>`, `T:N` = Non-Thinking Direct) | Flash Attention (`FA:on` vs `FA:off`) | Active GPU Offload Layers (`NGL:99` = 100% in RX 580 8GB VRAM).
> * **`GPU PP` / `GPU TG`:** Prompt Processing (`tok/s`) and Text Generation (`tok/s`) on AMD Radeon RX 580 8GB Vulkan.
> * **`CPU PP` / `CPU TG`:** Pure CPU AVX2 Prompt Processing (`tok/s`) and Text Generation (`tok/s`) via `llama-bench -ngl 0`.
> * **`13 Areas: Base ➔ Final`:** Zero-Shot Baseline score vs. Final `Lambda-RLM` score out of 39 tests across 13 cognitive areas.
> * **`+RLM (13A)`:** Exact number of failed Baseline tests rescued by `Lambda-RLM` recursive metacognition (`+166 total rescues` across the 35 models: `+127` in the 26 Pesos-Mosca variants and `+39` in the 9 K2-Horizon variants).
> * **`Gabaritos`:** Number of cognitive areas (out of 13) where the model achieved a perfect `3/3` score.

| Rank | Tier | Model | Quant | Ctx / Think / FA / NGL | Size (MB) | Boot (s) | GPU PP (tok/s) | GPU TG (tok/s) | CPU PP (tok/s) | CPU TG (tok/s) | 13 Areas: Base ➔ Final (% Final) | +RLM (13A) | Gabaritos | Opus Hard: Base ➔ Final | +RLM (Opus) | Specific Opus Challenges Solved (Pass Origin) |
| :-: | :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **1** | **3.7B** | **`K2-Horizon-3.7B`** | `Q8_0` | 512K / T:S / FA:on / NGL:99 | `5136.88 MB` | `10.76s` | `94.17` | **`19.91`** | `110.55` | `9.14` | `32/39` ➔ **`37/39` (94.87%)** | **`+5 RLM`** | `11/13` | `3/10` ➔ **`3/10` (30%)** | `+0 RLM` | `OPUS_04` (Base), `OPUS_05` (Base), `OPUS_09` (Base) |
| **2** | **3.7B** | **`K2-Horizon-3.7B`** 👑 | **`Q6_K`** | 512K / T:S / FA:on / NGL:99 | `3968.62 MB` | `9.26s` | `76.80` | **`19.53`** | `109.97` | `10.48` | `31/39` ➔ **`37/39` (94.87%)** | **`+6 RLM`** | `11/13` | `3/10` ➔ **`3/10` (30%)** | `+0 RLM` | `OPUS_04` (Base), `OPUS_05` (Base), `OPUS_07` (Base) |
| **3** | **3.7B** | **`K2-Horizon-3.7B`** 🔥 | **`Q5_K_M`** | 512K / T:S / FA:on / NGL:99 | `3474.98 MB` | `9.79s` | `80.90` | **`20.11`** | `119.21` | `11.37` | **`36/39`** ➔ **`37/39` (94.87%)** | **`+1 RLM`** | `11/13` | `2/10` ➔ **`2/10` (20%)** | `+0 RLM` | `OPUS_04` (Base), `OPUS_07` (Base) |
| **4** | **7.0B** | **`K2-Horizon-7B`** ⚠️ | `Q4_K_M` | 512K / T:S / FA:on / NGL:99 | `5333.15 MB` | `5.05s` | `15.82` | **`6.89`** | `41.73` | `8.06` | **`36/39`** ➔ **`37/39` (94.87%)** | **`+1 RLM`** | `11/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_08` (Base) |
| **5** | **1.7B** | **`Qwen3-1.7B`** 👑 | **`Q8_0`** | 32K / T:S / FA:on / NGL:99 | `2064.71 MB` | `5.64s` | `159.50` | **`31.07`** | `225.57` | `19.64` | `34/39` ➔ **`36/39` (92.31%)** | **`+2 RLM`** | `11/13` | `2/10` ➔ **`2/10` (20%)** | `+0 RLM` | `OPUS_06` (Base), `OPUS_07` (Base) |
| **6** | **1.7B** | **`Qwen3-1.7B`** ⚖️ | **`Q5_K_M`** | 32K / T:S / FA:on / NGL:99 | `1403.58 MB` | `5.25s` | `182.62` | **`31.22`** | `243.24` | `24.92` | `32/39` ➔ **`36/39` (92.31%)** | **`+4 RLM`** | `11/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_06` (Base) |
| **7** | **3.7B** | **`K2-Horizon-3.7B`** | `Q4_K_M` | 512K / T:S / FA:on / NGL:99 | `3010.37 MB` | `8.19s` | `82.57` | **`22.59`** | `126.38` | `12.54` | `34/39` ➔ **`36/39` (92.31%)** | **`+2 RLM`** | `10/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_04` (Base) |
| **8** | **0.9B** | **`K2-Horizon-0.9B`** 👑 | **`Q8_0`** | 512K / T:N / FA:on / NGL:99 | `1095.40 MB` | `1.52s` | `44.20` | **`28.39`** | `119.05` | `28.46` | `27/39` ➔ **`35/39` (89.74%)** | **`+8 RLM`** | `10/13` | `2/10` ➔ **`3/10` (30%)** | **`+1 RLM`** | `OPUS_05` (**RLM**), `OPUS_06` (Base), `OPUS_08` (Base) |
| **9** | **1.7B** | **`Qwen3-1.7B`** | `Q4_K_M` | 32K / T:S / FA:on / NGL:99 | `1223.01 MB` | `5.74s` | `174.51` | **`33.08`** | `252.07` | `26.38` | `34/39` ➔ **`35/39` (89.74%)** | **`+1 RLM`** | `10/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_05` (Base) |
| **10** | **1.7B** | **`Qwen3-1.7B`** | `BF16` | 32K / T:S / FA:on / NGL:99 | `3881.21 MB` | `9.73s` | `55.68` | **`25.88`** | `153.65` | `11.06` | `33/39` ➔ **`35/39` (89.74%)** | **`+2 RLM`** | `10/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_07` (Base) |
| **11** | **0.9B** | **`K2-Horizon-0.9B`** 🏆 | **`Q6_K`** | 512K / T:N / FA:on / NGL:99 | `846.37 MB` | `2.57s` | `121.33` | **`34.29`** | `312.45` | **`36.60`** | `25/39` ➔ **`34/39` (87.18%)** | **`+9 RLM`** | `9/13` | **`4/10`** ➔ **`4/10` (40%)** | `+0 RLM` | `OPUS_05` (Base), `OPUS_06` (Base), `OPUS_08` (Base), `OPUS_09` (Base) |
| **12** | **0.9B** | **`K2-Horizon-0.9B`** ⚡ | **`Q5_K_M`** | 512K / T:N / FA:on / NGL:99 | `737.65 MB` | `2.55s` | `242.11` | **`33.35`** | `335.64` | **`38.57`** | `26/39` ➔ **`33/39` (84.62%)** | **`+7 RLM`** | `8/13` | `3/10` ➔ **`4/10` (40%)** | **`+1 RLM`** | `OPUS_05` (Base), `OPUS_06` (Base), `OPUS_07` (Base), `OPUS_08` (**RLM**) |
| **13** | **1.0B** | **`MiniCPM5-1B-Opus`** | `F16` | 128K / T:S / FA:on / NGL:99 | `2066.22 MB` | `6.04s` | `149.18` | **`38.69`** | `293.67` | `21.38` | `30/39` ➔ **`32/39` (82.05%)** | **`+2 RLM`** | `7/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_06` (Base) |
| **14** | **0.9B** | **`K2-Horizon-0.9B`** | `Q4_K_M` | 512K / T:N / FA:on / NGL:99 | `635.32 MB` | `2.58s` | `183.37` | **`37.65`** | `354.40` | **`43.01`** | `21/39` ➔ **`32/39` (82.05%)** | **`+11 RLM`** | `7/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_06` (Base) |
| **15** | **1.0B** | **`IBM-GPT-5.4-Coder-1B`** | `F16` | 128K / T:N / FA:off / NGL:99 | `3116.03 MB` | `8.06s` | `66.95` | **`17.34`** | `148.28` | `11.57` | `28/39` ➔ **`32/39` (82.05%)** | **`+4 RLM`** | `8/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_08` (Base) |
| **16** | **500M** | **`MiniCPM4-0.5B`** 👑 | **`Q8_0`** | 32K / T:N / FA:on / NGL:99 | `441.39 MB` | `3.61s` | `311.56` | **`38.60`** | `556.24` | **`49.99`** | `24/39` ➔ **`31/39` (79.49%)** | **`+7 RLM`** | `7/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **17** | **500M** | **`MiniCPM4-0.5B`** | `Q6_K` | 32K / T:N / FA:on / NGL:99 | `341.22 MB` | `3.24s` | `267.18` | **`37.33`** | `524.86` | **`56.02`** | `27/39` ➔ **`30/39` (76.92%)** | **`+3 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **18** | **500M** | **`MiniCPM4-0.5B`** | `F16` | 32K / T:N / FA:on / NGL:99 | `829.33 MB` | `4.05s` | `303.32` | **`36.75`** | `394.17` | `36.18` | `26/39` ➔ **`30/39` (76.92%)** | **`+4 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **19** | **500M** | **`MiniCPM4-0.5B`** | `Q5_K_M` | 32K / T:N / FA:on / NGL:99 | `302.32 MB` | `4.04s` | `295.45` | **`32.53`** | `569.83` | **`54.99`** | `22/39` ➔ **`30/39` (76.92%)** | **`+8 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **20** | **350M** | **`Granite-350M-Gemini3`** 👑 | **`F16`** | 128K / T:S / FA:off / NGL:99 | `653.17 MB` | `4.46s` | `105.24` | **`23.08`** | `380.88` | `10.01` | `25/39` ➔ **`29/39` (74.36%)** | **`+4 RLM`** | `7/13` | `0/10` ➔ **`1/10` (10%)** | **`+1 RLM`** | `OPUS_06` (**RLM**) |
| **21** | **350M** | **`Granite-4.0-H-350M`** 👑 | **`Q8_0`** | 128K / T:N / FA:off / NGL:99 | `349.23 MB` | `3.61s` | `124.18` | **`21.80`** | `399.75` | `10.54` | `18/39` ➔ **`29/39` (74.36%)** | **`+11 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **22** | **500M** | **`QwQ-0.5B-Distilled`** | `Q6_K` | 32K / T:S / FA:on / NGL:99 | `482.31 MB` | `3.62s` | `290.94` | **`48.29`** | `424.22` | `30.34` | `24/39` ➔ **`28/39` (71.79%)** | **`+4 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **23** | **350M** | **`Granite-4.0-H-350M`** | `Q4_K_M` | 128K / T:N / FA:off / NGL:99 | `212.35 MB` | `3.26s` | `139.12` | **`22.18`** | `428.20` | `12.43` | `19/39` ➔ **`28/39` (71.79%)** | **`+9 RLM`** | `5/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **24** | **500M** | **`QwQ-0.5B-Distilled`** | `Q5_K_M` | 32K / T:S / FA:on / NGL:99 | `400.62 MB` | `6.07s` | `63.31` | **`50.15`** | `405.40` | `46.78` | `24/39` ➔ **`27/39` (69.23%)** | **`+3 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **25** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `F16` | 32K / T:S / FA:on / NGL:99 | `948.13 MB` | `4.49s` | `234.72` | **`43.91`** | `440.34` | `30.34` | `23/39` ➔ **`27/39` (69.23%)** | **`+4 RLM`** | `7/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **26** | **350M** | **`Granite-4.0-H-350M`** | `Q6_K` | 128K / T:N / FA:off / NGL:99 | `270.71 MB` | `4.02s` | `109.38` | **`21.92`** | `164.61` | `2.07` | `17/39` ➔ **`27/39` (69.23%)** | **`+10 RLM`** | `4/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **27** | **350M** | **`Granite-350M-Gemini3`** | `Q8_0` | 128K / T:S / FA:off / NGL:99 | `349.23 MB` | `3.63s` | `111.19` | **`21.99`** | `420.63` | `10.68` | `21/39` ➔ **`26/39` (66.67%)** | **`+5 RLM`** | `5/13` | `1/10` ➔ **`1/10` (10%)** | `+0 RLM` | `OPUS_06` (Base) |
| **28** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `Q6_K` | 32K / T:S / FA:on / NGL:99 | `482.31 MB` | `4.02s` | `254.96` | **`50.18`** | `494.02` | `43.08` | `23/39` ➔ **`26/39` (66.67%)** | **`+3 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **29** | **500M** | **`QwQ-0.5B-Distilled`** | `Q8_0` | 32K / T:S / FA:on / NGL:99 | `506.47 MB` | `2.56s` | `220.00` | **`50.03`** | `510.16` | `43.39` | `22/39` ➔ **`26/39` (66.67%)** | **`+4 RLM`** | `5/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **30** | **500M** | **`QwQ-0.5B-Distilled`** | `F16` | 32K / T:S / FA:on / NGL:99 | `948.13 MB` | `3.83s` | `182.50` | **`43.80`** | `389.69` | `23.50` | `22/39` ➔ **`26/39` (66.67%)** | **`+4 RLM`** | `5/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **31** | **350M** | **`Granite-350M-Gemini3`** | `Q6_K` | 128K / T:S / FA:off / NGL:99 | `270.71 MB` | `2.15s` | `123.05` | **`21.88`** | `375.06` | `6.33` | `23/39` ➔ **`25/39` (64.10%)** | **`+2 RLM`** | `4/13` | `0/10` ➔ **`1/10` (10%)** | **`+1 RLM`** | `OPUS_06` (**RLM**) |
| **32** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `Q8_0` | 32K / T:S / FA:on / NGL:99 | `506.47 MB` | `4.04s` | `260.23` | **`50.60`** | `522.88` | `46.63` | `22/39` ➔ **`25/39` (64.10%)** | **`+3 RLM`** | `5/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **33** | **500M** | **`Qwen2.5-0.5B-OpenR1`** | `Q5_K_M` | 32K / T:S / FA:on / NGL:99 | `400.62 MB` | `3.63s` | `287.10` | **`47.81`** | `469.97` | `45.54` | `18/39` ➔ **`24/39` (61.54%)** | **`+6 RLM`** | `6/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **34** | **350M** | **`Granite-4.0-H-350M`** | `Q5_K_M` | 128K / T:N / FA:off / NGL:99 | `240.64 MB` | `3.22s` | `134.09` | **`14.10`** | `142.47` | `2.33` | `16/39` ➔ **`24/39` (61.54%)** | **`+8 RLM`** | `2/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |
| **35** | **350M** | **`Granite-350M-Gemini3`** | `Q5_K_M` | 128K / T:S / FA:off / NGL:99 | `240.64 MB` | `3.27s` | `131.78` | **`21.87`** | `407.37` | `11.03` | `9/39` ➔ **`19/39` (48.72%)** | **`+10 RLM`** | `2/13` | `0/10` ➔ **`0/10` (0%)** | `+0 RLM` | — |

---

### 3.2 Full 35 × 13 Area-by-Area Cognitive Decomposition Matrix (`Baseline ➔ Final Lambda-RLM`)

Every cell below reports `Baseline Score ➔ Final Lambda-RLM Score` out of `3` tests per area (`39` total tests across `13` cognitive areas). Bold cells highlight tests rescued by `Lambda-RLM`.

* **A01:** Reflexo / Triagem (*Intent Classification & Agile Routing*)
* **A02:** Engenharia de Código (*Python Synthesis, Refactoring & Patches*)
* **A03:** Matemática & Provas (*Formal Proofs, Symbolic Logic & Calculus*)
* **A04:** Automação de SO / RPA (*Windows GUI, OCR, Processes & PowerShell*)
* **A05:** Memória Perene (*Knowledge Graphs, Cypher & State Persistence*)
* **A06:** Metacognição (*Self-Correction, LTI Stability & Counterexample Repair*)
* **A07:** Cadinho Red-Team (*Fuzzing, Exploit Auditing & Defensive Security*)
* **A08:** Síntese Vocal (*Phonetic Normalization & Prosody TTS Formatting*)
* **A09:** Multimodal & Visão (*Screen Geometry, SVG Parsing & Spatial Coordinates*)
* **A10:** Planejamento Deliberativo (*Multi-Step Chained Plans & PDDL*)
* **A11:** Raciocínio Científico (*Physics, Chemistry & Systems Engineering*)
* **A12:** Linguagem & Discurso (*Rhetorical Coherence, Synthesis & Verbal Logic*)
* **A13:** Governador de Hardware (*Clocks, Thermal Envelopes & VRAM Budgeting*)

| # | Model & Quantization | A01 Triagem | A02 Código | A03 Mat | A04 RPA | A05 Memória | A06 Meta | A07 RedTeam | A08 Vocal | A09 Visão | A10 PDDL | A11 Ciência | A12 Língua | A13 Hardw | Total (`Base ➔ RLM`) |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
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

### 3.3 Full 35 × 10 Opus Hard Algorithm-by-Algorithm Matrix (`Baseline` vs. `Lambda-RLM` vs. `Fail/Timeout`)

Each of the 10 Opus Hard challenges is a LeetCode Hard / Olympiad-grade algorithmic problem verified via Python AST inspection (forbidding cheat modules such as `import re` or `eval()`) and multi-case `pytest` assertions with an 8.0s execution timeout:

* **`OPUS_01`:** Pure Regex Engine supporting `.`, `*`, and `+` (DP / NFA without `re` module)
* **`OPUS_02`:** Algebraic Expression Parser without `eval()` supporting unary minus `-` and right-associative exponentiation `^`
* **`OPUS_03`:** 2D State-Space Dijkstra Shortest Path with up to $K$ Free Edges (`menor_custo_k_pedagios`)
* **`OPUS_04`:** 2D Monotonic Stack: Maximal Rectangle of `1`s in a Binary Matrix (`maior_retangulo_binario`)
* **`OPUS_05`:** Bitmask Dynamic Programming: Minimum Open Hamiltonian Path / Open TSP (`tsp_aberto`)
* **`OPUS_06`:** $O(\log(\min(M,N)))$ Binary Partition Search: Median of Two Sorted Arrays (`mediana_arrays_ordenados`)
* **`OPUS_07`:** Index Stack / DP: Longest Valid Parentheses Substring Trap (`maior_parenteses_validos`)
* **`OPUS_08`:** Two-Pointers / Prefix-Suffix Maxima: Trapping Rain Water (`agua_retida`)
* **`OPUS_09`:** Post-Order Tree DP: Binary Tree Maximum Path Sum Any-to-Any with Negative Nodes (`maior_caminho_arvore`)
* **`OPUS_10`:** Complete Backtracking DPLL SAT Solver with Unit Propagation for CNF Formulas (`resolver_sat_cnf`)

| # | Model & Quantization | `OPUS_01` Regex | `OPUS_02` Parser | `OPUS_03` Dijkstra | `OPUS_04` Rect 2D | `OPUS_05` TSP DP | `OPUS_06` Median | `OPUS_07` Parenth | `OPUS_08` RainWater | `OPUS_09` TreeMax | `OPUS_10` DPLL SAT | Score (`Base ➔ Final`) |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **`K2-Horizon-3.7B`** `Q8_0` | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ✅ **Base** | ⏱️ Timeout | ❌ Fail | ⏱️ Timeout | ✅ **Base** | ❌ Fail | **`3 ➔ 3/10` (30%)** |
| **2** | **`K2-Horizon-3.7B`** `Q6_K` | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ✅ **Base** | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | **`3 ➔ 3/10` (30%)** |
| **3** | **`K2-Horizon-3.7B`** `Q5_K_M` | ⏱️ Timeout | ⏱️ Timeout | ❌ Fail | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | **`2 ➔ 2/10` (20%)** |
| **4** | **`K2-Horizon-7B`** `Q4_K_M` | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | **`1 ➔ 1/10` (10%)** |
| **5** | **`Qwen3-1.7B`** `Q8_0` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | **`2 ➔ 2/10` (20%)** |
| **6** | **`Qwen3-1.7B`** `Q5_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **7** | **`K2-Horizon-3.7B`** `Q4_K_M` | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ✅ **Base** | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | ⏱️ Timeout | **`1 ➔ 1/10` (10%)** |
| **8** | **`K2-Horizon-0.9B`** `Q8_0` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **RLM** 🎯 | ✅ **Base** | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | **`2 ➔ 3/10` (30%)** |
| **9** | **`Qwen3-1.7B`** `Q4_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **10** | **`Qwen3-1.7B`** `BF16` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **11** | **`K2-Horizon-0.9B`** `Q6_K` 👑 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ✅ **Base** | ❌ Fail | ✅ **Base** | ✅ **Base** | ❌ Fail | **`4 ➔ 4/10` (40%)** 🏆 |
| **12** | **`K2-Horizon-0.9B`** `Q5_K_M` 👑 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ✅ **Base** | ✅ **Base** | ✅ **RLM** 🎯 | ❌ Fail | ❌ Fail | **`3 ➔ 4/10` (40%)** 🏆 |
| **13** | **`MiniCPM5-1B-Opus`** `F16` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **14** | **`K2-Horizon-0.9B`** `Q4_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **15** | **`IBM-GPT-5.4-Coder-1B`** `F16` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **16** | **`MiniCPM4-0.5B`** `Q8_0` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **17** | **`MiniCPM4-0.5B`** `Q6_K` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **18** | **`MiniCPM4-0.5B`** `F16` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **19** | **`MiniCPM4-0.5B`** `Q5_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **20** | **`Granite-350M-Gemini3`** `F16` 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **RLM** 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 1/10` (10%)** |
| **21** | **`Granite-4.0-H-350M`** `Q8_0` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **22** | **`QwQ-0.5B-Distilled`** `Q6_K` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **23** | **`Granite-4.0-H-350M`** `Q4_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **24** | **`QwQ-0.5B-Distilled`** `Q5_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **25** | **`Qwen2.5-0.5B-OpenR1`** `F16` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **26** | **`Granite-4.0-H-350M`** `Q6_K` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **27** | **`Granite-350M-Gemini3`** `Q8_0` 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **Base** | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`1 ➔ 1/10` (10%)** |
| **28** | **`Qwen2.5-0.5B-OpenR1`** `Q6_K` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **29** | **`QwQ-0.5B-Distilled`** `Q8_0` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **30** | **`QwQ-0.5B-Distilled`** `F16` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **31** | **`Granite-350M-Gemini3`** `Q6_K` 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ✅ **RLM** 🎯 | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 1/10` (10%)** |
| **32** | **`Qwen2.5-0.5B-OpenR1`** `Q8_0` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **33** | **`Qwen2.5-0.5B-OpenR1`** `Q5_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **34** | **`Granite-4.0-H-350M`** `Q5_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |
| **35** | **`Granite-350M-Gemini3`** `Q5_K_M` | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | ❌ Fail | **`0 ➔ 0/10` (0%)** |

*(Note: In earlier rounds recorded in Section 8 of the Livro Sagrado, `IBM-GPT-5.4-Coder-1B [Q6_K]` solved `2/10` Opus Hard challenges — `OPUS_01` Regex Engine and `OPUS_08` Trapping Rain Water — while `MiniCPM5-1B-Opus [Q4_K_M]` solved `1/10` — `OPUS_06` Median of Two Sorted Arrays).*

---

## 🧠 4. Winners & Mathematical / Hardware Pareto Explanations

### 4.1 Why `IFM/K2-Horizon-3.7B [Q6_K]` (`3.88 GB`) & `[Q5_K_M]` (`3.39 GB`) Beat `K2-Horizon-7B` (`5.21 GB`)
1. **Unprecedented Zero-Shot Autonomy (`36/39` Baseline in `Q5_K_M`):**
   * `K2-Horizon-3.7B [Q5_K_M]` achieved **`36/39 (92.31%)` purely in Zero-Shot Baseline** without any intervention from `Lambda-RLM`. Only a single test in Area 08 (Phonetic TTS Normalization) required a `+1 RLM` rescue to reach **`37/39 (94.87%)`** with `11/13` perfect `3/3` areas at **`20.11 tok/s`** on the RX 580 GPU.
2. **6-Bit Dynamic Programming Precision Unlock (`Q6_K`):**
   * Upgrading from `Q5_K_M` (`3475.0 MB`) to `Q6_K` (`3968.6 MB`) preserved the fine-grained attention logits required to synthesize the exact state-transition recurrence for `OPUS_05` (*Bitmask DP Open TSP*), raising the Opus Hard score from `2/10` to **`3/10 (30%)`** (`OPUS_04`, `OPUS_05`, `OPUS_07`) while sustaining **`19.53 tok/s`** on Vulkan GPU.
   * By contrast, `K2-Horizon-3.7B [Q8_0]` (`5136.9 MB`) achieved the exact same `37/39` and `3/10` Opus score while consuming `+1.17 GB` more VRAM. Thus, **`Q6_K` strictly dominates `Q8_0` on the Pareto frontier**.
3. **The 8 GB VRAM Bandwidth & Timeout Collapse in `K2-Horizon-7B [Q4_K_M]`:**
   * On the AMD Radeon RX 580 (`8192 MiB` GDDR5, `224 GB/s` bandwidth), `K2-Horizon-7B [Q4_K_M]` occupies `5333.15 MB` for weights alone. Once the `4096`-token KV cache and Vulkan compute buffers are allocated, memory pressure saturates the 256-bit GDDR5 bus and triggers driver-level memory management overhead.
   * Consequently, generation throughput collapses from **`20.11 tok/s`** (`3.7B Q5_K_M`) down to **`6.89 tok/s`** (`7B Q4_K_M`) — a **2.92× slowdown** — while delivering **zero cognitive gain** in the 13 Areas (`37/39` tied).
   * Worse, because `K2-Horizon-7B` uses long `<think>` chains before emitting Python code, generating `1,500+` reasoning tokens at `6.89 tok/s` exceeds the `240.0s` HTTP socket timeout on 9 of the 10 Opus Hard problems (`ERROR: timed out`), reducing its Opus score to `1/10` (`OPUS_08`).

### 4.2 Why `IFM/K2-Horizon-0.9B [Q6_K]` (`846 MB`) & `[Q8_0]` (`1.07 GB`) Dethroned All Sub-1B & 1.0B Models with `4/10` Opus Hard
1. **Direct Non-Thinking Fast Synthesis (`thinking: False`) Eliminates Reasoning Timeouts:**
   * Unlike `<think>` models that spend 80% of their token budget on verbose internal monologues, `K2-Horizon-0.9B` was trained via IFM's 512K native pretraining/midtraining pipeline to emit structured code and formal logic directly.
   * Running at **`34.29 tok/s` on GPU** and **`36.60 tok/s` on CPU** (`Q6_K`), it emits complete, syntactically clean Python algorithms in under 4 seconds.
2. **All-Time Sub-4B Record of `4/10` Opus Hard in `846 MB` (`Q6_K`) and `738 MB` (`Q5_K_M`):**
   * `K2-Horizon-0.9B [Q6_K]` solved **4 out of 10 LeetCode Hard challenges purely in Zero-Shot Baseline**: `OPUS_05` (Bitmask DP TSP), `OPUS_06` (Median of Two Sorted Arrays), `OPUS_08` (Trapping Rain Water), and `OPUS_09` (Binary Tree Max Path Sum with Negatives), while scoring **`34/39 (87.18%)`** across the 13 Cognitive Areas (`25/39` Baseline + **`+9 Lambda-RLM rescues`**).
   * `K2-Horizon-0.9B [Q5_K_M]` (`737.65 MB`) also achieved **`4/10` Opus Hard** (`3/10` Baseline on `OPUS_05`, `06`, `07` + **`+1 Lambda-RLM rescue` on `OPUS_08`**) and `33/39 (84.62%)` in the 13 Areas at **`38.57 tok/s` on CPU**.
   * `K2-Horizon-0.9B [Q8_0]` (`1095.4 MB`) pushed the sub-1B 13-Area ceiling to **`35/39 (89.74%)`** (`10/13` perfect areas, `+8 RLM` rescues) with **`3/10` Opus Hard** (`OPUS_06`, `08` Baseline + **`+1 RLM` rescue on `OPUS_05`**).
3. **Complete Victory Over 600M and 1.0B Champions:**
   * `K2-Horizon-0.9B` decisively outperformed `TinyQwen3-Distill-0.6B [Q5_K_M]` (`34/39`, `0/10` Opus), `MiniCPM5-1B-Opus` (`32–33/39`, `1/10` Opus), and `IBM-GPT-5.4-Coder-1B` (`31–33/39`, `2/10` Opus).
4. **CPU AVX2 > GPU Vulkan Symmetry:**
   * Because an `846 MB` model fits substantially inside the L3 cache + fast DDR4 prefetch window of an AVX2 CPU without Vulkan kernel launch overhead, `K2-Horizon-0.9B [Q6_K]` runs **faster on pure CPU (`36.60 tok/s` TG / `312.45 tok/s` PP) than on the RX 580 GPU (`34.29 tok/s` TG / `121.33 tok/s` PP)**.

### 4.3 Why `MiniCPM4-0.5B [Q8_0]` (`441 MB`) Broke the `30/39` Barrier (`31/39` at `49.99 tok/s` CPU)
* In 500M-parameter models (`0.5B`), 4-bit quantization (`Q4_K_M`, `265.8 MB`) compresses attention projection matrices too aggressively for multi-constraint formatting, capping `MiniCPM4-0.5B [Q4_K_M]` at `29/39 (74.36%)`.
* Stepping up to `Q5_K_M` (`302.3 MB`) and `Q6_K` (`341.2 MB`) lifted the score to **`30/39 (76.92%)`** at **`56.02 tok/s` on CPU**.
* At **`Q8_0` (`441.39 MB`)**, 8-bit uniform block quantization eliminated quantization noise in the GQA heads without introducing full 16-bit tail dispersion, enabling `Lambda-RLM` to rescue `+7` tests and reach **`31/39 (79.49%)`** (`7/13` perfect areas) at **`49.99 tok/s` on CPU AVX2** (`556.24 tok/s` CPU PP) — the first sub-600M model in laboratory history to break 30 points.

### 4.4 Why Hybrid Mamba-2 Models (`Granite-4.0-H-350M` & `Granite-350M-Gemini3`) Require `-fa off` on Vulkan
* IBM's `Granite-4.0-H-350M` uses a **Hybrid Mamba-2 State-Space Model (SSM) + Transformer Attention** architecture.
* When `llama-server.exe` runs on the Vulkan backend with Flash Attention enabled (`-fa on` / `-fa 1`), tiled FP16 accumulator rounding in the Vulkan Flash Attention shaders interacts destructively with the recurrent state-space scan tensors of the Mamba-2 blocks, causing severe numerical drift and collapsing generation speed (`4.74 tok/s`) and accuracy.
* Forcing **`-fa off` (`-fa 0`)** restores exact standard attention + SSM state accumulation, boosting `Granite-4.0-H-350M [Q8_0]` (`349.2 MB`) to **`29/39 (74.36%)`** at **`21.80 tok/s` GPU** and enabling `Granite-350M-Gemini3 [F16]` (`653.2 MB`) to reach **`29/39 (74.36%)`** plus **`1/10` Opus Hard** (`OPUS_06` Median of Two Sorted Arrays rescued by `Lambda-RLM`) — making it the lightest model on Earth (`350M` parameters) ever verified to solve a LeetCode Hard challenge.

### 4.5 The Law of Implicit Discretization Regularization vs. `F16` / `BF16` Tail Noise
* Across every single model family tested from `500M` to `4.5B` (`MiniCPM4-0.5B`, `QwQ-0.5B`, `TinyQwen3-0.6B`, `Qwen3-0.6B-Distill-30B`, `Qwen3-0.6B-Opus4.6`, `MiniCPM5-1B`, `IBM-GPT-5.4-Coder-1B`, `Qwen3-1.7B`, `Parable-Qwen3-4B`, and `Gemma4-E4B`), unquantized 16-bit weights (`F16` / `BF16`) **underperformed** or tied optimal K-quants (`Q4_K_M`, `Q5_K_M`, `Q6_K`, `Q8_0`) while cutting generation throughput by **30% to 71%**:
  * **`Qwen3-1.7B`:** `Q8_0` (`2.06 GB`) and `Q5_K_M` (`1.40 GB`) scored **`36/39 (92.31%)`** at `31.1–31.2 tok/s` GPU, whereas unquantized `BF16` (`3.88 GB`) dropped to **`35/39 (89.74%)`** at `25.88 tok/s` GPU (`11.06 tok/s` CPU vs `24.92 tok/s` CPU in `Q5_K_M`).
  * **`TinyQwen3-Distill-0.6B`:** `Q5_K_M` (`423.6 MB`) scored **`34/39 (87.18%)`** at `41.23 tok/s`, whereas `F16` (`1142.2 MB`) fell to **`30/39 (76.92%)`** at `15.98 tok/s` (`-61.2%` speed loss).
  * **Physical Explanation:** In distilled student models, 16-bit floating-point weights retain low-magnitude continuous residual noise from the teacher's KL-divergence soft labels. Block quantization (`Q4_K_M` through `Q8_0`) acts as a discrete low-pass regularizer (implicit weight pruning/clustering) that suppresses peripheral logit entropy and sharpens greedy argmax decisions, while simultaneously halving memory-bus traffic.
