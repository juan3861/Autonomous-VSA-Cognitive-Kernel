# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO DA NOVA GERAÇÃO (NEXT-GEN TRIO CHAMPIONS)
Comandante: Mestre Ruan

Modelos Concorrentes:
1. yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF (gemma4-coding-Q4_K_M.gguf - 6.87 GB)
2. yuxinlu1/Mellum2-12B-A2.5B-Claude-4.6-4.8-Opus-Thinking-GGUF (mellum2-claude-Q4_K_M.gguf - 7.52 GB)
3. TeichAI/Qwen3.8-27B-Fable-Distill-GGUF (Qwen3.8-27B-Fable-Distill-IQ4_XS.gguf - 14.94 GB)

Baterias:
- Turbo Parallel Downloader (12 streams)
- Velocidade Bare-Metal (PP tok/s e TG tok/s)
- 10 Desafios Opus sob Lambda-RLM com Verificação Formal AST & pytest
- Rotação Automática e Prova Empírica em F:\data\proof_nextgen_trio_champions.json
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

from duelo_nivel_opus_8b_vs_9b import OPUS_10_TESTS
from router.formal_verifier import formal_verifier
from rlm import LambdaRLM

SERVER_BIN = r"F:\tools\lc_b10749\llama-server.exe"
PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"
LOCAL_DIR = Path(r"F:\AetherMind_Contenders")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

PROOF_FILE = Path(r"F:\data\proof_nextgen_trio_champions.json")
LOG_FILE = Path(r"F:\data\tournament_nextgen_trio.log")

CONTENDERS = [
    {
        "id": "yuxinlu1_gemma4_coder_fable5",
        "name": "gemma-4-12B-coder-fable5-composer2.5-v1",
        "maintainer": "yuxinlu1",
        "repo": "yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF",
        "filename": "gemma4-coding-Q4_K_M.gguf",
        "size_gb": 6.87,
        "teacher": "Fable 5 Coder + Composer 2.5",
        "arch": "Gemma 4 12B Dense",
        "quant": "Q4_K_M"
    },
    {
        "id": "yuxinlu1_mellum2_claude_opus",
        "name": "Mellum2-12B-A2.5B-Claude-4.6-4.8-Opus-Thinking",
        "maintainer": "yuxinlu1",
        "repo": "yuxinlu1/Mellum2-12B-A2.5B-Claude-4.6-4.8-Opus-Thinking-GGUF",
        "filename": "mellum2-claude-Q4_K_M.gguf",
        "size_gb": 7.52,
        "teacher": "Claude 4.6-4.8 Opus Thinking",
        "arch": "Mellum 2 MoE 12B (2.5B ativos - A2.5B)",
        "quant": "Q4_K_M"
    },
    {
        "id": "teichai_qwen3_8_fable_iq4_xs",
        "name": "Qwen3.8-27B-Fable-Distill-IQ4_XS",
        "maintainer": "TeichAI",
        "repo": "TeichAI/Qwen3.8-27B-Fable-Distill-GGUF",
        "filename": "Qwen3.8-27B-Fable-Distill-IQ4_XS.gguf",
        "size_gb": 14.94,
        "teacher": "Fable 5 Distill",
        "arch": "Qwen 3.8 MoE 27B",
        "quant": "IQ4_XS"
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

def wait_for_disk_space(required_gb: float = 16.0):
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
    if target_path.exists() and target_path.stat().st_size > 1024**3:
        log(f"[+] Modelo já presente no SSD local: {target_path.name} ({target_path.stat().st_size / (1024**3):.2f} GB)")
        return target_path

    url = f"https://huggingface.co/{repo}/resolve/main/{filename}"
    log(f"[*] Iniciando download TURBO paralelo (12 streams) de {filename}...")
    part_path = LOCAL_DIR / f"{filename}.part"

    # Obter Content-Length via Range 0-0
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

    # Pré-alocar arquivo se necessário
    if not part_path.exists() or part_path.stat().st_size != total_len:
        log(f"[*] Pré-alocando espaço para {part_path.name}...")
        with open(part_path, "wb") as f:
            f.seek(total_len - 1)
            f.write(b"\0")

    chunk_size = 16 * 1024 * 1024  # 16 MB por chunk
    num_chunks = (total_len + chunk_size - 1) // chunk_size

    # Carregar controle de progresso
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
    proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, errors="replace")

    for sec in range(300):
        time.sleep(1.0)
        if proc.poll() is not None:
            err_msg = proc.stderr.read() if proc.stderr else "Sem detalhes."
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
            
            if tg_speed == 0.0 and "tokens_predicted" in timings and timings.get("predicted_ms", 0) > 0:
                tg_speed = timings["tokens_predicted"] / (timings["predicted_ms"] / 1000.0)
            if tg_speed == 0.0:
                tokens_count = len(data.get("content", "").split())
                tg_speed = tokens_count / elapsed if elapsed > 0 else 0.0

            log(f"   [SPEED PROOF] Ingestão Prompt (PP): {pp_speed:.2f} tok/s | Geração Texto (TG): {tg_speed:.2f} tok/s")
            return {"prompt_per_second": round(pp_speed, 2), "predicted_per_second": round(tg_speed, 2)}
    except Exception as e:
        log(f"[!] Erro ao aferir velocidade: {e}")
        return {"prompt_per_second": 0.0, "predicted_per_second": 0.0}

def clean_python_code(text: str) -> str:
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE).strip()
    pattern = r"```(?:python)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, cleaned, re.IGNORECASE)
    if match:
        cleaned = match.group(1).strip()
    m_code = re.search(r"^(?:import|from|def|class)\s+", cleaned, re.MULTILINE)
    if m_code:
        cleaned = cleaned[m_code.start():]
    return cleaned.strip()

def query_lambda(lambda_engine: LambdaRLM, prompt: str) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown."
    try:
        res = lambda_engine.completion(eff_prompt)
        return res.response.strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def run_opus_benchmark(lambda_engine: LambdaRLM) -> Dict[str, Any]:
    log("  [*] Executando Bateria 10 Desafios Opus sob Lambda-RLM (com AST/pytest)...")
    opus_passed = 0
    opus_details = {}

    for test in OPUS_10_TESTS:
        t_id = test["id"]
        t_name = test["name"]
        prompt = test["prompt"]
        assertions = test["assertions"]

        log(f"    -> {t_id} ({t_name[:35]})...")
        try:
            raw_code = query_lambda(lambda_engine, prompt)
            code = clean_python_code(raw_code)
            try:
                ver = formal_verifier.verify_python_code(code, assertions, timeout_s=15.0)
                passed = ver.passed
            except Exception:
                passed = False

            if passed:
                opus_passed += 1
                res_str = "PASS (Lambda-RLM)"
            else:
                res_str = "FAIL"
        except Exception as e:
            res_str = f"ERROR ({e})"

        log(f"       Resultado: {res_str}")
        opus_details[t_id] = res_str

    log(f"  [+] Pontuação Final Opus: {opus_passed}/{len(OPUS_10_TESTS)} ({(opus_passed/len(OPUS_10_TESTS))*100:.1f}%)")
    return {"passed": opus_passed, "total": len(OPUS_10_TESTS), "details": opus_details}

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
    log("AETHERMIND — TORNEIO DA NOVA GERAÇÃO (NEXT-GEN TRIO CHAMPIONS)")
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
        req_space = contender["size_gb"] + 0.5

        if c_id in proof_data and "opus_passed" in proof_data[c_id]:
            log(f"[*] {c_name} já avaliado ({proof_data[c_id]['opus_passed']}/10). Pulando...")
            continue

        log(f"\n################################################################################")
        log(f"[*] PROCESSANDO CONCORRENTE: {c_name} ({contender['size_gb']} GB)")
        log(f"    Mantenedor: {contender['maintainer']} | Arquitetura: {contender['arch']}")
        log(f"    Destilador: {contender['teacher']} | Quantização: {contender['quant']}")
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
                "timeout": 120.0,
                "max_tokens": 512,
                "temperature": 0.0
            },
            environment="local",
            context_window_chars=40000,
            verbose=False
        )

        opus_res = run_opus_benchmark(lambda_engine)
        stop_any_llama_server()

        proof_data[c_id] = {
            "name": c_name,
            "filename": c_fn,
            "maintainer": contender["maintainer"],
            "repo": c_repo,
            "teacher": contender["teacher"],
            "arch": contender["arch"],
            "quant": contender["quant"],
            "size_gb": contender["size_gb"],
            "speeds": speeds,
            "opus_passed": opus_res["passed"],
            "opus_total": opus_res["total"],
            "opus_pct": round((opus_res["passed"] / opus_res["total"]) * 100, 2),
            "opus_details": opus_res["details"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(PROOF_FILE, "w", encoding="utf-8") as f:
            json.dump(proof_data, f, indent=2, ensure_ascii=False)
        log(f"[+] Prova gravada com sucesso em {PROOF_FILE}!")

        # Purgar modelo do SSD para garantir espaço imediato para o próximo
        purge_local_model(model_path)

    log("\n[TORNEIO NEXT-GEN CONCLUÍDO] Todos os concorrentes foram avaliados com sucesso!")

if __name__ == "__main__":
    main()
