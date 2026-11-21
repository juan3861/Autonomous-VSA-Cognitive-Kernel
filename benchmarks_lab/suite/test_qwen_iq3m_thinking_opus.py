# -*- coding: utf-8 -*-
"""
AETHERMIND — TESTE DE RACIOCÍNIO DESTRAVADO (<think>) NO LÍDER DE AMPLITUDE
Modelo: Qwen_Qwen3-30B-A3B-IQ3_M.gguf (13.11 GB)
Objetivo: Extrair raciocínio algorítmico profundo nos 10 Desafios Opus (LeetCode Hard)
          com scratchpad reflexivo destravado e verificação formal AST/pytest.
"""

import os
import sys
import time
import json
import re
import shutil
import subprocess
import urllib.request
from pathlib import Path
from typing import Dict, Any

ROTOR_ROOT = Path(r"F:\rotor-llm")
LAMBDA_RLM_DIR = ROTOR_ROOT / "lambda_rlm"
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))
if str(LAMBDA_RLM_DIR) not in sys.path:
    sys.path.insert(0, str(LAMBDA_RLM_DIR))

from duelo_nivel_opus_8b_vs_9b import OPUS_10_TESTS
from router.formal_verifier import formal_verifier
from rlm import LambdaRLM

SERVER_BIN = r"F:\tools\lc\bin\llama-server.exe"
PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"
LOCAL_DIR = Path(r"F:\AetherMind_Contenders")
LOCAL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_FILENAME = "Qwen_Qwen3-30B-A3B-IQ3_M.gguf"
MODEL_LOCAL_PATH = LOCAL_DIR / MODEL_FILENAME
GDRIVE_SOURCE = f"gdrive_01:AetherMind_High_Titans/{MODEL_FILENAME}"

RCLONE_BIN = r"C:\Users\juanp\.gemini\antigravity\scratch\aether_gdrive_turbo\bin\rclone.exe"
RCLONE_CONF = r"C:\Users\juanp\.gemini\antigravity\scratch\aether_gdrive_turbo\config\rclone.conf"

PROOF_FILE = Path(r"F:\data\proof_qwen_iq3m_thinking_opus.json")
LOG_FILE = Path(r"F:\data\qwen_iq3m_thinking_opus.log")

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

def wait_for_disk_space(required_gb: float = 14.0):
    log(f"[*] Aguardando espaço em disco no SSD F:\\ (necessário: {required_gb:.1f} GB livres)...")
    while True:
        free_gb = shutil.disk_usage("F:").free / (1024**3)
        if free_gb >= required_gb:
            log(f"[+] Espaço suficiente detectado em F:\\: {free_gb:.2f} GB livres.")
            break
        log(f"    Espaço atual: {free_gb:.2f} GB livres. Aguardando finalização da tarefa anterior...")
        time.sleep(15.0)

def ensure_model_local() -> Path:
    if MODEL_LOCAL_PATH.exists() and MODEL_LOCAL_PATH.stat().st_size > 10 * 1024**3:
        log(f"[+] Modelo já presente no SSD local: {MODEL_LOCAL_PATH.name} ({MODEL_LOCAL_PATH.stat().st_size / (1024**3):.2f} GB)")
        return MODEL_LOCAL_PATH

    wait_for_disk_space(15.0)

    log(f"[*] Copiando {MODEL_FILENAME} do Google Drive para o SSD local...")
    cmd = [
        RCLONE_BIN, "copy",
        GDRIVE_SOURCE,
        str(LOCAL_DIR),
        "--config", RCLONE_CONF,
        "--drive-chunk-size", "64M",
        "--transfers", "4"
    ]
    subprocess.run(cmd, check=True)

    if MODEL_LOCAL_PATH.exists() and MODEL_LOCAL_PATH.stat().st_size > 10 * 1024**3:
        log(f"[+] Modelo transferido com sucesso: {MODEL_LOCAL_PATH.name} ({MODEL_LOCAL_PATH.stat().st_size / (1024**3):.2f} GB)")
        return MODEL_LOCAL_PATH
    else:
        raise RuntimeError("Falha ao transferir modelo do Google Drive.")

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
    log(f"-> Subindo llama-server Turbo (14 threads Xeon, AVX2 batch=512): {model_path.name}...")
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

def query_with_deep_thinking(lambda_engine: LambdaRLM, prompt: str) -> str:
    clean_p = prompt.replace("/no_think", "").strip()
    eff_prompt = (
        f"{clean_p}\n\n"
        "Instruções Estritas de Raciocínio:\n"
        "1. Pense detalhadamente sobre o algoritmo, invariantes de loop e casos de borda usando <think> ... </think>.\n"
        "2. Após o pensamento, forneça APENAS o código Python puro dentro de um bloco ```python ... ```.\n"
        "3. Não inclua texto explicativo fora do bloco de código ou do <think>."
    )
    try:
        res = lambda_engine.completion(eff_prompt)
        return res.response.strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def run_opus_with_thinking(lambda_engine: LambdaRLM) -> Dict[str, Any]:
    log("  [*] Executando Bateria 10 Desafios Opus com <think> DESTRAVADO...")
    opus_passed = 0
    opus_details = {}

    for test in OPUS_10_TESTS:
        t_id = test["id"]
        t_name = test["name"]
        prompt = test["prompt"]
        assertions = test["assertions"]

        log(f"    -> {t_id} ({t_name[:35]})...")
        try:
            raw_response = query_with_deep_thinking(lambda_engine, prompt)
            code = clean_python_code(raw_response)
            try:
                ver = formal_verifier.verify_python_code(code, assertions, timeout_s=15.0)
                passed = ver.passed
            except Exception:
                passed = False

            if passed:
                opus_passed += 1
                res_str = "PASS (DeepThinking-RLM)"
            else:
                res_str = "FAIL"
        except Exception as e:
            res_str = f"ERROR ({e})"

        log(f"       Resultado: {res_str}")
        opus_details[t_id] = res_str

    log(f"  [+] Pontuação Final Opus com Thinking: {opus_passed}/{len(OPUS_10_TESTS)} ({(opus_passed/len(OPUS_10_TESTS))*100:.1f}%)")
    return {"passed": opus_passed, "total": len(OPUS_10_TESTS), "details": opus_details}

def main():
    log("================================================================================")
    log("AETHERMIND — TESTE DE RACIOCÍNIO PROFUNDO (<think>) NO QWEN_QWEN3-30B-A3B-IQ3_M")
    log("================================================================================")

    model_path = ensure_model_local()
    proc = start_server(model_path)

    lambda_engine = LambdaRLM(
        backend="openai",
        backend_kwargs={
            "model_name": MODEL_FILENAME,
            "base_url": f"{BASE_URL}/v1",
            "api_key": "none",
            "timeout": 180.0,
            "max_tokens": 1024,
            "temperature": 0.0
        },
        environment="local",
        context_window_chars=40000,
        verbose=False
    )

    opus_res = run_opus_with_thinking(lambda_engine)
    stop_any_llama_server()

    proof_data = {
        "model": "Qwen_Qwen3-30B-A3B-IQ3_M",
        "mode": "DeepThinking-Unchained (<think>)",
        "opus_passed": opus_res["passed"],
        "opus_total": opus_res["total"],
        "opus_pct": round((opus_res["passed"] / opus_res["total"]) * 100, 2),
        "opus_details": opus_res["details"],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(PROOF_FILE, "w", encoding="utf-8") as f:
        json.dump(proof_data, f, indent=2, ensure_ascii=False)
    log(f"[+] Prova gravada com sucesso em {PROOF_FILE}!")

    if MODEL_LOCAL_PATH.exists():
        try:
            MODEL_LOCAL_PATH.unlink()
            free_gb = shutil.disk_usage("F:").free / (1024**3)
            log(f"[+] {MODEL_LOCAL_PATH.name} removido do SSD local. Espaço livre restaurado em F:\\: {free_gb:.2f} GB.")
        except Exception as e:
            log(f"[!] Falha ao remover {MODEL_LOCAL_PATH.name}: {e}")

if __name__ == "__main__":
    main()
