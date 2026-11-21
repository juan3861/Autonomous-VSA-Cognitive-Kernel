# -*- coding: utf-8 -*-
"""
AETHERMIND — GRANDE TORNEIO DOS 9 MODELOS DESTILADOS 2026 (1-TIER TEACHERS)
Comandante Primário: Mestre Ruan

Faixas e Concorrentes:
1. Faixa 200M a 1B (3 Modelos):
   - tinyopsec/MiniCPM5-1B-Claude-Opus-Fable5-Thinking-GGUF (model-Q4_K_M.gguf - 0.64 GB)
   - QuantFactory/Reasoning-0.5b-GGUF (Reasoning-0.5b.Q4_K_M.gguf - 0.37 GB)
   - mradermacher/DeepSeek-R1-Distill-Qwen-0.5B-CoMa-GGUF (DeepSeek-R1-Distill-Qwen-0.5B-CoMa.Q4_K_M.gguf - 0.37 GB)

2. Faixa 2B (3 Modelos):
   - mradermacher/Gemma-2-2B-Opus-Instruct-GGUF (Gemma-2-2B-Opus-Instruct.Q4_K_M.gguf - 1.59 GB)
   - bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF (DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf - 1.04 GB)
   - C10X/Qwen2.5-1.5B-Claude-GGUF (unsloth.Q8_0.gguf - 1.53 GB)

3. Faixa 5B a 7B (3 Modelos):
   - bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF (DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf - 4.36 GB)
   - mradermacher/Qwen2.5-7B-Instruct-1M-Thinking-Claude-Gemini-GPT5.2-DISTILL-GGUF (Qwen2.5-7B-Instruct-1M-Thinking-Claude-Gemini-GPT5.2-DISTILL.Q4_K_M.gguf - 4.68 GB)
   - QuantFactory/OpenR1-Distill-7B-GGUF (OpenR1-Distill-7B.Q4_K_M.gguf - 4.36 GB)

Harness de Homologação:
- Download Turbo Paralelo (12 streams, 16MB chunks) para SSD F:\\
- Velocidade Bare-Metal Xeon AVX2 14 threads (PP tok/s, TG tok/s, boot)
- 13 Áreas Cognitivas Canônicas (39 testes pontuados 0 a 3)
- 10 Desafios Opus (LeetCode Hard) com Verificação Formal AST & pytest
- Gravação Incremental em F:\\data\\proof_9_distills_2026.json
- Rotação Automática e Purga de SSD
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
LOCAL_DIR = Path(r"F:\AetherMind_Contenders")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

PROOF_FILE = Path(r"F:\data\proof_9_distills_2026.json")
LOG_FILE = Path(r"F:\data\tournament_9_distills_2026.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_tournament.log")

CONTENDERS = [
    # --- FAIXA 200M a 1B ---
    {
        "id": "tinyopsec_minicpm5_1b",
        "name": "MiniCPM5-1B-Claude-Opus-Fable5-Thinking",
        "maintainer": "tinyopsec",
        "repo": "tinyopsec/MiniCPM5-1B-Claude-Opus-Fable5-Thinking-GGUF",
        "filename": "model-Q4_K_M.gguf",
        "size_gb": 0.64,
        "teacher": "Claude Opus + Fable 5 Thinking",
        "arch": "MiniCPM 1B",
        "quant": "Q4_K_M",
        "tier": "200M-1B"
    },
    {
        "id": "quantfactory_reasoning_05b",
        "name": "Reasoning-0.5b",
        "maintainer": "QuantFactory",
        "repo": "QuantFactory/Reasoning-0.5b-GGUF",
        "filename": "Reasoning-0.5b.Q4_K_M.gguf",
        "size_gb": 0.37,
        "teacher": "DeepSeek-R1 CoT (KingNish)",
        "arch": "Qwen2.5 0.5B",
        "quant": "Q4_K_M",
        "tier": "200M-1B"
    },
    {
        "id": "mradermacher_deepseek_r1_05b_coma",
        "name": "DeepSeek-R1-Distill-Qwen-0.5B-CoMa",
        "maintainer": "mradermacher",
        "repo": "mradermacher/DeepSeek-R1-Distill-Qwen-0.5B-CoMa-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-0.5B-CoMa.Q4_K_M.gguf",
        "size_gb": 0.37,
        "teacher": "DeepSeek-R1 CoMa (Mathematical Reasoning)",
        "arch": "Qwen2.5 0.5B",
        "quant": "Q4_K_M",
        "tier": "200M-1B"
    },
    # --- FAIXA 2B ---
    {
        "id": "mradermacher_gemma2_2b_opus",
        "name": "Gemma-2-2B-Opus-Instruct",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Gemma-2-2B-Opus-Instruct-GGUF",
        "filename": "Gemma-2-2B-Opus-Instruct.Q4_K_M.gguf",
        "size_gb": 1.59,
        "teacher": "Claude Opus Instruct",
        "arch": "Gemma-2 2B",
        "quant": "Q4_K_M",
        "tier": "2B"
    },
    {
        "id": "bartowski_deepseek_r1_15b",
        "name": "DeepSeek-R1-Distill-Qwen-1.5B",
        "maintainer": "bartowski",
        "repo": "bartowski/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "size_gb": 1.04,
        "teacher": "DeepSeek-R1",
        "arch": "Qwen2.5 1.5B",
        "quant": "Q4_K_M",
        "tier": "2B"
    },
    {
        "id": "c10x_qwen25_15b_claude",
        "name": "Qwen2.5-1.5B-Claude",
        "maintainer": "C10X",
        "repo": "C10X/Qwen2.5-1.5B-Claude-GGUF",
        "filename": "unsloth.Q8_0.gguf",
        "size_gb": 1.53,
        "teacher": "Claude 3.5 Sonnet",
        "arch": "Qwen2.5 1.5B",
        "quant": "Q8_0",
        "tier": "2B"
    },
    # --- FAIXA 5B a 7B ---
    {
        "id": "bartowski_deepseek_r1_7b",
        "name": "DeepSeek-R1-Distill-Qwen-7B",
        "maintainer": "bartowski",
        "repo": "bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-7B-Q4_K_M.gguf",
        "size_gb": 4.36,
        "teacher": "DeepSeek-R1",
        "arch": "Qwen2.5 7B",
        "quant": "Q4_K_M",
        "tier": "5B-7B"
    },
    {
        "id": "mradermacher_qwen25_7b_claude_gemini_gpt52",
        "name": "Qwen2.5-7B-Thinking-Claude-Gemini-GPT5.2-Distill",
        "maintainer": "mradermacher",
        "repo": "mradermacher/Qwen2.5-7B-Instruct-1M-Thinking-Claude-Gemini-GPT5.2-DISTILL-GGUF",
        "filename": "Qwen2.5-7B-Instruct-1M-Thinking-Claude-Gemini-GPT5.2-DISTILL.Q4_K_M.gguf",
        "size_gb": 4.68,
        "teacher": "Claude + Gemini + GPT-5.2 Distill",
        "arch": "Qwen2.5 7B",
        "quant": "Q4_K_M",
        "tier": "5B-7B"
    },
    {
        "id": "quantfactory_openr1_distill_7b",
        "name": "OpenR1-Distill-7B",
        "maintainer": "QuantFactory",
        "repo": "QuantFactory/OpenR1-Distill-7B-GGUF",
        "filename": "OpenR1-Distill-7B.Q4_K_M.gguf",
        "size_gb": 4.36,
        "teacher": "OpenR1 (Hugging Face / DeepSeek-R1 Distill)",
        "arch": "Qwen2.5 7B",
        "quant": "Q4_K_M",
        "tier": "5B-7B"
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
    time.sleep(1.0)

def wait_for_disk_space(required_gb: float = 8.0):
    log(f"[*] Verificando espaço em disco no SSD F:\\ (necessário: {required_gb:.1f} GB livres)...")
    while True:
        free_gb = shutil.disk_usage("F:").free / (1024**3)
        if free_gb >= required_gb:
            log(f"[+] Espaço disponível confirmado em F:\\: {free_gb:.2f} GB livres.")
            break
        log(f"    Espaço atual: {free_gb:.2f} GB livres. Aguardando liberação do SSD...")
        time.sleep(5.0)

def download_model_turbo(repo: str, filename: str, max_workers: int = 12) -> Path:
    target_path = LOCAL_DIR / filename
    if target_path.exists() and target_path.stat().st_size > 50 * 1024 * 1024:
        log(f"[+] Modelo já presente no SSD local: {target_path.name} ({target_path.stat().st_size / (1024**3):.2f} GB)")
        return target_path

    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
    log(f"[*] Iniciando download TURBO paralelo (12 streams) de {filename}...")
    part_path = LOCAL_DIR / f"{filename}.part"

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
        log(f"[*] Pré-alocando espaço para {part_path.name}...")
        with open(part_path, "wb") as f:
            f.seek(total_len - 1)
            f.write(b"\0")

    chunk_size = 16 * 1024 * 1024
    num_chunks = (total_len + chunk_size - 1) // chunk_size

    chunks_done_file = LOCAL_DIR / f"{filename}.chunks.json"
    done_set = set()
    if chunks_done_file.exists():
        try:
            with open(chunks_done_file, "r") as f:
                done_set = set(json.load(f))
        except Exception:
            done_set = set()

    chunks_to_download = [i for i in range(num_chunks) if i not in done_set]
    log(f"[*] Total de chunks de 16MB: {num_chunks} | Já concluídos: {len(done_set)} | A baixar: {len(chunks_to_download)}")

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
                if now - last_log >= 8.0 or len(done_set) == num_chunks:
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
        raise RuntimeError(f"Falha na validação final do arquivo baixado {filename}")

def start_server(model_path: Path) -> subprocess.Popen:
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
    log(f"-> Subindo llama-server Turbo (14 threads Xeon AVX2): {model_path.name}...")
    server_out = open(SERVER_LOG_FILE, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=server_out, stderr=subprocess.STDOUT, text=True, errors="replace")

    for sec in range(180):
        time.sleep(1.0)
        if proc.poll() is not None:
            server_out.flush()
            err_msg = open(SERVER_LOG_FILE, encoding="utf-8", errors="replace").read()[-500:]
            raise RuntimeError(f"llama-server encerrou prematuramente (código {proc.returncode}):\n{err_msg}")
        try:
            req = urllib.request.Request(f"{BASE_URL}/health")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    log(f"   [+] Servidor 200 OK (tempo de boot: {sec+1}s)!")
                    return proc
        except Exception:
            pass

    stop_any_llama_server()
    raise RuntimeError(f"Timeout ao iniciar llama-server para {model_path.name}")

def measure_speed() -> Dict[str, float]:
    log("[*] Aferindo velocidade de inferência bare-metal (Prompt Processing e Text Generation)...")
    prompt = "Escreva uma análise técnica profunda sobre a teoria dos números primos, complexidade ciclomática e arquitetura de computadores quânticos."
    payload = json.dumps({
        "prompt": prompt,
        "n_predict": 128,
        "temperature": 0.0
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=60.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = time.time() - t0
            timings = data.get("timings", {})
            pp_speed = timings.get("prompt_per_second", 0.0)
            tg_speed = timings.get("predicted_per_second", 0.0)

            if tg_speed == 0.0 and "predicted_ms" in timings and timings["predicted_ms"] > 0:
                n_tokens = timings.get("predicted_n") or timings.get("tokens_predicted") or 128
                tg_speed = n_tokens / (timings["predicted_ms"] / 1000.0)
            if tg_speed == 0.0:
                tokens_count = len(data.get("content", "").split())
                tg_speed = tokens_count / elapsed if elapsed > 0 else 0.0

            log(f"   [SPEED PROOF] Ingestão Prompt (PP): {pp_speed:.2f} tok/s | Geração Texto (TG): {tg_speed:.2f} tok/s")
            return {"prompt_per_second": round(pp_speed, 2), "predicted_per_second": round(tg_speed, 2)}
    except Exception as e:
        log(f"[!] Erro ao aferir velocidade: {e}")
        return {"prompt_per_second": 0.0, "predicted_per_second": 0.0}

def extract_text_after_think(text: str) -> str:
    if "</think>" in text:
        parts = text.split("</think>", 1)
        post = parts[1].strip()
        if post:
            return post
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
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

def query_fast_direct(prompt: str, is_code: bool = False, max_tokens: int = 384) -> str:
    clean = prompt.replace("/no_think", "").strip()
    if is_code:
        eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown."
    else:
        eff_prompt = clean

    payload = json.dumps({
        "messages": [{"role": "user", "content": eff_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=45.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
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

def run_13_areas() -> Dict[str, Any]:
    log("  [*] Executando Bateria 13 Áreas Cognitivas (39 testes)...")
    passed = 0
    areas = {}
    perfect_count = 0

    for i, area in enumerate(BENCHMARK_SUITE, 1):
        a_id = area.get("area_id", str(i))
        a_name = area.get("area_name", f"Area_{i}")
        a_pass = 0
        for test in area["tests"]:
            p = test["prompt"]
            validator = test.get("verify") or test.get("validator")
            is_code = (test.get("schema_type") == "python_func" or "Escreva em Python" in p or "função `" in p)
            out = query_fast_direct(p, is_code=is_code, max_tokens=256)
            val_input = clean_python_code(out) if is_code else extract_text_after_think(out)
            try:
                ok = bool(validator(val_input))
            except Exception:
                try:
                    ok = bool(validator(out))
                except Exception:
                    ok = False
            if ok:
                a_pass += 1
                passed += 1

        if a_pass == len(area["tests"]):
            perfect_count += 1
        areas[a_id] = {"name": a_name, "passed": a_pass, "total": len(area["tests"])}
        log(f"    -> Área {a_id} ({a_name[:25]}): {a_pass}/{len(area['tests'])}")

    pct = round((passed / 39) * 100, 2)
    log(f"  [+] Pontuação Final 13 Áreas: {passed}/39 ({pct}%) | Gabaritadas 3/3: {perfect_count}")
    return {"passed": passed, "total": 39, "pct": pct, "perfect_areas_count": perfect_count, "areas": areas}

def run_opus(lambda_engine: LambdaRLM) -> Dict[str, Any]:
    log("  [*] Executando Bateria 10 Desafios Opus (com verificação formal AST & pytest)...")
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
            raw = query_fast_direct(prompt, is_code=True, max_tokens=512)
            code = clean_python_code(raw)
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=10.0)
            if ver.passed:
                passed = True
                res_str = "PASS (Baseline)"
        except Exception:
            pass

        # Tentativa 2: Fallback Lambda-RLM se baseline falhar
        if not passed:
            try:
                raw_rlm = query_lambda(lambda_engine, prompt, is_code=True)
                code_rlm = clean_python_code(raw_rlm)
                ver_rlm = formal_verifier.verify_python_code(code_rlm, assertions, timeout_s=10.0)
                if ver_rlm.passed:
                    passed = True
                    res_str = "PASS (Lambda-RLM)"
            except Exception:
                pass

        if passed:
            opus_passed += 1
        log(f"       Resultado: {res_str}")
        opus_details[t_id] = res_str

    pct = round((opus_passed / len(OPUS_10_TESTS)) * 100, 2)
    log(f"  [+] Pontuação Final Opus: {opus_passed}/{len(OPUS_10_TESTS)} ({pct}%)")
    return {"passed": opus_passed, "total": len(OPUS_10_TESTS), "pct": pct, "details": opus_details}

def purge_local_model(model_path: Path):
    log(f"[*] Liberando espaço no SSD local: removendo {model_path.name}...")
    if model_path.exists():
        try:
            model_path.unlink()
            free_gb = shutil.disk_usage("F:").free / (1024**3)
            log(f"[+] {model_path.name} purgado. Espaço livre restaurado em F:\\: {free_gb:.2f} GB.")
        except Exception as e:
            log(f"[!] Falha ao remover {model_path.name}: {e}")

def main():
    log("================================================================================")
    log("AETHERMIND — GRANDE TORNEIO DOS 9 MODELOS DESTILADOS 2026 (1-TIER TEACHERS)")
    log("================================================================================")

    proof_data = {}
    if PROOF_FILE.exists():
        try:
            proof_data = json.load(open(PROOF_FILE, encoding="utf-8"))
        except Exception:
            pass

    for contender in CONTENDERS:
        c_id = contender["id"]
        c_name = contender["name"]
        c_fn = contender["filename"]
        c_repo = contender["repo"]
        req_space = contender["size_gb"] + 1.0

        if c_id in proof_data and "areas_13" in proof_data[c_id] and "opus_10" in proof_data[c_id]:
            log(f"[*] {c_name} já avaliado (13 Áreas: {proof_data[c_id]['areas_13']['passed']}/39, Opus: {proof_data[c_id]['opus_10']['passed']}/10). Pulando...")
            continue

        log(f"\n################################################################################")
        log(f"[*] PROCESSANDO CONCORRENTE: {c_name} ({contender['size_gb']} GB) | Faixa: {contender['tier']}")
        log(f"    Mantenedor: {contender['maintainer']} | Arquitetura: {contender['arch']}")
        log(f"    Professor: {contender['teacher']} | Quantização: {contender['quant']}")
        log(f"################################################################################")

        wait_for_disk_space(req_space)
        model_path = download_model_turbo(c_repo, c_fn, max_workers=12)
        proc = start_server(model_path)

        speeds = measure_speed()

        lambda_engine = LambdaRLM(
            backend="openai",
            backend_kwargs={
                "model_name": c_fn,
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

        areas_res = run_13_areas()
        opus_res = run_opus(lambda_engine)
        stop_any_llama_server()

        proof_data[c_id] = {
            "name": c_name,
            "filename": c_fn,
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

        purge_local_model(model_path)

    log("\n[TORNEIO DOS 9 MODELOS DESTILADOS CONCLUÍDO] Todos os concorrentes avaliados com sucesso!")

if __name__ == "__main__":
    main()
