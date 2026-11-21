# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO DA FAMÍLIA IFM K2-HORIZON (3.7B, 0.9B, 7B)
Avaliação Bare-Metal das 13 Áreas Cognitivas (39 Provas) + 10 Desafios Opus Hard sob Lambda-RLM
Comandante Primário: Mestre Ruan

Modelos:
  - Frente 1: K2-Horizon-3.7B (Q5_K_M, Q6_K, Q4_K_M, Q8_0) -> Entrada da Camada Média (Sweet Spot)
  - Frente 2: K2-Horizon-0.9B (Q4_K_M, Q5_K_M, Q6_K, Q8_0) -> Gladiador Pesos-Mosca vs TinyQwen3 / MiniCPM4
  - Frente 3: K2-Horizon-7B   (Q4_K_M, Q5_K_M)               -> Camada Média Clássica (Híbrido GPU+CPU)
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

# Verificação obrigatória de dependências
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

MODELS_DIR = Path(r"F:\models\k2_horizon")
PROOF_FILE = Path(r"F:\data\proof_k2_horizon_completo.json")
LOG_FILE   = Path(r"F:\data\tournament_k2_horizon.log")
SERVER_LOG = Path(r"F:\data\llama_server_k2_horizon.log")

HF = "https://huggingface.co"

CHALLENGERS = [
    # ── FRENTE 1: K2-HORIZON-3.7B (Camada Média Compacta) ──
    {
        "id": "k2_horizon_3_7b__q5_k_m",
        "family": "K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "tier": "3.7B", "params": "3.7B",
        "quant": "Q5_K_M", "fa_off": False, "thinking": True,
        "filename": "K2-Horizon-4B-Q5_K_M.gguf",
        "url": f"{HF}/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q6_k",
        "family": "K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "tier": "3.7B", "params": "3.7B",
        "quant": "Q6_K", "fa_off": False, "thinking": True,
        "filename": "K2-Horizon-4B-Q6_K.gguf",
        "url": f"{HF}/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q4_k_m",
        "family": "K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "tier": "3.7B", "params": "3.7B",
        "quant": "Q4_K_M", "fa_off": False, "thinking": True,
        "filename": "K2-Horizon-4B-Q4_K_M.gguf",
        "url": f"{HF}/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q8_0",
        "family": "K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "tier": "3.7B", "params": "3.7B",
        "quant": "Q8_0", "fa_off": False, "thinking": True,
        "filename": "K2-Horizon-4B-Q8_0.gguf",
        "url": f"{HF}/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf",
    },
    # ── FRENTE 2: K2-HORIZON-0.9B (Gladiador Pesos-Mosca) ──
    {
        "id": "k2_horizon_0_9b__q4_k_m",
        "family": "K2-Horizon-0.9B",
        "champ_short": "K2-Horizon-0.9B",
        "tier": "900M", "params": "0.9B",
        "quant": "Q4_K_M", "fa_off": False, "thinking": False,
        "filename": "K2-Horizon-1B-Q4_K_M.gguf",
        "url": f"{HF}/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q4_K_M.gguf",
    },
    {
        "id": "k2_horizon_0_9b__q5_k_m",
        "family": "K2-Horizon-0.9B",
        "champ_short": "K2-Horizon-0.9B",
        "tier": "900M", "params": "0.9B",
        "quant": "Q5_K_M", "fa_off": False, "thinking": False,
        "filename": "K2-Horizon-1B-Q5_K_M.gguf",
        "url": f"{HF}/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q5_K_M.gguf",
    },
    {
        "id": "k2_horizon_0_9b__q6_k",
        "family": "K2-Horizon-0.9B",
        "champ_short": "K2-Horizon-0.9B",
        "tier": "900M", "params": "0.9B",
        "quant": "Q6_K", "fa_off": False, "thinking": False,
        "filename": "K2-Horizon-1B-Q6_K.gguf",
        "url": f"{HF}/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q6_K.gguf",
    },
    # ── FRENTE 3: K2-HORIZON-7B (Camada Média Clássica) ──
    {
        "id": "k2_horizon_0_9b__q8_0",
        "family": "K2-Horizon-0.9B",
        "champ_short": "K2-Horizon-0.9B",
        "tier": "900M", "params": "0.9B",
        "quant": "Q8_0", "fa_off": False, "thinking": False, "ngl": 99,
        "filename": "K2-Horizon-1B-Q8_0.gguf",
        "url": f"{HF}/IFM/K2-Horizon-0.9B-GGUF/resolve/main/K2-Horizon-1B-Q8_0.gguf",
    },
    {
        "id": "k2_horizon_7b__q4_k_m",
        "family": "K2-Horizon-7B",
        "champ_short": "K2-Horizon-7B",
        "tier": "7B", "params": "7.0B",
        "quant": "Q4_K_M", "fa_off": False, "thinking": True, "ngl": 99,
        "filename": "K2-Horizon-7B-Q4_K_M.gguf",
        "url": f"{HF}/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q4_K_M.gguf",
    },
    {
        "id": "k2_horizon_7b__q5_k_m",
        "family": "K2-Horizon-7B",
        "champ_short": "K2-Horizon-7B",
        "tier": "7B", "params": "7.0B",
        "quant": "Q5_K_M", "fa_off": False, "thinking": True, "ngl": 24,
        "filename": "K2-Horizon-7B-Q5_K_M.gguf",
        "url": f"{HF}/IFM/K2-Horizon-7B-GGUF/resolve/main/K2-Horizon-7B-Q5_K_M.gguf",
    },
]

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def kill_llama():
    subprocess.run(
        ["taskkill", "/F", "/IM", "llama-server.exe", "/T"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    time.sleep(1.0)

def download_if_needed(url: str, dest: Path) -> bool:
    if dest.exists() and dest.stat().st_size > 10 * 1024 * 1024:
        log(f"[*] Arquivo ja presente: {dest.name} ({dest.stat().st_size / (1024**2):.1f} MB)")
        return True

    temp_dest = dest.with_suffix(".part")
    log(f"[*] Baixando: {url}")
    log(f"    -> Destino temporario: {temp_dest.name}")

    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(url, headers=headers)

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120.0) as resp, open(temp_dest, "wb") as out:
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            last_p = 0
            while True:
                chunk = resp.read(8 * 1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = int(downloaded * 100 / total)
                    if pct >= last_p + 15:
                        speed = downloaded / (time.time() - t0) / (1024**2)
                        log(f"    ... {pct}% ({downloaded / (1024**2):.1f}/{total / (1024**2):.1f} MB) a {speed:.1f} MB/s")
                        last_p = pct
        temp_dest.rename(dest)
        el = time.time() - t0
        log(f"[+] Download concluido em {el:.1f}s: {dest.name} ({dest.stat().st_size / (1024**2):.1f} MB)")
        return True
    except Exception as e:
        log(f"[!] ERRO no download de {url}: {e}")
        if temp_dest.exists():
            temp_dest.unlink()
        return False

def benchmark_cpu_speed(model_path: Path, fa_off: bool = False) -> Dict[str, float]:
    log("  [*] Medindo velocidade nativa CPU AVX2 via llama-bench...")
    cmd = [
        str(BENCH_BIN),
        "-m", str(model_path),
        "-n", "32",
        "-p", "128",
        "-ngl", "0",
        "--device", "none",
        "-t", "8",
        "-r", "1",
    ]
    if fa_off:
        cmd += ["-fa", "0"]
    else:
        cmd += ["-fa", "1"]

    pp_speed = 0.0
    tg_speed = 0.0
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=240)
        out = res.stdout + res.stderr
        for line in out.splitlines():
            line_s = line.strip()
            if "pp128" in line_s or "pp256" in line_s:
                m = re.search(r"([\d\.]+)\s*±\s*[\d\.]+", line_s)
                if m:
                    pp_speed = float(m.group(1))
            elif "tg32" in line_s or "tg64" in line_s:
                m = re.search(r"([\d\.]+)\s*±\s*[\d\.]+", line_s)
                if m:
                    tg_speed = float(m.group(1))
    except Exception as e:
        log(f"  [!] Aviso: llama-bench CPU falhou: {e}")

    log(f"  [+] Throughput CPU: Prompt={pp_speed:.2f} t/s | Geracao={tg_speed:.2f} t/s")
    return {"cpu_pp_tok_s": pp_speed, "cpu_tg_tok_s": tg_speed}

def start_llama_server(model_path: Path, fa_off: bool = False, ngl: int = 99):
    attempts = [
        (ngl, [], "Vulkan GPU"),
        (0, ["--device", "none"], "CPU AVX2 Fallback (--device none)"),
    ]
    for try_ngl, extra_args, label in attempts:
        kill_llama()
        time.sleep(1.5)

        log(f"  [*] Iniciando llama-server para {model_path.name} [{label} | -ngl {try_ngl}]...")
        cmd = [
            str(SERVER_BIN),
            "-m", str(model_path),
            "--host", "127.0.0.1",
            "--port", str(PORT),
            "-ngl", str(try_ngl),
            "--fit", "off",
            "-c", "4096",
            "-cb",
            "-np", "1",
            "-t", "8",
        ] + extra_args
        if fa_off:
            cmd += ["-fa", "0"]
        else:
            cmd += ["-fa", "1"]

        server_f = open(SERVER_LOG, "w", encoding="utf-8")
        t_start = time.time()
        proc = subprocess.Popen(
            cmd,
            stdout=server_f,
            stderr=subprocess.STDOUT,
            text=True,
        )

        ready = False
        boot_s = 0.0
        for _ in range(360):
            time.sleep(0.5)
            if proc.poll() is not None:
                log(f"  [!] Tentativa {label} encerrou com codigo {proc.returncode}.")
                break
            try:
                req = urllib.request.Request(f"{BASE_URL}/health")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        ready = True
                        boot_s = round(time.time() - t_start, 2)
                        break
            except Exception:
                pass

        if ready:
            log(f"  [+] llama-server ONLINE ({label}) em {boot_s:.2f}s!")
            return proc, boot_s, try_ngl

        kill_llama()

    log("  [!] Todas as tentativas de subir llama-server falharam.")
    return None, 0.0, 0

def benchmark_speed(boot_s: float) -> Dict[str, float]:
    log("  [*] Medindo velocidade de inferencia GPU Vulkan via servidor HTTP...")
    payload = json.dumps({
        "prompt": "Explique resumidamente em portugues o principio fundamental da entropia.",
        "n_predict": 64,
        "temperature": 0.0,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/completion",
        data=payload,
        headers={"Content-Type": "application/json"},
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=40.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            timings = data.get("timings", {})
            pp_speed = timings.get("prompt_per_second", 0.0)
            tg_speed = timings.get("predicted_per_second", 0.0)
            if tg_speed == 0.0:
                elapsed = time.time() - t0
                toks = timings.get("predicted_n", 64)
                tg_speed = toks / max(elapsed, 0.01)
    except Exception as e:
        log(f"  [!] Aviso: benchmark HTTP GPU falhou: {e}")
        pp_speed, tg_speed = 0.0, 0.0

    log(f"  [+] Throughput GPU: Prompt={pp_speed:.2f} t/s | Geracao={tg_speed:.2f} t/s | Boot={boot_s:.2f}s")
    return {"boot_seconds": boot_s, "pp_tok_s": pp_speed, "tg_tok_s": tg_speed}

def extract_text_after_think(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    cleaned = re.sub(r"^.*?<\/think>", "", cleaned, flags=re.DOTALL)
    return cleaned.strip()

def clean_python_code(raw: str) -> str:
    text = extract_text_after_think(raw)
    if "```python" in text:
        text = text.split("```python", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    return text.strip()

def query_fast_direct(prompt: str, is_code: bool = False, max_tokens: int = 768) -> str:
    system_inst = (
        "Voce e um motor de computacao formal ultra-rigoroso. Responda com precisao cirurgica."
        if not is_code else
        "Voce e um especialista em engenharia de software Python. Escreva estritamente o codigo Python solicitado, sem markdown, sem explicacoes."
    )
    payload = json.dumps({
        "messages": [
            {"role": "system", "content": system_inst},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.0,
        "max_tokens": max_tokens,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{BASE_URL}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=240.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"]

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
    log("AETHERMIND — TORNEIO DA FAMÍLIA IFM K2-HORIZON (3.7B, 0.9B, 7B)")
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
        log(f"[{idx}/{len(CHALLENGERS)}] {c_name} (Familia: {c['family']})")
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
            proc, boot_s, active_ngl = start_llama_server(model_path, fa_off=c["fa_off"], ngl=c.get("ngl", 99))
            if proc is None:
                log(f"[!] Erro ao subir servidor para {c_name}. Pulando.")
                continue

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
            )

            res_13a = run_13_areas(lambda_engine, thinking=c["thinking"])
            res_opus = run_opus(lambda_engine, thinking=c["thinking"])

            rec = {
                "id": c_id,
                "family": c["family"],
                "champ_short": c["champ_short"],
                "tier": c["tier"],
                "quant": c["quant"],
                "size_mb": size_mb,
                "active_ngl": active_ngl,
                "boot_seconds": gpu_info["boot_seconds"],
                "pp_tok_s": gpu_info["pp_tok_s"],
                "tg_tok_s": gpu_info["tg_tok_s"],
                "cpu_pp_tok_s": cpu_info["cpu_pp_tok_s"],
                "cpu_tg_tok_s": cpu_info["cpu_tg_tok_s"],
                "score_13_areas": res_13a["passed"],
                "baseline_13_areas": res_13a["baseline_passed"],
                "pct_13_areas": res_13a["pct"],
                "perfect_areas_count": res_13a["perfect_areas_count"],
                "score_opus": res_opus["passed"],
                "baseline_opus": res_opus["baseline_passed"],
                "pct_opus": res_opus["pct"],
                "details_13_areas": res_13a,
                "details_opus": res_opus,
                "completed": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }

            results[c_id] = rec
            PROOF_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            log(f"[+] PROVA GRAVADA COM SUCESSO: {c_id} -> {res_13a['passed']}/39 e {res_opus['passed']}/10 Opus")

        finally:
            kill_llama()
            if model_path.exists():
                try:
                    model_path.unlink()
                    log(f"[*] Limpeza de disco: {model_path.name} removido para liberar espaço.")
                except Exception as e:
                    log(f"[!] Erro ao remover {model_path.name}: {e}")

    log("\n" + "=" * 80)
    log("[🏆] TORNEIO K2-HORIZON FINALIZADO COM SUCESSO!")
    log("=" * 80)

if __name__ == "__main__":
    main()
