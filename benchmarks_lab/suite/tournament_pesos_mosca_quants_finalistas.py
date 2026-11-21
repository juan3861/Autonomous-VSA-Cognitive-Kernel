# -*- coding: utf-8 -*-
"""
AETHERMIND — DUELO DE QUANTIZAÇÕES DOS 3 FINALISTAS PESOS-MOSCA (Q5_K_M a Q8_0)
Comandante Primário: Mestre Ruan

Finalistas Selecionados:
1. IBM-GPT-5.4-Coder-1B (1.0B | OpenAI GPT-5.4 Coder)
2. MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic (1.0B | Claude Opus + Fable 5 V2 Thinking)
3. Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT (600M | Qwen3-30B-A3B-Thinking SFT)

Quantizações Avaliadas por Modelo:
- Q4_K_M (Baseline Histórico já homologado no round anterior)
- Q5_K_M
- Q6_K
- Q8_0

Objetivo:
Medir empiricamente o Ganho Cognitivo x Perda de Velocidade e determinar o Equilíbrio Perfeito (Pareto Sweet Spot).
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
LOCAL_DIR = Path(r"F:\models\pesos_mosca_quants_finalistas")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

PROOF_FILE = Path(r"F:\data\proof_pesos_mosca_quants_finalistas.json")
BASELINE_PROOF_FILE = Path(r"F:\data\proof_duelo_pesos_mosca_200m_15b.json")
LOG_FILE = Path(r"F:\data\tournament_pesos_mosca_quants.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_pesos_mosca_quants.log")

CONTENDERS = [
    # -------------------------------------------------------------
    # 1. IBM-GPT-5.4-Coder-1B (Campeão Geral 1B)
    # -------------------------------------------------------------
    {
        "id": "ibm_gpt54_coder_1b_q5_k_m",
        "name": "IBM-GPT-5.4-Coder-1B-Q5_K_M",
        "base_model": "IBM-GPT-5.4-Coder-1B",
        "maintainer": "mradermacher",
        "repo": "mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF",
        "filename": "IBM-GPT-5.4-Coder-1B.i1-Q5_K_M.gguf",
        "local_fn": "ibm_gpt54_coder_1b__Q5_K_M.gguf",
        "teacher": "OpenAI GPT-5.4 Coder (imatrix)",
        "arch": "Granite 1B",
        "quant": "Q5_K_M",
        "tier": "1.0B"
    },
    {
        "id": "ibm_gpt54_coder_1b_q6_k",
        "name": "IBM-GPT-5.4-Coder-1B-Q6_K",
        "base_model": "IBM-GPT-5.4-Coder-1B",
        "maintainer": "mradermacher",
        "repo": "mradermacher/IBM-GPT-5.4-Coder-1B-i1-GGUF",
        "filename": "IBM-GPT-5.4-Coder-1B.i1-Q6_K.gguf",
        "local_fn": "ibm_gpt54_coder_1b__Q6_K.gguf",
        "teacher": "OpenAI GPT-5.4 Coder (imatrix)",
        "arch": "Granite 1B",
        "quant": "Q6_K",
        "tier": "1.0B"
    },
    {
        "id": "ibm_gpt54_coder_1b_q8_0",
        "name": "IBM-GPT-5.4-Coder-1B-Q8_0",
        "base_model": "IBM-GPT-5.4-Coder-1B",
        "maintainer": "mradermacher",
        "repo": "mradermacher/IBM-GPT-5.4-Coder-1B-GGUF",
        "filename": "IBM-GPT-5.4-Coder-1B.Q8_0.gguf",
        "local_fn": "ibm_gpt54_coder_1b__Q8_0.gguf",
        "teacher": "OpenAI GPT-5.4 Coder",
        "arch": "Granite 1B",
        "quant": "Q8_0",
        "tier": "1.0B"
    },

    # -------------------------------------------------------------
    # 2. MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic (Campeão Opus 1B)
    # -------------------------------------------------------------
    {
        "id": "minicpm5_1b_opus_fable_v2_q5_k_m",
        "name": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Q5_K_M",
        "base_model": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic",
        "maintainer": "mradermacher",
        "repo": "mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF",
        "filename": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q5_K_M.gguf",
        "local_fn": "minicpm5_1b_opus_fable5_v2__Q5_K_M.gguf",
        "teacher": "Claude Opus + Fable 5 V2 Thinking",
        "arch": "MiniCPM 1B",
        "quant": "Q5_K_M",
        "tier": "1.0B"
    },
    {
        "id": "minicpm5_1b_opus_fable_v2_q6_k",
        "name": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Q6_K",
        "base_model": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic",
        "maintainer": "mradermacher",
        "repo": "mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF",
        "filename": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q6_K.gguf",
        "local_fn": "minicpm5_1b_opus_fable5_v2__Q6_K.gguf",
        "teacher": "Claude Opus + Fable 5 V2 Thinking",
        "arch": "MiniCPM 1B",
        "quant": "Q6_K",
        "tier": "1.0B"
    },
    {
        "id": "minicpm5_1b_opus_fable_v2_q8_0",
        "name": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Q8_0",
        "base_model": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic",
        "maintainer": "mradermacher",
        "repo": "mradermacher/MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic-GGUF",
        "filename": "MiniCPM5-1B-Claude-Opus-Fable5-V2-Thinking-heretic.Q8_0.gguf",
        "local_fn": "minicpm5_1b_opus_fable5_v2__Q8_0.gguf",
        "teacher": "Claude Opus + Fable 5 V2 Thinking",
        "arch": "MiniCPM 1B",
        "quant": "Q8_0",
        "tier": "1.0B"
    },

    # -------------------------------------------------------------
    # 3. Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT (Rei Sub-1B)
    # -------------------------------------------------------------
    {
        "id": "qwen3_06b_distill_30b_thinking_q5_k_m",
        "name": "Qwen3-0.6B-Distilled-30B-Thinking-Q5_K_M",
        "base_model": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF",
        "filename": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q5_K_M.gguf",
        "local_fn": "qwen3_06b_distill_30b_thinking__Q5_K_M.gguf",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "arch": "Qwen3 0.6B",
        "quant": "Q5_K_M",
        "tier": "600M"
    },
    {
        "id": "qwen3_06b_distill_30b_thinking_q6_k",
        "name": "Qwen3-0.6B-Distilled-30B-Thinking-Q6_K",
        "base_model": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF",
        "filename": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q6_K.gguf",
        "local_fn": "qwen3_06b_distill_30b_thinking__Q6_K.gguf",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "arch": "Qwen3 0.6B",
        "quant": "Q6_K",
        "tier": "600M"
    },
    {
        "id": "qwen3_06b_distill_30b_thinking_q8_0",
        "name": "Qwen3-0.6B-Distilled-30B-Thinking-Q8_0",
        "base_model": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF",
        "filename": "Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT.Q8_0.gguf",
        "local_fn": "qwen3_06b_distill_30b_thinking__Q8_0.gguf",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "arch": "Qwen3 0.6B",
        "quant": "Q8_0",
        "tier": "600M"
    }
]

def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] {msg}"
    print(entry, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def stop_any_llama_server():
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command",
            "Get-NetTCPConnection -LocalPort 8089 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"],
            capture_output=True, text=True)
        pids = [p.strip() for p in r.stdout.split() if p.strip() and p.strip() != "0"]
        for pid in pids:
            log(f"[!] Encerrando processo na porta 8089 (PID: {pid})...")
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        time.sleep(1.0)
    except Exception as e:
        log(f"[!] Aviso ao encerrar processo 8089: {e}")

def download_model_turbo(repo: str, filename: str, local_filename: str, max_workers: int = 12) -> Path:
    target_path = LOCAL_DIR / local_filename
    if target_path.exists() and target_path.stat().st_size > 50 * 1024 * 1024:
        log(f"[+] Modelo já presente em {LOCAL_DIR.name}: {target_path.name} ({target_path.stat().st_size / (1024**3):.2f} GB)")
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
                    pass
                else:
                    return content
    except Exception:
        pass

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

    return ""

def query_lambda(lambda_engine: LambdaRLM, prompt: str, is_code: bool = False) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown." if is_code else clean
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
        log(f"    -> Área {a_id} ({a_name[:25]}): Baseline {a_base_pass}/{len(area['tests'])} | Lambda-RLM {a_rlm_pass}/{len(area['tests'])}")

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
    log("=" * 80)
    log("AETHERMIND — DUELO DE QUANTIZAÇÕES DOS 3 FINALISTAS (Q5_K_M a Q8_0)")
    log("=" * 80)

    proof_data = {}
    if PROOF_FILE.exists():
        try:
            with open(PROOF_FILE, "r", encoding="utf-8") as f:
                proof_data = json.load(f)
            log(f"[*] Carregados {len(proof_data)} modelos previamente homologados deste duelo de quantizações.")
        except Exception:
            proof_data = {}

    total_contenders = len(CONTENDERS)

    for idx, c in enumerate(CONTENDERS, 1):
        c_id = c["id"]
        c_name = c["name"]

        if c_id in proof_data:
            log(f"[+] [{idx}/{total_contenders}] {c_name} JÁ HOMOLOGADO. Pulando...")
            continue

        log("\n" + "#" * 80)
        log(f"[*] [{idx}/{total_contenders}] PROCESSANDO QUANTIZAÇÃO: {c_name} | Quant: {c['quant']} | Classe: {c['tier']}")
        log(f"    Modelo Base: {c['base_model']} | Mantenedor: {c['maintainer']}")
        log(f"    Professor: {c['teacher']}")
        log("#" * 80)

        # 1. Download Turbo
        try:
            model_path = download_model_turbo(c["repo"], c["filename"], c["local_fn"])
        except Exception as e:
            log(f"[!] ERRO CRÍTICO no download de {c_name}: {e}")
            continue

        # 2. Inicia llama-server
        server_proc = None
        try:
            server_proc, boot_s = start_server(model_path)
            speeds = measure_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": c["local_fn"],
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

            # 3. Bateria 13 Áreas
            areas_res = run_13_areas(lambda_engine)

            # 4. Bateria Opus
            opus_res = run_opus(lambda_engine)

            # 5. Salva Prova Incremental
            proof_data[c_id] = {
                "name": c_name,
                "base_model": c["base_model"],
                "filename": c["filename"],
                "local_path": str(model_path),
                "maintainer": c["maintainer"],
                "repo": c["repo"],
                "teacher": c["teacher"],
                "arch": c["arch"],
                "quant": c["quant"],
                "tier": c["tier"],
                "size_gb": round(model_path.stat().st_size / (1024**3), 2),
                "speeds": speeds,
                "areas_13": areas_res,
                "opus_10": opus_res,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(PROOF_FILE, "w", encoding="utf-8") as f:
                json.dump(proof_data, f, ensure_ascii=False, indent=2)
            log(f"[+] Prova gravada com sucesso em {PROOF_FILE}!")

        except Exception as e:
            log(f"[!] ERRO DURANTE AVALIAÇÃO DE {c_name}: {e}")
        finally:
            if server_proc:
                try:
                    server_proc.terminate()
                    server_proc.wait(timeout=5)
                except Exception:
                    pass
            stop_any_llama_server()
            time.sleep(2.0)

    log("\n[DUELO DE QUANTIZAÇÕES CONCLUÍDO] Todos os concorrentes avaliados com sucesso!")

if __name__ == "__main__":
    main()
