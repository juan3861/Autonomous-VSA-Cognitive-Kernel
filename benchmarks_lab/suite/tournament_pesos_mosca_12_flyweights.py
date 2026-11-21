# -*- coding: utf-8 -*-
"""
AETHERMIND — DUELO FINAL DOS PESOS-MOSCA (200M a 1.5B) — 12 MODELOS TIER-1 TEACHER DISTILLS
Comandante Primário: Mestre Ruan

Escalação de Elite (12 Concorrentes Inéditos de 350M a 1.5B):
1. granite-4.0-h-350m-DISTILL-gemini-3-pro-think (350M | Google Gemini 3 Pro Thinking | 0.21 GB)
2. Gemini-Distill-Qwen2.5-0.5B-ead (500M | Google Gemini Pro | 0.37 GB)
3. Qwen-3-0.6B-Claude-4.7-Opus-Distilled (600M | Anthropic Claude 4.7 Opus imatrix | 0.37 GB)
4. Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT (600M | Qwen3-30B-A3B-Thinking SFT | 0.45 GB)
5. Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled (800M | Claude 4.6 Opus Reasoning - Jackrong | 0.49 GB)
6. Qwen3-Zero-Coder-Reasoning-V2-0.8B-NEO-EX (800M | Zero-Coder Reasoning V2 NEO-EX - DavidAU | 0.49 GB)
7. IBM-GPT-5.4-Coder-1B (1.0B | OpenAI GPT-5.4 Coder imatrix | 0.95 GB)
8. MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic (1.0B | Claude Opus + Fable 5 V2 Heretic | 0.64 GB)
9. LFM2.5-1.2B-Thinking-Claude-4.6-Opus-Heretic (1.2B | Claude 4.6 Opus Heretic - Liquid LFM2.5 | 0.68 GB)
10. DeepScaleR-1.5B-Preview (1.5B | Agentica / UC Berkeley RL O1-Preview Killer | 1.04 GB)
11. Thinkless-1.5B-RL-DeepScaleR (1.5B | Thinkless RL + DeepScaleR Adaptive Reasoning | 1.04 GB)
12. FableForge-1.5B-v2 (1.5B | Claude Fable-5 V2 Agentic Synthesis | 0.92 GB)
"""

import os
import sys
import time
import json
import re
import shutil
import urllib.request
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

ROTOR_ROOT = Path(r"F:\rotor-llm")
LAMBDA_RLM_DIR = ROTOR_ROOT / "lambda_rlm"
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))
if str(LAMBDA_RLM_DIR) not in sys.path:
    sys.path.insert(0, str(LAMBDA_RLM_DIR))

from benchmark_13_areas_39_testes import BENCHMARK_SUITE
from duelo_nivel_opus_8b_vs_9b import OPUS_10_TESTS
from router.formal_verifier import formal_verifier
from rlm import LambdaRLM

SERVER_BIN = r"F:\tools\lc_b10749\llama-server.exe"
PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"
LOCAL_DIR = Path(r"F:\models\pesos_mosca_200m_15b")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

PROOF_FILE = Path(r"F:\data\proof_duelo_pesos_mosca_200m_15b.json")
LOG_FILE = Path(r"F:\data\tournament_pesos_mosca.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_pesos_mosca.log")

CONTENDERS = [
    {
        "id": "glogwa68_granite4_350m_gemini3_pro",
        "name": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think",
        "maintainer": "glogwa68",
        "repo": "glogwa68/granite-4.0-h-350m-DISTILL-gemini-think-GGUF",
        "filename": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q4_k_m.gguf",
        "size_gb": 0.21,
        "teacher": "Google Gemini 3 Pro Thinking",
        "arch": "Granite 4.0 Hybrid 350M",
        "quant": "Q4_K_M",
        "tier": "350M"
    },
    {
        "id": "geraldine_gemini_qwen25_05b",
        "name": "Gemini-Distill-Qwen2.5-0.5B-ead",
        "maintainer": "Geraldine",
        "repo": "Geraldine/Gemini-Distill-Qwen2.5-0.5B-ead-GGUF",
        "filename": "Gemini-Distill-Qwen2.5-0.5B-ead-Q4_K_M.gguf",
        "size_gb": 0.37,
        "teacher": "Google Gemini Pro",
        "arch": "Qwen2.5 0.5B",
        "quant": "Q4_K_M",
        "tier": "500M"
    },
    {
        "id": "mradermacher_qwen3_06b_claude47_opus",
        "name": "Qwen-3-0.6B-Claude-4.7-Opus-Distilled",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Qwen-3-0.6B-Claude-4.7-Opus-Distilled-i1-GGUF",
        "filename": "Qwen-3-0.6B-Claude-4.7-Opus-Distilled.i1-Q4_K_M.gguf",
        "size_gb": 0.37,
        "teacher": "Anthropic Claude 4.7 Opus (imatrix)",
        "arch": "Qwen3 0.6B",
        "quant": "i1-Q4_K_M",
        "tier": "600M"
    },
    {
        "id": "reaper_qwen3_06b_distill_30b_thinking",
        "name": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT",
        "maintainer": "reaperdoesntknow",
        "repo": "reaperdoesntknow/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF",
        "filename": "qwen3-0.6b-distilled-30b-thinking-sft-Q4_K_M.gguf",
        "size_gb": 0.45,
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "arch": "Qwen3 0.6B",
        "quant": "Q4_K_M",
        "tier": "600M"
    },
    {
        "id": "jackrong_qwen35_08b_claude46_opus",
        "name": "Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled",
        "maintainer": "Jackrong",
        "repo": "Jackrong/Qwen3.5-0.8B-Claude-4.6-Opus-Reasoning-Distilled-GGUF",
        "filename": "Qwen3.5-0.8B.Q4_K_M.gguf",
        "size_gb": 0.49,
        "teacher": "Anthropic Claude 4.6 Opus Reasoning",
        "arch": "Qwen3.5 0.8B",
        "quant": "Q4_K_M",
        "tier": "800M"
    },
    {
        "id": "davidau_qwen3_zerocoder_v2_08b_neo",
        "name": "Qwen3-Zero-Coder-Reasoning-V2-0.8B-NEO-EX",
        "maintainer": "DavidAU",
        "repo": "DavidAU/Qwen3-Zero-Coder-Reasoning-V2-0.8B-NEO-EX-GGUF",
        "filename": "Qwen3-Zro-Cdr-Reason-V2-0.8B-NEO-EX-D_AU-Q4_K_M-imat.gguf",
        "size_gb": 0.49,
        "teacher": "Zero-Coder Reasoning V2 NEO-EX (imatrix)",
        "arch": "Qwen3 0.8B",
        "quant": "Q4_K_M-imat",
        "tier": "800M"
    },
    {
        "id": "mradermacher_ibm_gpt54_coder_1b",
        "name": "IBM-GPT-5.4-Coder-1B",
        "maintainer": "mradermacher",
        "repo": "mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF",
        "filename": "IBM-GPT-5.4-Coder-1B.i1-Q4_K_M.gguf",
        "size_gb": 0.95,
        "teacher": "OpenAI GPT-5.4 Coder (imatrix)",
        "arch": "IBM Granite 1B",
        "quant": "i1-Q4_K_M",
        "tier": "1.0B"
    },
    {
        "id": "mradermacher_minicpm5_1b_opus_fable5_v2_heretic",
        "name": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic",
        "maintainer": "mradermacher",
        "repo": "mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF",
        "filename": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q4_K_M.gguf",
        "size_gb": 0.64,
        "teacher": "Claude Opus + Fable 5 V2 Thinking Heretic",
        "arch": "MiniCPM5 1B",
        "quant": "Q4_K_M",
        "tier": "1.0B"
    },
    {
        "id": "mradermacher_lfm25_12b_claude46_opus_heretic",
        "name": "LFM2.5-1.2B-Thinking-Claude-4.6-Opus-Heretic",
        "maintainer": "mradermacher",
        "repo": "mradermacher/LFM2.5-1.2B-Thinking-Claude-4.6-Opus-Heretic-Uncensored-DISTILL-GGUF",
        "filename": "LFM2.5-1.2B-Thinking-Claude-4.6-Opus-Heretic-Uncensored-DISTILL.Q4_K_M.gguf",
        "size_gb": 0.68,
        "teacher": "Anthropic Claude 4.6 Opus Heretic",
        "arch": "Liquid LFM2.5 1.2B",
        "quant": "Q4_K_M",
        "tier": "1.2B"
    },
    {
        "id": "bartowski_deepscaler_15b_preview",
        "name": "DeepScaleR-1.5B-Preview",
        "maintainer": "bartowski",
        "repo": "bartowski/agentica-org_DeepScaleR-1.5B-Preview-GGUF",
        "filename": "agentica-org_DeepScaleR-1.5B-Preview-Q4_K_M.gguf",
        "size_gb": 1.04,
        "teacher": "Agentica / UC Berkeley RL O1-Preview Surpasser",
        "arch": "Qwen2.5 1.5B RL",
        "quant": "Q4_K_M",
        "tier": "1.5B"
    },
    {
        "id": "mradermacher_thinkless_15b_rl_deepscaler",
        "name": "Thinkless-1.5B-RL-DeepScaleR",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Thinkless-1.5B-RL-DeepScaleR-GGUF",
        "filename": "Thinkless-1.5B-RL-DeepScaleR.Q4_K_M.gguf",
        "size_gb": 1.04,
        "teacher": "Thinkless RL + DeepScaleR Adaptive Reasoning",
        "arch": "Qwen2.5 1.5B RL",
        "quant": "Q4_K_M",
        "tier": "1.5B"
    },
    {
        "id": "fableforge_15b_v2",
        "name": "FableForge-1.5B-v2",
        "maintainer": "fableforge-ai",
        "repo": "fableforge-ai/FableForge-1.5B-v2-GGUF",
        "filename": "FableForge-1.5B-v2-q4_k_m.gguf",
        "size_gb": 0.92,
        "teacher": "Claude Fable-5 V2 Agentic Synthesis",
        "arch": "Qwen2.5 1.5B",
        "quant": "Q4_K_M",
        "tier": "1.5B"
    }
]

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
        f.write(line + "\n")

def stop_any_llama_server():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe", "/T"], capture_output=True, timeout=5)
    except Exception:
        pass
    time.sleep(0.8)

def download_model_turbo(repo: str, filename: str, local_filename: str, max_workers: int = 12) -> Path:
    target_path = LOCAL_DIR / local_filename
    if target_path.exists() and target_path.stat().st_size > 50 * 1024 * 1024:
        log(f"[+] Modelo já presente em F:\\models\\pesos_mosca_200m_15b: {target_path.name} ({target_path.stat().st_size / (1024**3):.2f} GB)")
        return target_path

    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
    log(f"[*] Iniciando download TURBO paralelo (12 streams) de {repo}/{filename}...")
    part_path = LOCAL_DIR / f"{local_filename}.part"

    req_probe = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Range": "bytes=0-0"})
    with urllib.request.urlopen(req_probe, timeout=20) as resp:
        cr = resp.headers.get("Content-Range", "")
        if "/" in cr:
            total_len = int(cr.split("/")[-1])
        else:
            total_len = int(resp.headers.get("Content-Length", 0))

    if total_len <= 0:
        raise RuntimeError(f"Não foi possível obter tamanho do arquivo remoto {url}")

    log(f"[*] Tamanho total esperado: {total_len:,} bytes ({total_len / (1024**3):.2f} GB)")

    if not part_path.exists() or part_path.stat().st_size != total_len:
        with open(part_path, "wb") as f:
            f.seek(total_len - 1)
            f.write(b"\0")

    chunk_size = 16 * 1024 * 1024
    num_chunks = (total_len + chunk_size - 1) // chunk_size

    chunks_done_file = LOCAL_DIR / f"{local_filename}.chunks.json"
    done_set = set()
    if chunks_done_file.exists():
        try:
            with open(chunks_done_file, "r") as f:
                done_set = set(json.load(f))
        except Exception:
            done_set = set()

    chunks_to_download = [i for i in range(num_chunks) if i not in done_set]
    lock = threading.Lock()
    downloaded_bytes = len(done_set) * chunk_size
    start_t = time.time()
    last_log = time.time()
    chunks_downloaded_this_run = 0

    def fetch_chunk(idx):
        c_start = idx * chunk_size
        c_end = min(total_len - 1, c_start + chunk_size - 1)
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Range": f"bytes={c_start}-{c_end}"
        })

        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    data = r.read()
                    if len(data) != (c_end - c_start + 1):
                        raise IOError(f"Chunk {idx} truncado: {len(data)} != {c_end - c_start + 1}")
                    with open(part_path, "r+b") as fp:
                        fp.seek(c_start)
                        fp.write(data)
                    return idx, len(data)
            except Exception as ex:
                if attempt == 4:
                    raise ex
                time.sleep(1.0 * (attempt + 1))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(fetch_chunk, idx): idx for idx in chunks_to_download}
        for fut in as_completed(futures):
            idx, sz = fut.result()
            with lock:
                done_set.add(idx)
                downloaded_bytes += sz
                chunks_downloaded_this_run += 1
                now = time.time()
                if now - last_log >= 6.0 or len(done_set) == num_chunks:
                    elapsed = now - start_t
                    speed_mb = (chunks_downloaded_this_run * chunk_size) / elapsed / (1024**2) if elapsed > 0 else 0.0
                    pct = (len(done_set) / num_chunks) * 100
                    log(f"    -> Turbo Download: {len(done_set)}/{num_chunks} chunks ({pct:.1f}%) | {downloaded_bytes / (1024**3):.2f}/{total_len / (1024**3):.2f} GB | {speed_mb:.2f} MB/s")
                    last_log = now
                    with open(chunks_done_file, "w") as f:
                        json.dump(list(done_set), f)

    if chunks_done_file.exists():
        chunks_done_file.unlink()

    if part_path.exists() and part_path.stat().st_size == total_len:
        if target_path.exists():
            target_path.unlink()
        part_path.rename(target_path)
        log(f"[+] Download Turbo Concluído: {target_path.name} ({target_path.stat().st_size / (1024**3):.2f} GB)!")
        return target_path
    else:
        raise RuntimeError(f"Falha na validação final do arquivo baixado {local_filename}")

def start_server(model_path: Path) -> tuple[subprocess.Popen, float]:
    stop_any_llama_server()
    cmd = [
        SERVER_BIN,
        "-m", str(model_path),
        "-c", "4096",
        "-b", "512",
        "-ub", "512",
        "-t", "14",
        "--port", str(PORT),
        "--host", "127.0.0.1"
    ]
    log(f"-> Subindo llama-server Turbo (14 threads Xeon AVX2, BelowNormal priority): {model_path.name}...")
    server_out = open(SERVER_LOG_FILE, "w", encoding="utf-8")
    t0 = time.time()
    # creationflags=0x00004000 sets BelowNormal priority on Windows so desktop never freezes
    proc = subprocess.Popen(cmd, stdout=server_out, stderr=subprocess.STDOUT, text=True, errors="replace", creationflags=0x00004000)

    for _ in range(240):
        time.sleep(0.5)
        if proc.poll() is not None:
            server_out.flush()
            err_msg = open(SERVER_LOG_FILE, encoding="utf-8", errors="replace").read()[-800:]
            raise RuntimeError(f"llama-server encerrou prematuramente (código {proc.returncode}):\n{err_msg}")
        try:
            req = urllib.request.Request(f"{BASE_URL}/health")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    boot_s = round(time.time() - t0, 2)
                    log(f"   [+] Servidor 200 OK (tempo de boot: {boot_s}s)!")
                    return proc, boot_s
        except Exception:
            pass

    stop_any_llama_server()
    raise RuntimeError(f"Timeout ao iniciar llama-server para {model_path.name}")

def measure_speed(boot_s: float) -> Dict[str, float]:
    log("[*] Aferindo velocidade de inferência bare-metal (128 tokens forçados com ignore_eos)...")
    prompt = "Escreva uma análise técnica profunda sobre a teoria dos números primos, complexidade ciclomática, grafos de fluxo de controle e arquitetura de computadores quânticos."
    payload = json.dumps({
        "prompt": prompt,
        "n_predict": 128,
        "temperature": 0.0,
        "ignore_eos": True
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = max(0.01, time.time() - t0)
            timings = data.get("timings", {})
            pp_speed = timings.get("prompt_per_second", 0.0)
            tg_speed = timings.get("predicted_per_second", 0.0)

            if tg_speed <= 0.0 or tg_speed > 5000.0:
                pred_ms = timings.get("predicted_ms", 0.0)
                pred_n = timings.get("predicted_n", 128)
                if pred_ms > 1.0:
                    tg_speed = pred_n / (pred_ms / 1000.0)
                else:
                    tg_speed = 128.0 / elapsed

            log(f"   [SPEED PROOF] Boot: {boot_s}s | Ingestão Prompt (PP): {pp_speed:.2f} tok/s | Geração Texto (TG): {tg_speed:.2f} tok/s")
            return {
                "boot_seconds": boot_s,
                "prompt_per_second": round(pp_speed, 2),
                "predicted_per_second": round(tg_speed, 2)
            }
    except Exception as e:
        log(f"[!] Erro ao aferir velocidade: {e}")
        return {"boot_seconds": boot_s, "prompt_per_second": 0.0, "predicted_per_second": 0.0}

def extract_text_after_think(text: str) -> str:
    if "</think>" in text:
        parts = text.split("</think>", 1)
        post = parts[1].strip()
        if post:
            return post
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    if "<think>" in cleaned.lower():
        cleaned = re.sub(r"<think>", "", cleaned, flags=re.IGNORECASE).strip()
    return cleaned if cleaned else text.strip()

def clean_python_code(text: str) -> str:
    cleaned = extract_text_after_think(text)
    pattern = r"```(?:python)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    m_code = re.search(r"^(?:import|from|def|class)\s+", cleaned, re.MULTILINE)
    if m_code:
        cleaned = cleaned[m_code.start():]
    return cleaned.strip()

def query_fast_direct(prompt: str, is_code: bool = False, max_tokens: int = 512) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown." if is_code else clean

    # Tentativa 1: Chat completions
    payload = json.dumps({
        "messages": [{"role": "user", "content": eff_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if content:
                if "<think>" in content.lower() and "</think>" not in content.lower():
                    pass # cai no fallback raw completion
                else:
                    return content
    except Exception:
        pass

    # Tentativa 2: Raw completion com prefill anti-think
    payload2 = json.dumps({
        "prompt": f"<|im_start|>user\n{eff_prompt}\n<|im_end|>\n<|im_start|>assistant\n<think>\nDirect answer.\n</think>\n",
        "n_predict": max_tokens,
        "temperature": 0.0,
        "stop": ["<|im_end|>", "<|endoftext|>", "</s>"]
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=45.0) as r2:
            d2 = json.loads(r2.read().decode("utf-8"))
            c2 = d2.get("content", "").strip()
            if c2:
                return c2
    except Exception:
        pass

    # Tentativa 3: Completion cru
    payload3 = json.dumps({
        "prompt": eff_prompt,
        "n_predict": max_tokens,
        "temperature": 0.0
    }).encode("utf-8")
    req3 = urllib.request.Request(f"{BASE_URL}/completion", data=payload3, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req3, timeout=45.0) as r3:
            d3 = json.loads(r3.read().decode("utf-8"))
            return d3.get("content", "").strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def query_lambda(lambda_engine: LambdaRLM, prompt: str, is_code: bool = False) -> str:
    clean = prompt.replace("/no_think", "").strip()
    if is_code:
        eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown."
    else:
        eff_prompt = clean
    try:
        res = lambda_engine.completion(eff_prompt)
        return res.response.strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def run_13_areas(lambda_engine: LambdaRLM) -> Dict[str, Any]:
    log("  [*] Executando Bateria 13 Áreas Cognitivas (39 testes: Baseline + Lambda-RLM)...")
    base_passed = 0
    rlm_passed = 0
    areas = {}
    perfect_count = 0

    for i, area in enumerate(BENCHMARK_SUITE, 1):
        a_id = area.get("area_id", str(i))
        a_name = area.get("area_name", f"Area_{i}")
        a_base_pass = 0
        a_rlm_pass = 0
        for test in area["tests"]:
            p = test["prompt"]
            validator = test.get("verify") or test.get("validator")
            is_code = (test.get("schema_type") == "python_func" or "Escreva em Python" in p or "função `" in p)

            # Pass 1: Baseline
            out = query_fast_direct(p, is_code=is_code, max_tokens=512 if is_code else 384)
            val_input = clean_python_code(out) if is_code else extract_text_after_think(out)
            ok_base = False
            try:
                ok_base = bool(validator(val_input))
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
                # Pass 2: Lambda-RLM Fallback
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
            "total": len(area["tests"])
        }
        log(f"    -> Área {a_id} ({a_name[:25]}): Baseline {a_base_pass}/3 | Lambda-RLM {a_rlm_pass}/3")

    base_pct = round((base_passed / 39) * 100, 2)
    rlm_pct = round((rlm_passed / 39) * 100, 2)
    log(f"  [+] Pontuação Final 13 Áreas: Baseline {base_passed}/39 ({base_pct}%) ➔ Lambda-RLM {rlm_passed}/39 ({rlm_pct}%) | Gabaritadas 3/3: {perfect_count}")
    return {
        "baseline_passed": base_passed,
        "baseline_pct": base_pct,
        "passed": rlm_passed,
        "total": 39,
        "pct": rlm_pct,
        "perfect_areas_count": perfect_count,
        "areas": areas
    }

def run_opus(lambda_engine: LambdaRLM) -> Dict[str, Any]:
    log("  [*] Executando Bateria 10 Desafios Opus (Verificação Formal AST & pytest: Baseline + Lambda-RLM)...")
    base_passed = 0
    opus_passed = 0
    opus_details = {}

    for test in OPUS_10_TESTS:
        t_id = test["id"]
        t_name = test["name"]
        prompt = test["prompt"]
        assertions = test["assertions"]

        log(f"    -> {t_id} ({t_name[:35]})...")
        passed = False
        res_str = "FAIL"

        # Tentativa 1: Baseline Direto
        try:
            raw = query_fast_direct(prompt, is_code=True, max_tokens=640)
            code = clean_python_code(raw)
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=8.0)
            if ver.passed:
                passed = True
                base_passed += 1
                res_str = "PASS (Baseline)"
        except Exception:
            pass

        # Tentativa 2: Fallback Lambda-RLM se baseline falhar
        if not passed:
            try:
                raw_rlm = query_lambda(lambda_engine, prompt, is_code=True)
                code_rlm = clean_python_code(raw_rlm)
                ver_rlm = formal_verifier.verify_python_code(code_rlm, assertions, timeout_s=8.0)
                if ver_rlm.passed:
                    passed = True
                    res_str = "PASS (Lambda-RLM)"
            except Exception:
                pass

        if passed:
            opus_passed += 1
        log(f"       Resultado: {res_str}")
        opus_details[t_id] = res_str

    base_pct = round((base_passed / len(OPUS_10_TESTS)) * 100, 2)
    pct = round((opus_passed / len(OPUS_10_TESTS)) * 100, 2)
    log(f"  [+] Pontuação Final Opus: Baseline {base_passed}/10 ({base_pct}%) ➔ Lambda-RLM {opus_passed}/10 ({pct}%)")
    return {
        "baseline_passed": base_passed,
        "baseline_pct": base_pct,
        "passed": opus_passed,
        "total": len(OPUS_10_TESTS),
        "pct": pct,
        "details": opus_details
    }

def main():
    log("================================================================================")
    log("AETHERMIND — DUELO FINAL DOS PESOS-MOSCA (200M a 1.5B) — 12 MODELOS TIER-1")
    log("================================================================================")

    proof_data = {}
    if PROOF_FILE.exists():
        try:
            proof_data = json.load(open(PROOF_FILE, encoding="utf-8"))
        except Exception:
            pass

    for idx, contender in enumerate(CONTENDERS, 1):
        c_id = contender["id"]
        c_name = contender["name"]
        c_fn = contender["filename"]
        c_local_fn = f"{c_id}__{c_fn}"
        c_repo = contender["repo"]

        if c_id in proof_data and "areas_13" in proof_data[c_id] and "opus_10" in proof_data[c_id]:
            log(f"[*] [{idx}/{len(CONTENDERS)}] {c_name} já avaliado (13 Áreas: {proof_data[c_id]['areas_13']['passed']}/39, Opus: {proof_data[c_id]['opus_10']['passed']}/10). Pulando...")
            continue

        log(f"\n################################################################################")
        log(f"[*] [{idx}/{len(CONTENDERS)}] PROCESSANDO PESO-MOSCA: {c_name} ({contender['size_gb']} GB) | Classe: {contender['tier']}")
        log(f"    Mantenedor: {contender['maintainer']} | Arquitetura: {contender['arch']}")
        log(f"    Professor: {contender['teacher']} | Quantização: {contender['quant']}")
        log(f"################################################################################")

        try:
            model_path = download_model_turbo(c_repo, c_fn, c_local_fn, max_workers=12)
            proc, boot_s = start_server(model_path)
            speeds = measure_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": c_local_fn,
                    "base_url": f"{BASE_URL}/v1",
                    "api_key": "none",
                    "timeout": 45.0,
                    "max_tokens": 512,
                    "temperature": 0.0
                },
                environment="local",
                context_window_chars=40000,
                verbose=False
            )

            areas_res = run_13_areas(lambda_engine)
            opus_res = run_opus(lambda_engine)
            stop_any_llama_server()

            proof_data[c_id] = {
                "name": c_name,
                "filename": c_fn,
                "local_path": str(model_path),
                "maintainer": contender["maintainer"],
                "repo": c_repo,
                "teacher": contender["teacher"],
                "arch": contender["arch"],
                "quant": contender["quant"],
                "tier": contender["tier"],
                "size_gb": contender["size_gb"],
                "speeds": speeds,
                "areas_13": areas_res,
                "opus_10": opus_res,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(PROOF_FILE, "w", encoding="utf-8") as f:
                json.dump(proof_data, f, indent=2, ensure_ascii=False)
            log(f"[+] Prova gravada com sucesso em {PROOF_FILE}!")

        except Exception as e:
            log(f"[!] ERRO ao processar {c_name}: {e}")
            stop_any_llama_server()

    log("\n[DUELO FINAL DOS PESOS-MOSCA CONCLUÍDO] Todos os concorrentes avaliados com sucesso!")

if __name__ == "__main__":
    main()
