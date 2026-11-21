# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO DE EQUILIBRIO PARETO (Q4_K_M a F16/BF16) DOS 3 FINALISTAS 3B-4B
Comandante Primário: Mestre Ruan

Os 3 Finalistas da Faixa 3B a 4B:
1. ai9stars/G9v3-3B (bartowski/ai9stars_G9v3-3B-GGUF): Q4_K_M, Q5_K_M, Q6_K, Q8_0, BF16
2. Parable-Qwen3-4B-Fable5 (AnkitAI/Parable-Qwen3-4B-Claude-Fable-5-GGUF): Q4_K_M, Q5_K_M, Q6_K, Q8_0, F16
3. deadbydawn101-Gemma4-E4B (deadbydawn101/gemma-4-E4B-Agentic-Opus-Reasoning-GeminiCLI-GGUF): Q4_K_M, Q5_K_M, Q8_0, F16

Objetivo:
Medir bare-metal (14 threads Xeon AVX2, porta isolada 8089):
- Tempo de Boot, Prompt Processing (PP tok/s) e Text Generation (TG tok/s)
- 13 Areas Cognitivas (39 testes: Baseline + Lambda-RLM)
- 10 Desafios Opus Hard (AST formal + pytest + reparo por contraexemplo)
E identificar o ponto de equilibrio perfeito (velocidade x inteligencia) de cada finalista,
coroando o lider consensual da categoria 3B-4B.
"""

import os
import sys
import time
import json
import re
import shutil
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import Dict, Any

sys.stdout.reconfigure(encoding="utf-8")

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

SERVER_BIN = r"F:\AetherMind_LLM\bin\llama-server.exe"
BENCH_BIN = r"F:\AetherMind_LLM\bin\llama-bench.exe"
PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"

MODELS_DIR = Path(r"F:\models\finalistas_3b_4b")
ARCHIVE_DIR = Path(r"I:\AetherMind_High_Titans\finalistas_3b_4b_archive")
PROOF_FILE = Path(r"F:\data\proof_quants_finalistas_3b_4b.json")
LOG_FILE = Path(r"F:\data\tournament_quants_finalistas_3b_4b.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_quants_3b_4b.log")

CONTENDERS = [
    # --- 1. ai9stars/G9v3-3B ---
    {"id": "g9v3_3b__q4_k_m", "champ": "ai9stars/G9v3-3B", "champ_short": "G9v3-3B", "params": "3B", "teacher": "G9v3 Cognitive Distill", "quant": "Q4_K_M", "filename": "g9v3_3b__Q4_K_M.gguf"},
    {"id": "g9v3_3b__q5_k_m", "champ": "ai9stars/G9v3-3B", "champ_short": "G9v3-3B", "params": "3B", "teacher": "G9v3 Cognitive Distill", "quant": "Q5_K_M", "filename": "g9v3_3b__Q5_K_M.gguf"},
    {"id": "g9v3_3b__q6_k",   "champ": "ai9stars/G9v3-3B", "champ_short": "G9v3-3B", "params": "3B", "teacher": "G9v3 Cognitive Distill", "quant": "Q6_K",   "filename": "g9v3_3b__Q6_K.gguf"},
    {"id": "g9v3_3b__q8_0",   "champ": "ai9stars/G9v3-3B", "champ_short": "G9v3-3B", "params": "3B", "teacher": "G9v3 Cognitive Distill", "quant": "Q8_0",   "filename": "g9v3_3b__Q8_0.gguf"},
    {"id": "g9v3_3b__bf16",   "champ": "ai9stars/G9v3-3B", "champ_short": "G9v3-3B", "params": "3B", "teacher": "G9v3 Cognitive Distill", "quant": "BF16",   "filename": "g9v3_3b__BF16.gguf"},

    # --- 2. Parable-Qwen3-4B-Fable5 ---
    {"id": "parable_4b__q4_k_m", "champ": "Parable-Qwen3-4B-Fable5", "champ_short": "Parable-4B-Fable5", "params": "4B", "teacher": "Claude 3.5 + Fable 5", "quant": "Q4_K_M", "filename": "parable_4b_fable5__Q4_K_M.gguf"},
    {"id": "parable_4b__q5_k_m", "champ": "Parable-Qwen3-4B-Fable5", "champ_short": "Parable-4B-Fable5", "params": "4B", "teacher": "Claude 3.5 + Fable 5", "quant": "Q5_K_M", "filename": "parable_4b_fable5__Q5_K_M.gguf"},
    {"id": "parable_4b__q6_k",   "champ": "Parable-Qwen3-4B-Fable5", "champ_short": "Parable-4B-Fable5", "params": "4B", "teacher": "Claude 3.5 + Fable 5", "quant": "Q6_K",   "filename": "parable_4b_fable5__Q6_K.gguf"},
    {"id": "parable_4b__q8_0",   "champ": "Parable-Qwen3-4B-Fable5", "champ_short": "Parable-4B-Fable5", "params": "4B", "teacher": "Claude 3.5 + Fable 5", "quant": "Q8_0",   "filename": "parable_4b_fable5__Q8_0.gguf"},
    {"id": "parable_4b__f16",    "champ": "Parable-Qwen3-4B-Fable5", "champ_short": "Parable-4B-Fable5", "params": "4B", "teacher": "Claude 3.5 + Fable 5", "quant": "F16",    "filename": "parable_4b_fable5__F16.gguf"},

    # --- 3. deadbydawn101-Gemma4-E4B ---
    {"id": "gemma4_e4b__q4_k_m", "champ": "deadbydawn101-Gemma4-E4B", "champ_short": "Gemma4-E4B-Opus", "params": "4.5B", "teacher": "Claude Opus + GeminiCLI", "quant": "Q4_K_M", "filename": "gemma4_e4b_opus__Q4_K_M.gguf"},
    {"id": "gemma4_e4b__q5_k_m", "champ": "deadbydawn101-Gemma4-E4B", "champ_short": "Gemma4-E4B-Opus", "params": "4.5B", "teacher": "Claude Opus + GeminiCLI", "quant": "Q5_K_M", "filename": "gemma4_e4b_opus__Q5_K_M.gguf"},
    {"id": "gemma4_e4b__q8_0",   "champ": "deadbydawn101-Gemma4-E4B", "champ_short": "Gemma4-E4B-Opus", "params": "4.5B", "teacher": "Claude Opus + GeminiCLI", "quant": "Q8_0",   "filename": "gemma4_e4b_opus__Q8_0.gguf"},
    {"id": "gemma4_e4b__f16",    "champ": "deadbydawn101-Gemma4-E4B", "champ_short": "Gemma4-E4B-Opus", "params": "4.5B", "teacher": "Claude Opus + GeminiCLI", "quant": "F16",    "filename": "gemma4_e4b_opus__F16.gguf"},
]


def log(msg: str):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def kill_port_8089():
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"(Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue).OwningProcess"],
            capture_output=True, text=True, timeout=8
        )
        pids = [p.strip() for p in res.stdout.split() if p.strip().isdigit()]
        for pid in set(pids):
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        time.sleep(0.8)
    except Exception as e:
        log(f"[!] Aviso ao limpar porta {PORT}: {e}")


def benchmark_cpu_speed(model_path: Path) -> Dict[str, float]:
    log(f"  [*] Medindo throughput CPU puro (Xeon AVX2 -t 14 -fa 1) via llama-bench: {model_path.name}...")
    cmd = [
        BENCH_BIN, "-m", str(model_path),
        "-ngl", "0", "-t", "14", "-fa", "1", "-p", "128", "-n", "32", "-r", "1", "-o", "json"
    ]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        stdout = res.stdout.strip()
        start_idx = stdout.find("[")
        end_idx = stdout.rfind("]")
        if start_idx != -1 and end_idx != -1:
            rows = json.loads(stdout[start_idx:end_idx + 1])
            cpu_pp = 0.0
            cpu_tg = 0.0
            for r in rows:
                if r.get("n_prompt", 0) > 0:
                    cpu_pp = round(float(r.get("avg_ts", 0.0)), 2)
                elif r.get("n_gen", 0) > 0:
                    cpu_tg = round(float(r.get("avg_ts", 0.0)), 2)
            log(f"   [CPU AVX2 PROOF] PP: {cpu_pp:.2f} tok/s | TG: {cpu_tg:.2f} tok/s")
            return {"cpu_pp_tok_s": cpu_pp, "cpu_tg_tok_s": cpu_tg}
    except Exception as e:
        log(f"[!] Aviso no benchmark CPU: {e}")
    return {"cpu_pp_tok_s": 0.0, "cpu_tg_tok_s": 0.0}


def start_llama_server(model_path: Path) -> tuple[subprocess.Popen, float, int]:
    kill_port_8089()
    if not model_path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

    size_gb = model_path.stat().st_size / (1024**3)
    if size_gb <= 5.2:
        ngl_candidates = [99, 24, 0]
    elif size_gb <= 6.2:
        ngl_candidates = [99, 22, 14, 0]
    elif size_gb <= 8.0:
        ngl_candidates = [20, 12, 0]
    else:
        ngl_candidates = [12, 0]

    for ngl in ngl_candidates:
        kill_port_8089()
        log(f"[*] Subindo llama-server b12420 (-ngl {ngl} | -np 1 | -fa on | -t 14): {model_path.name}...")
        log_fp = open(SERVER_LOG_FILE, "a", encoding="utf-8")
        cmd = [
            SERVER_BIN,
            "-m", str(model_path),
            "-c", "4096",
            "-np", "1",
            "-fa", "on",
            "-ngl", str(ngl),
            "-b", "512",
            "-ub", "512",
            "-t", "14",
            "--port", str(PORT),
            "--host", "127.0.0.1",
            "--cont-batching",
        ]
        p = subprocess.Popen(
            cmd,
            stdout=log_fp,
            stderr=subprocess.STDOUT,
        )

        t0 = time.time()
        ready = False
        early_exit = False
        while time.time() - t0 < 180.0:
            if p.poll() is not None:
                log(f"[!] llama-server (-ngl {ngl}) encerrou (código {p.returncode}). Tentando próximo degrau...")
                early_exit = True
                break
            try:
                req = urllib.request.Request(f"{BASE_URL}/health")
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.5)

        if ready:
            boot_time = round(time.time() - t0, 2)
            log(f"[+] Servidor 200 OK (-ngl {ngl}) em {boot_time}s!")
            return p, boot_time, ngl

        if not early_exit:
            kill_port_8089()

    raise RuntimeError(f"Falha ao subir servidor em todos os níveis de -ngl para {model_path.name}")


def benchmark_speed(boot_s: float) -> Dict[str, float]:
    log("  [*] Medindo throughput bare-metal (PP tok/s e TG tok/s)...")
    prompt = "Explique a diferenca entre um compilador e um interpretador em computacao de alta performance."
    payload = json.dumps({
        "prompt": prompt,
        "n_predict": 96,
        "temperature": 0.0,
        "ignore_eos": True
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=120.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elapsed = max(0.01, time.time() - t0)
            timings = data.get("timings", {})
            pp_speed = timings.get("prompt_per_second", 0.0)
            tg_speed = timings.get("predicted_per_second", 0.0)

            if tg_speed <= 0.0 or tg_speed > 5000.0:
                pred_ms = timings.get("predicted_ms", 0.0)
                pred_n = timings.get("predicted_n", 96)
                tg_speed = (pred_n / (pred_ms / 1000.0)) if pred_ms > 1.0 else (96.0 / elapsed)

            log(f"   [SPEED PROOF] Boot: {boot_s}s | PP: {pp_speed:.2f} tok/s | TG: {tg_speed:.2f} tok/s")
            return {
                "boot_seconds": boot_s,
                "prompt_per_second": round(pp_speed, 2),
                "predicted_per_second": round(tg_speed, 2),
            }
    except Exception as e:
        log(f"[!] Erro ao medir velocidade: {e}")
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


def query_fast_direct(prompt: str, is_code: bool = False, max_tokens: int = 768) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown." if is_code else clean

    payload = json.dumps({
        "messages": [{"role": "user", "content": eff_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=480.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if not content:
                content = (msg.get("reasoning_content") or "").strip()
            if content:
                return content
    except urllib.error.HTTPError:
        pass
    except Exception:
        return ""

    payload2 = json.dumps({
        "prompt": f"<|im_start|>user\n{eff_prompt}\n<|im_end|>\n<|im_start|>assistant\n",
        "n_predict": max_tokens,
        "temperature": 0.0,
        "stop": ["<|im_end|>", "<|endoftext|>", "</s>"]
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=480.0) as r2:
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
        ans = res.response.strip()
        if ans and not ans.startswith("[ERROR:"):
            return ans
    except Exception:
        pass
    return query_fast_direct(prompt, is_code=is_code, max_tokens=768)


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

            out = query_fast_direct(p, is_code=is_code, max_tokens=768 if is_code else 448)
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

        passed = False
        res_str = "FAIL"

        try:
            raw = query_fast_direct(prompt, is_code=True, max_tokens=1024)
            code = clean_python_code(raw)
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=8.0)
            if ver.passed:
                passed = True
                base_passed += 1
                opus_passed += 1
                res_str = "PASS (Baseline)"
            else:
                retry_p = f"{prompt}\nATENCAO: A implementacao anterior falhou ({ver.details or 'erro'}). Escreva estritamente a funcao Python correta sem sintaxe quebrada e tratando todos edge cases."
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

        opus_details[t_id] = {
            "name": t_name,
            "passed": passed,
            "result": res_str
        }
        log(f"    -> {t_id} ({t_name[:30]}): {res_str}")

    opus_pct = round((opus_passed / 10) * 100, 2)
    log(f"  [+] Pontuação Final Opus Hard: {opus_passed}/10 ({opus_pct}%) [Baseline: {base_passed}/10]")
    return {
        "baseline_passed": base_passed,
        "passed": opus_passed,
        "total": 10,
        "pct": opus_pct,
        "details": opus_details
    }


def prepare_wave2_space_and_download(results: dict):
    f16_target = MODELS_DIR / "gemma4_e4b_opus__F16.gguf"
    if f16_target.exists():
        return
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    for fn, cid in [("g9v3_3b__BF16.gguf", "g9v3_3b__bf16"), ("parable_4b_fable5__F16.gguf", "parable_4b__f16")]:
        src = MODELS_DIR / fn
        if src.exists() and results.get(cid, {}).get("completed"):
            dst = ARCHIVE_DIR / fn
            log(f"[*] Arquivando {fn} já avaliado para {dst} para liberar espaço NVMe para Wave 2...")
            shutil.move(str(src), str(dst))
    log("[*] Disparando Download Wave 2 (gemma4_e4b_opus__F16.gguf - 14.02 GB)...")
    subprocess.run([sys.executable, str(ROTOR_ROOT / "download_finalistas_3b_4b_quants.py"), "--wave2"], check=False)


def main():
    log("=" * 80)
    log("AETHERMIND — TORNEIO DE EQUILIBRIO (Q4_K_M a F16) DOS 3 FINALISTAS 3B-4B")
    log("=" * 80)

    results = {}
    if PROOF_FILE.exists():
        try:
            results = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
            log(f"[*] Carregado histórico com {len(results)} variantes concluídas.")
        except Exception:
            results = {}

    for idx, c in enumerate(CONTENDERS, 1):
        c_id = c["id"]
        c_name = f"{c['champ_short']} [{c['quant']}]"
        model_path = MODELS_DIR / c["filename"]

        if c_id == "gemma4_e4b__f16" and not model_path.exists():
            prepare_wave2_space_and_download(results)

        log("\n" + "#" * 80)
        log(f"[{idx}/{len(CONTENDERS)}] PROCESSANDO: {c_name} ({c['params']})")
        log(f"   Campeão: {c['champ']} | Quant: {c['quant']} | Professor: {c['teacher']}")
        log(f"   Arquivo: {model_path}")
        log("#" * 80)

        if c_id in results and results[c_id].get("completed", False):
            log(f"[+] {c_name} já avaliado ({results[c_id]['score_13_areas']}/39 | Opus: {results[c_id]['score_opus']}/10 | TG: {results[c_id]['tg_tok_s']} t/s). Pulando...")
            continue

        part_path = Path(str(model_path) + ".part")
        if not model_path.exists() and part_path.exists():
            log(f"[*] Arquivo {model_path.name} ainda em download (.part detectado). Aguardando conclusão...")
            while part_path.exists() and not model_path.exists():
                time.sleep(5.0)
            time.sleep(1.0)

        if not model_path.exists():
            log(f"[!] Arquivo ausente: {model_path}. Pulando...")
            continue

        proc = None
        try:
            cpu_speed_info = benchmark_cpu_speed(model_path)
            proc, boot_s, active_ngl = start_llama_server(model_path)
            speed_info = benchmark_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model_path.name,
                    "base_url": f"{BASE_URL}/v1",
                    "api_key": "none",
                    "max_tokens": 768,
                    "temperature": 0.0,
                    "timeout": 480.0,
                },
                context_window_chars=4096,
                verbose=False
            )

            res_13 = run_13_areas(lambda_engine)
            res_opus = run_opus(lambda_engine)

            results[c_id] = {
                "champ": c["champ"],
                "champ_short": c["champ_short"],
                "params": c["params"],
                "teacher": c["teacher"],
                "quant": c["quant"],
                "size_mb": round(model_path.stat().st_size / (1024**2), 2),
                "active_ngl": active_ngl,
                "speed": speed_info,
                "boot_seconds": speed_info["boot_seconds"],
                "pp_tok_s": speed_info["prompt_per_second"],
                "tg_tok_s": speed_info["predicted_per_second"],
                "cpu_pp_tok_s": cpu_speed_info["cpu_pp_tok_s"],
                "cpu_tg_tok_s": cpu_speed_info["cpu_tg_tok_s"],
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
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            PROOF_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log(f"[+] Prova gravada em {PROOF_FILE.name}!")

        except Exception as e:
            log(f"[!] Erro ao testar {c_name}: {e}")
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            kill_port_8089()
            time.sleep(1.0)

    log("\n" + "=" * 80)
    log("[+] TORNEIO DE EQUILIBRIO 3B-4B FINALIZADO COM SUCESSO!")
    log("=" * 80)


if __name__ == "__main__":
    main()
