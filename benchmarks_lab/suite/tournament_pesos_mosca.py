# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO COMPLETO DOS PESOS-MOSCA (350M / 500M / 1.0B / 1.7B)
Fechamento 100% da Malha de Quantizacao Q4_K_M a F16/BF16 sob Lambda-RLM
Comandante Primario: Mestre Ruan

26 Variantes 100% Verificadas via Hugging Face API (HTTP 200):
  - Faixa 350M (8):
      * ibm-granite/granite-4.0-h-350m (Q4_K_M, Q5_K_M, Q6_K, Q8_0) [BF16 ja homologado]
      * glogwa68/granite-4.0-h-350m-DISTILL-gemini-think (Q5_K_M, Q6_K, Q8_0, F16) [Q4_K_M ja homologado]
  - Faixa 500M (12):
      * MiniCPM4-0.5B (Q5_K_M, Q6_K, Q8_0, F16) [Q4_K_M ja homologado]
      * QwQ-0.5B-Distilled-SFT (Q5_K_M, Q6_K, Q8_0, F16) [Q4_K_M ja homologado]
      * Qwen2.5-0.5B-Open-R1-Distill (Q5_K_M, Q6_K, Q8_0, F16) [Q4_K_M ja homologado]
  - Faixa 1.0B a 1.7B (6):
      * MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic (F16) [Q4..Q8 ja homologados]
      * IBM-GPT-5.4-Coder-1B (F16) [Q4..Q8 ja homologados]
      * bartowski/Qwen_Qwen3-1.7B (Q4_K_M, Q5_K_M, Q8_0, BF16) [Q6_K ja homologado]
"""

import os
import re
import sys
import time
import json
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, Any

sys.stdout.reconfigure(encoding="utf-8")

# Verificacao obrigatoria de dependencias antes de rodar (anti-falha silenciosa do Lambda-RLM)
for _pkg in ("openai", "dotenv", "rich", "pytest", "pydantic"):
    __import__(_pkg)

ROTOR_ROOT = Path(r"F:\rotor-llm")
LAMBDA_RLM_DIR = ROTOR_ROOT / "lambda_rlm"
for _p in (str(ROTOR_ROOT), str(LAMBDA_RLM_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from benchmark_13_areas_39_testes import BENCHMARK_SUITE
from duelo_nivel_opus_8b_vs_9b import OPUS_10_TESTS
from router.formal_verifier import formal_verifier
from rlm import LambdaRLM

SERVER_BIN = r"F:\AetherMind_LLM\bin\llama-server.exe"
BENCH_BIN  = r"F:\AetherMind_LLM\bin\llama-bench.exe"
PORT       = 8089
BASE_URL   = f"http://127.0.0.1:{PORT}"

MODELS_DIR = Path(r"F:\models\pesos_mosca")
PROOF_FILE = Path(r"F:\data\proof_pesos_mosca_completo.json")
LOG_FILE   = Path(r"F:\data\tournament_pesos_mosca_completo.log")
SERVER_LOG = Path(r"F:\data\llama_server_pesos_mosca_completo.log")

HF = "https://huggingface.co"

# fa_off=True para arquiteturas Granite Hybrid Mamba-2 (evita degradacao numerica em Vulkan FA)
# thinking=True para modelos com raciocinio <think> (da orcamento maior de tokens em codigo/Opus)
CHALLENGERS = [
    # ─────────────────────────── FAIXA 350M (8) ───────────────────────────
    {
        "id": "granite_h_350m__q4_k_m",
        "champ": "ibm-granite/granite-4.0-h-350m",
        "champ_short": "Granite-4.0-H-350M",
        "tier": "350M", "params": "350M",
        "teacher": "IBM Granite 4.0 Hybrid Base",
        "quant": "Q4_K_M", "fa_off": True, "thinking": False,
        "filename": "granite-4.0-h-350m-Q4_K_M.gguf",
        "url": f"{HF}/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q4_K_M.gguf",
    },
    {
        "id": "granite_h_350m__q5_k_m",
        "champ": "ibm-granite/granite-4.0-h-350m",
        "champ_short": "Granite-4.0-H-350M",
        "tier": "350M", "params": "350M",
        "teacher": "IBM Granite 4.0 Hybrid Base",
        "quant": "Q5_K_M", "fa_off": True, "thinking": False,
        "filename": "granite-4.0-h-350m-Q5_K_M.gguf",
        "url": f"{HF}/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q5_K_M.gguf",
    },
    {
        "id": "granite_h_350m__q6_k",
        "champ": "ibm-granite/granite-4.0-h-350m",
        "champ_short": "Granite-4.0-H-350M",
        "tier": "350M", "params": "350M",
        "teacher": "IBM Granite 4.0 Hybrid Base",
        "quant": "Q6_K", "fa_off": True, "thinking": False,
        "filename": "granite-4.0-h-350m-Q6_K.gguf",
        "url": f"{HF}/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q6_K.gguf",
    },
    {
        "id": "granite_h_350m__q8_0",
        "champ": "ibm-granite/granite-4.0-h-350m",
        "champ_short": "Granite-4.0-H-350M",
        "tier": "350M", "params": "350M",
        "teacher": "IBM Granite 4.0 Hybrid Base",
        "quant": "Q8_0", "fa_off": True, "thinking": False,
        "filename": "granite-4.0-h-350m-Q8_0.gguf",
        "url": f"{HF}/ibm-granite/granite-4.0-h-350m-GGUF/resolve/main/granite-4.0-h-350m-Q8_0.gguf",
    },
    {
        "id": "granite_gemini3_350m__q5_k_m",
        "champ": "glogwa68/granite-4.0-h-350m-DISTILL-gemini-think",
        "champ_short": "Granite-350M-Gemini3",
        "tier": "350M", "params": "350M",
        "teacher": "Google Gemini 3 Pro Thinking",
        "quant": "Q5_K_M", "fa_off": True, "thinking": True,
        "filename": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf",
        "url": f"{HF}/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q5_k_m.gguf",
    },
    {
        "id": "granite_gemini3_350m__q6_k",
        "champ": "glogwa68/granite-4.0-h-350m-DISTILL-gemini-think",
        "champ_short": "Granite-350M-Gemini3",
        "tier": "350M", "params": "350M",
        "teacher": "Google Gemini 3 Pro Thinking",
        "quant": "Q6_K", "fa_off": True, "thinking": True,
        "filename": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf",
        "url": f"{HF}/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q6_k.gguf",
    },
    {
        "id": "granite_gemini3_350m__q8_0",
        "champ": "glogwa68/granite-4.0-h-350m-DISTILL-gemini-think",
        "champ_short": "Granite-350M-Gemini3",
        "tier": "350M", "params": "350M",
        "teacher": "Google Gemini 3 Pro Thinking",
        "quant": "Q8_0", "fa_off": True, "thinking": True,
        "filename": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf",
        "url": f"{HF}/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q8_0.gguf",
    },
    {
        "id": "granite_gemini3_350m__f16",
        "champ": "glogwa68/granite-4.0-h-350m-DISTILL-gemini-think",
        "champ_short": "Granite-350M-Gemini3",
        "tier": "350M", "params": "350M",
        "teacher": "Google Gemini 3 Pro Thinking",
        "quant": "F16", "fa_off": True, "thinking": True,
        "filename": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf",
        "url": f"{HF}/glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF/resolve/main/granite-4.0-h-350m-DISTILL-gemini-3-pro-think-f16.gguf",
    },

    # ─────────────────────────── FAIXA 500M (12) ───────────────────────────
    {
        "id": "minicpm4_05b__q5_k_m",
        "champ": "openbmb/MiniCPM4-0.5B",
        "champ_short": "MiniCPM4-0.5B",
        "tier": "500M", "params": "500M",
        "teacher": "OpenBMB MiniCPM4 Base",
        "quant": "Q5_K_M", "fa_off": False, "thinking": False,
        "filename": "MiniCPM4-0.5B.Q5_K_M.gguf",
        "url": f"{HF}/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q5_K_M.gguf",
    },
    {
        "id": "minicpm4_05b__q6_k",
        "champ": "openbmb/MiniCPM4-0.5B",
        "champ_short": "MiniCPM4-0.5B",
        "tier": "500M", "params": "500M",
        "teacher": "OpenBMB MiniCPM4 Base",
        "quant": "Q6_K", "fa_off": False, "thinking": False,
        "filename": "MiniCPM4-0.5B.Q6_K.gguf",
        "url": f"{HF}/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q6_K.gguf",
    },
    {
        "id": "minicpm4_05b__q8_0",
        "champ": "openbmb/MiniCPM4-0.5B",
        "champ_short": "MiniCPM4-0.5B",
        "tier": "500M", "params": "500M",
        "teacher": "OpenBMB MiniCPM4 Base",
        "quant": "Q8_0", "fa_off": False, "thinking": False,
        "filename": "MiniCPM4-0.5B.Q8_0.gguf",
        "url": f"{HF}/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.Q8_0.gguf",
    },
    {
        "id": "minicpm4_05b__f16",
        "champ": "openbmb/MiniCPM4-0.5B",
        "champ_short": "MiniCPM4-0.5B",
        "tier": "500M", "params": "500M",
        "teacher": "OpenBMB MiniCPM4 Base",
        "quant": "F16", "fa_off": False, "thinking": False,
        "filename": "MiniCPM4-0.5B.f16.gguf",
        "url": f"{HF}/mradermacher/MiniCPM4-0.5B-GGUF/resolve/main/MiniCPM4-0.5B.f16.gguf",
    },
    {
        "id": "qwq_05b_distilled__q5_k_m",
        "champ": "mradermacher/QwQ-0.5B-Distilled-SFT",
        "champ_short": "QwQ-0.5B-Distilled",
        "tier": "500M", "params": "500M",
        "teacher": "Alibaba QwQ / OpenAI o1 SFT",
        "quant": "Q5_K_M", "fa_off": False, "thinking": True,
        "filename": "QwQ-0.5B-Distilled-SFT.Q5_K_M.gguf",
        "url": f"{HF}/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q5_K_M.gguf",
    },
    {
        "id": "qwq_05b_distilled__q6_k",
        "champ": "mradermacher/QwQ-0.5B-Distilled-SFT",
        "champ_short": "QwQ-0.5B-Distilled",
        "tier": "500M", "params": "500M",
        "teacher": "Alibaba QwQ / OpenAI o1 SFT",
        "quant": "Q6_K", "fa_off": False, "thinking": True,
        "filename": "QwQ-0.5B-Distilled-SFT.Q6_K.gguf",
        "url": f"{HF}/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q6_K.gguf",
    },
    {
        "id": "qwq_05b_distilled__q8_0",
        "champ": "mradermacher/QwQ-0.5B-Distilled-SFT",
        "champ_short": "QwQ-0.5B-Distilled",
        "tier": "500M", "params": "500M",
        "teacher": "Alibaba QwQ / OpenAI o1 SFT",
        "quant": "Q8_0", "fa_off": False, "thinking": True,
        "filename": "QwQ-0.5B-Distilled-SFT.Q8_0.gguf",
        "url": f"{HF}/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.Q8_0.gguf",
    },
    {
        "id": "qwq_05b_distilled__f16",
        "champ": "mradermacher/QwQ-0.5B-Distilled-SFT",
        "champ_short": "QwQ-0.5B-Distilled",
        "tier": "500M", "params": "500M",
        "teacher": "Alibaba QwQ / OpenAI o1 SFT",
        "quant": "F16", "fa_off": False, "thinking": True,
        "filename": "QwQ-0.5B-Distilled-SFT.f16.gguf",
        "url": f"{HF}/mradermacher/QwQ-0.5B-Distilled-SFT-GGUF/resolve/main/QwQ-0.5B-Distilled-SFT.f16.gguf",
    },
    {
        "id": "qwen25_05b_openr1__q5_k_m",
        "champ": "Alcoft/Qwen2.5-0.5B-Open-R1-Distill",
        "champ_short": "Qwen2.5-0.5B-OpenR1",
        "tier": "500M", "params": "500M",
        "teacher": "DeepSeek-R1 Distill",
        "quant": "Q5_K_M", "fa_off": False, "thinking": True,
        "filename": "Qwen2.5-0.5B-Open-R1-Distill_Q5_K_M.gguf",
        "url": f"{HF}/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q5_K_M.gguf",
    },
    {
        "id": "qwen25_05b_openr1__q6_k",
        "champ": "Alcoft/Qwen2.5-0.5B-Open-R1-Distill",
        "champ_short": "Qwen2.5-0.5B-OpenR1",
        "tier": "500M", "params": "500M",
        "teacher": "DeepSeek-R1 Distill",
        "quant": "Q6_K", "fa_off": False, "thinking": True,
        "filename": "Qwen2.5-0.5B-Open-R1-Distill_Q6_K.gguf",
        "url": f"{HF}/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q6_K.gguf",
    },
    {
        "id": "qwen25_05b_openr1__q8_0",
        "champ": "Alcoft/Qwen2.5-0.5B-Open-R1-Distill",
        "champ_short": "Qwen2.5-0.5B-OpenR1",
        "tier": "500M", "params": "500M",
        "teacher": "DeepSeek-R1 Distill",
        "quant": "Q8_0", "fa_off": False, "thinking": True,
        "filename": "Qwen2.5-0.5B-Open-R1-Distill_Q8_0.gguf",
        "url": f"{HF}/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_Q8_0.gguf",
    },
    {
        "id": "qwen25_05b_openr1__f16",
        "champ": "Alcoft/Qwen2.5-0.5B-Open-R1-Distill",
        "champ_short": "Qwen2.5-0.5B-OpenR1",
        "tier": "500M", "params": "500M",
        "teacher": "DeepSeek-R1 Distill",
        "quant": "F16", "fa_off": False, "thinking": True,
        "filename": "Qwen2.5-0.5B-Open-R1-Distill_f16.gguf",
        "url": f"{HF}/Alcoft/Qwen2.5-0.5B-Open-R1-Distill-GGUF/resolve/main/Qwen2.5-0.5B-Open-R1-Distill_f16.gguf",
    },

    # ─────────────────────────── FAIXA 1.0B - 1.7B (6) ───────────────────────────
    {
        "id": "minicpm5_1b_opus__f16",
        "champ": "mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic",
        "champ_short": "MiniCPM5-1B-Opus",
        "tier": "1.0B", "params": "1.0B",
        "teacher": "Claude Opus + Fable 5 V2 Thinking",
        "quant": "F16", "fa_off": False, "thinking": True,
        "filename": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf",
        "url": f"{HF}/mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF/resolve/main/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.f16.gguf",
    },
    {
        "id": "ibm_gpt54_coder_1b__f16",
        "champ": "mradermacher/IBM-GPT-5.4-Coder-1B",
        "champ_short": "IBM-GPT-5.4-Coder-1B",
        "tier": "1.0B", "params": "1.0B",
        "teacher": "OpenAI GPT-5.4 Coder",
        "quant": "F16", "fa_off": True, "thinking": False,
        "filename": "IBM-GPT-5.4-Coder-1B.f16.gguf",
        "url": f"{HF}/mradermacher/IBM-GPT-5.4-Coder-1B-GGUF/resolve/main/IBM-GPT-5.4-Coder-1B.f16.gguf",
    },
    {
        "id": "qwen3_1_7b__q4_k_m",
        "champ": "bartowski/Qwen_Qwen3-1.7B-GGUF",
        "champ_short": "Qwen3-1.7B",
        "tier": "1.7B", "params": "1.7B",
        "teacher": "Qwen3 Native Thinking (bartowski)",
        "quant": "Q4_K_M", "fa_off": False, "thinking": True,
        "filename": "Qwen_Qwen3-1.7B-Q4_K_M.gguf",
        "url": f"{HF}/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf",
    },
    {
        "id": "qwen3_1_7b__q5_k_m",
        "champ": "bartowski/Qwen_Qwen3-1.7B-GGUF",
        "champ_short": "Qwen3-1.7B",
        "tier": "1.7B", "params": "1.7B",
        "teacher": "Qwen3 Native Thinking (bartowski)",
        "quant": "Q5_K_M", "fa_off": False, "thinking": True,
        "filename": "Qwen_Qwen3-1.7B-Q5_K_M.gguf",
        "url": f"{HF}/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q5_K_M.gguf",
    },
    {
        "id": "qwen3_1_7b__q8_0",
        "champ": "bartowski/Qwen_Qwen3-1.7B-GGUF",
        "champ_short": "Qwen3-1.7B",
        "tier": "1.7B", "params": "1.7B",
        "teacher": "Qwen3 Native Thinking (bartowski)",
        "quant": "Q8_0", "fa_off": False, "thinking": True,
        "filename": "Qwen_Qwen3-1.7B-Q8_0.gguf",
        "url": f"{HF}/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q8_0.gguf",
    },
    {
        "id": "qwen3_1_7b__bf16",
        "champ": "bartowski/Qwen_Qwen3-1.7B-GGUF",
        "champ_short": "Qwen3-1.7B",
        "tier": "1.7B", "params": "1.7B",
        "teacher": "Qwen3 Native Thinking (bartowski)",
        "quant": "BF16", "fa_off": False, "thinking": True,
        "filename": "Qwen_Qwen3-1.7B-bf16.gguf",
        "url": f"{HF}/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-bf16.gguf",
    },
]


def log(msg: str):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def kill_llama():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], capture_output=True, timeout=8)
        time.sleep(0.8)
    except Exception:
        pass


def download_if_needed(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 100 * 1024 * 1024:
        log(f"[+] Ja presente em disco: {dest.name} ({dest.stat().st_size / 1024**2:.1f} MB)")
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(".gguf.part")
    log(f"[*] Baixando {dest.name} ...")
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded, last_pct = 0, -1
            with open(part, "wb") as out:
                while True:
                    chunk = resp.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    out.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = int(downloaded / total * 100)
                        if pct >= last_pct + 20:
                            last_pct = pct
                            mb_s = (downloaded / 1024**2) / max(0.1, time.time() - t0)
                            log(f"    -> {pct}% ({downloaded/1024**2:.0f}/{total/1024**2:.0f} MB) @ {mb_s:.1f} MB/s")
        if dest.exists():
            dest.unlink()
        part.rename(dest)
        log(f"[+] Download OK: {dest.name} ({dest.stat().st_size/1024**2:.1f} MB) em {time.time()-t0:.1f}s")
        return True
    except Exception as e:
        log(f"[!] Falha no download de {dest.name}: {e}")
        if part.exists():
            part.unlink()
        return False


def benchmark_cpu_speed(model_path: Path, fa_off: bool = False) -> Dict[str, float]:
    kill_llama()
    log(f"  [*] Medindo throughput CPU puro (Xeon AVX2 -t 14) via llama-bench: {model_path.name}...")
    cmd = [
        BENCH_BIN,
        "-m", str(model_path),
        "-ngl", "0",
        "-t", "14",
        "-fa", "0" if fa_off else "1",
        "-p", "256",
        "-n", "64",
        "-r", "1",
        "-o", "json",
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if res.returncode == 0 and res.stdout.strip():
            rows = json.loads(res.stdout)
            cpu_pp, cpu_tg = 0.0, 0.0
            for r in rows:
                if r.get("n_prompt", 0) > 0:
                    cpu_pp = round(float(r.get("avg_ts", 0.0)), 2)
                elif r.get("n_gen", 0) > 0:
                    cpu_tg = round(float(r.get("avg_ts", 0.0)), 2)
            log(f"   [CPU AVX2 PROOF] PP: {cpu_pp:.2f} tok/s | TG: {cpu_tg:.2f} tok/s")
            return {"cpu_pp_tok_s": cpu_pp, "cpu_tg_tok_s": cpu_tg}
    except Exception as e:
        log(f"   [!] Aviso benchmark CPU: {e}")
    return {"cpu_pp_tok_s": 0.0, "cpu_tg_tok_s": 0.0}


def start_llama_server(model_path: Path, fa_off: bool = False) -> tuple[subprocess.Popen, float, int]:
    kill_llama()
    fa_mode = "off" if fa_off else "on"
    ngl_candidates = [99, 0]

    for ngl in ngl_candidates:
        kill_llama()
        log(f"[*] Subindo llama-server b12420 (-ngl {ngl} | -fa {fa_mode} | -t 14): {model_path.name}...")
        log_fp = open(SERVER_LOG, "a", encoding="utf-8")
        cmd = [
            SERVER_BIN,
            "-m", str(model_path),
            "-c", "4096",
            "-np", "1",
            "-fa", fa_mode,
            "-ngl", str(ngl),
            "-b", "512",
            "-ub", "512",
            "-t", "14",
            "--port", str(PORT),
            "--host", "127.0.0.1",
            "--cont-batching",
        ]
        p = subprocess.Popen(cmd, stdout=log_fp, stderr=subprocess.STDOUT, creationflags=0x00004000)
        t0 = time.time()
        ready = False
        while time.time() - t0 < 120.0:
            if p.poll() is not None:
                log(f"[!] llama-server (-ngl {ngl}) encerrou (codigo {p.returncode}). Tentando fallback...")
                break
            try:
                with urllib.request.urlopen(f"{BASE_URL}/health", timeout=2.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.4)
        if ready:
            boot_s = round(time.time() - t0, 2)
            log(f"[+] Servidor 200 OK (-ngl {ngl} | -fa {fa_mode}) em {boot_s}s!")
            return p, boot_s, ngl
        kill_llama()

    raise RuntimeError(f"Falha ao subir llama-server para {model_path.name}")


def benchmark_speed(boot_s: float) -> Dict[str, float]:
    log("  [*] Medindo throughput GPU bare-metal (PP e TG tok/s)...")
    payload = json.dumps({
        "prompt": "Explique a diferenca entre um compilador e um interpretador em computacao de alta performance.",
        "n_predict": 96,
        "temperature": 0.0,
        "ignore_eos": True,
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=90.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = max(0.01, time.time() - t0)
            timings = data.get("timings", {})
            pp = float(timings.get("prompt_per_second", 0.0))
            tg = float(timings.get("predicted_per_second", 0.0))
            if tg <= 0.0 or tg > 5000.0:
                pred_ms = float(timings.get("predicted_ms", 0.0))
                pred_n = float(timings.get("predicted_n", 96))
                tg = (pred_n / (pred_ms / 1000.0)) if pred_ms > 1.0 else (96.0 / elapsed)
            log(f"   [GPU SPEED PROOF] Boot: {boot_s}s | PP: {pp:.2f} tok/s | TG: {tg:.2f} tok/s")
            return {"boot_seconds": boot_s, "prompt_per_second": round(pp, 2), "predicted_per_second": round(tg, 2)}
    except Exception as e:
        log(f"   [!] Erro benchmark GPU: {e}")
        return {"boot_seconds": boot_s, "prompt_per_second": 0.0, "predicted_per_second": 0.0}


def extract_text_after_think(text: str) -> str:
    if "</think>" in text:
        post = text.split("</think>", 1)[1].strip()
        if post:
            return post
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    if "<think>" in cleaned.lower():
        cleaned = re.sub(r"<think>", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else text.strip()


def clean_python_code(text: str) -> str:
    cleaned = extract_text_after_think(text)
    m = re.search(r"```(?:python)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if m:
        cleaned = m.group(1).strip()
    m_code = re.search(r"^(?:import|from|def|class)\s+", cleaned, re.MULTILINE)
    if m_code:
        cleaned = cleaned[m_code.start():]
    return cleaned.strip()


def query_fast_direct(prompt: str, is_code: bool = False, max_tokens: int = 768) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown." if is_code else clean

    payload = json.dumps({
        "messages": [{"role": "user", "content": eff_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=150.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if not content:
                content = (msg.get("reasoning_content") or "").strip()
            if content:
                return content
    except Exception:
        pass

    payload2 = json.dumps({
        "prompt": eff_prompt,
        "n_predict": max_tokens,
        "temperature": 0.0,
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=150.0) as r2:
            return json.loads(r2.read().decode("utf-8")).get("content", "").strip()
    except Exception:
        return ""


def query_lambda(lambda_engine: LambdaRLM, prompt: str, is_code: bool = False) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown." if is_code else clean
    try:
        res = lambda_engine.completion(eff_prompt)
        return (res.response or "").strip()
    except Exception as e:
        log(f"    [WARN LambdaRLM] {type(e).__name__}: {str(e)[:120]}")
        return ""


def run_13_areas(lambda_engine: LambdaRLM, thinking: bool) -> Dict[str, Any]:
    log("  [*] Bateria 13 Areas Cognitivas (39 testes: Baseline + Lambda-RLM)...")
    base_passed = 0
    rlm_passed = 0
    areas = {}
    perfect_count = 0

    tok_code = 1280 if thinking else 640
    tok_text = 768 if thinking else 448

    for i, area in enumerate(BENCHMARK_SUITE, 1):
        a_id = area.get("area_id", str(i))
        a_name = area.get("area_name", f"Area_{i}")
        a_base_pass = 0
        a_rlm_pass = 0
        for test in area["tests"]:
            p = test["prompt"]
            validator = test.get("verify") or test.get("validator")
            is_code = (test.get("schema_type") == "python_func" or "Escreva em Python" in p or "função `" in p)

            out = query_fast_direct(p, is_code=is_code, max_tokens=tok_code if is_code else tok_text)
            val_in = clean_python_code(out) if is_code else extract_text_after_think(out)
            ok_base = False
            try:
                ok_base = bool(validator(val_in))
            except Exception:
                try:
                    ok_base = bool(validator(out))
                except Exception:
                    ok_base = False

            if ok_base:
                a_base_pass += 1
                base_passed += 1
                a_rlm_pass += 1
                rlm_passed += 1
            else:
                out_l = query_lambda(lambda_engine, p, is_code=is_code)
                val_l = clean_python_code(out_l) if is_code else extract_text_after_think(out_l)
                ok_rlm = False
                try:
                    ok_rlm = bool(validator(val_l))
                except Exception:
                    try:
                        ok_rlm = bool(validator(out_l))
                    except Exception:
                        ok_rlm = False
                if ok_rlm:
                    a_rlm_pass += 1
                    rlm_passed += 1

        if a_rlm_pass == len(area["tests"]):
            perfect_count += 1
        areas[a_id] = {
            "name": a_name,
            "baseline_passed": a_base_pass,
            "passed": a_rlm_pass,
            "total": len(area["tests"]),
        }
        log(f"    -> {a_id:30s}: Baseline {a_base_pass}/3 | Lambda-RLM {a_rlm_pass}/3")

    base_pct = round((base_passed / 39) * 100, 2)
    rlm_pct  = round((rlm_passed / 39) * 100, 2)
    log(f"  [+] 13 Areas: Baseline {base_passed}/39 ({base_pct}%) -> Lambda-RLM {rlm_passed}/39 ({rlm_pct}%) | Gabaritos: {perfect_count}/13")
    return {
        "baseline_passed": base_passed,
        "baseline_pct": base_pct,
        "passed": rlm_passed,
        "total": 39,
        "pct": rlm_pct,
        "perfect_areas_count": perfect_count,
        "areas": areas,
    }


def run_opus(lambda_engine: LambdaRLM, thinking: bool) -> Dict[str, Any]:
    log("  [*] Bateria 10 Desafios Opus Hard (AST & pytest: Baseline + Lambda-RLM)...")
    base_passed = 0
    opus_passed = 0
    opus_details = {}
    tok_opus = 2048 if thinking else 1024

    for test in OPUS_10_TESTS:
        t_id = test["id"]
        t_name = test["name"]
        prompt = test["prompt"]
        assertions = test["assertions"]

        passed = False
        res_str = "FAIL"
        try:
            raw = query_fast_direct(prompt, is_code=True, max_tokens=tok_opus)
            code = clean_python_code(raw)
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=8.0)
            if ver.passed:
                passed = True
                base_passed += 1
                opus_passed += 1
                res_str = "PASS (Baseline)"
            else:
                retry_p = f"{prompt}\nATENCAO: A implementacao anterior falhou ({ver.details or 'erro'}). Escreva estritamente a funcao Python correta tratando todos os edge cases."
                raw_rlm = query_lambda(lambda_engine, retry_p, is_code=True)
                code_rlm = clean_python_code(raw_rlm)
                ver_rlm = formal_verifier.verify_python_code(code_rlm, assertions, timeout_s=8.0)
                if ver_rlm.passed:
                    passed = True
                    opus_passed += 1
                    res_str = "PASS (Lambda-RLM)"
                else:
                    res_str = f"FAIL ({(ver_rlm.details or 'assert')[:40]})"
        except Exception as e:
            res_str = f"ERROR: {str(e)[:40]}"

        opus_details[t_id] = {"name": t_name, "passed": passed, "result": res_str}
        log(f"    -> {t_id:38s}: {res_str}")

    opus_pct = round((opus_passed / 10) * 100, 2)
    log(f"  [+] Opus Hard: {opus_passed}/10 ({opus_pct}%) [Baseline: {base_passed}/10]")
    return {
        "baseline_passed": base_passed,
        "passed": opus_passed,
        "total": 10,
        "pct": opus_pct,
        "details": opus_details,
    }


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    log("=" * 80)
    log("AETHERMIND — TORNEIO COMPLETO PESOS-MOSCA (26 VARIANTES Q4_K_M A F16/BF16)")
    log(f"Python: {sys.executable} | Lambda-RLM + OpenAI VERIFICADOS")
    log("=" * 80)

    results = {}
    if PROOF_FILE.exists():
        try:
            results = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
            done_cnt = sum(1 for v in results.values() if v.get("completed"))
            log(f"[*] Historico carregado: {done_cnt}/{len(CHALLENGERS)} concluidos.")
        except Exception:
            results = {}

    for idx, c in enumerate(CHALLENGERS, 1):
        c_id = c["id"]
        c_name = f"{c['champ_short']} [{c['quant']}]"
        model_path = MODELS_DIR / c["filename"]

        log("\n" + "#" * 80)
        log(f"[{idx}/{len(CHALLENGERS)}] {c_name} ({c['tier']} | {c['teacher']})")
        log("#" * 80)

        if results.get(c_id, {}).get("completed"):
            prev = results[c_id]
            log(f"[+] Ja homologado: 13A {prev['score_13_areas']}/39 (Base {prev['baseline_13_areas']}) | Opus {prev['score_opus']}/10 | GPU {prev['tg_tok_s']} t/s. Pulando.")
            continue

        if not download_if_needed(c["url"], model_path):
            log(f"[!] Pulando {c_name} por erro de download.")
            continue

        proc = None
        try:
            size_mb = round(model_path.stat().st_size / (1024**2), 2)
            cpu_info = benchmark_cpu_speed(model_path, fa_off=c["fa_off"])
            proc, boot_s, active_ngl = start_llama_server(model_path, fa_off=c["fa_off"])
            gpu_info = benchmark_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model_path.name,
                    "base_url": f"{BASE_URL}/v1",
                    "api_key": "none",
                    "max_tokens": 1536 if c["thinking"] else 768,
                    "temperature": 0.0,
                    "timeout": 150.0,
                },
                environment="local",
                context_window_chars=40000,
                verbose=False,
            )

            res_13 = run_13_areas(lambda_engine, thinking=c["thinking"])
            res_opus = run_opus(lambda_engine, thinking=c["thinking"])

            results[c_id] = {
                "champ": c["champ"],
                "champ_short": c["champ_short"],
                "tier": c["tier"],
                "params": c["params"],
                "teacher": c["teacher"],
                "quant": c["quant"],
                "fa_mode": "off" if c["fa_off"] else "on",
                "thinking": c["thinking"],
                "size_mb": size_mb,
                "active_ngl": active_ngl,
                "boot_seconds": gpu_info["boot_seconds"],
                "pp_tok_s": gpu_info["prompt_per_second"],
                "tg_tok_s": gpu_info["predicted_per_second"],
                "cpu_pp_tok_s": cpu_info["cpu_pp_tok_s"],
                "cpu_tg_tok_s": cpu_info["cpu_tg_tok_s"],
                "score_13_areas": res_13["passed"],
                "baseline_13_areas": res_13["baseline_passed"],
                "pct_13_areas": res_13["pct"],
                "perfect_areas_count": res_13["perfect_areas_count"],
                "score_opus": res_opus["passed"],
                "baseline_opus": res_opus["baseline_passed"],
                "pct_opus": res_opus["pct"],
                "details_13_areas": res_13,
                "details_opus": res_opus,
                "completed": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            PROOF_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log(f"[+] PROVA SALVA ({sum(1 for v in results.values() if v.get('completed'))}/{len(CHALLENGERS)}): {c_name} -> 13A {res_13['passed']}/39 | Opus {res_opus['passed']}/10")

        except Exception as e:
            log(f"[!] ERRO critico em {c_name}: {e}")
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            kill_llama()
            # Libera espaco NVMe em F: apos prova gravada (mantem sempre >5 GB livres para F16/BF16)
            if results.get(c_id, {}).get("completed") and model_path.exists():
                try:
                    model_path.unlink()
                    log(f"    [CLEANUP] Removido {model_path.name} apos gravacao da prova.")
                except Exception as e:
                    log(f"    [WARN CLEANUP] {e}")
            time.sleep(0.8)

    done_total = sum(1 for v in results.values() if v.get("completed"))
    log("\n" + "=" * 80)
    log(f"[+] TORNEIO PESOS-MOSCA FINALIZADO: {done_total}/{len(CHALLENGERS)} VARIANTES HOMOLOGADAS!")
    log("=" * 80)


if __name__ == "__main__":
    main()
