# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO MUNDIAL DOS DESAFIANTES DE 100M A 200M — TIER-1 TEACHERS
Comandante Primário: Mestre Ruan

Busca Exaustiva pelos 3 Melhores Modelos do Mundo entre 100M e 200M:
- Professores de 1ª Classe: DeepSeek V4 Pro, OpenAI GPT-5.5, Alibaba Qwen2.5/Qwen3, TII Falcon, Zephyr DPO, Meta MobileLLM, Platypus, Cerebras, Mistral.

Baterias Avaliadas:
1. 13 Áreas Cognitivas AetherMind (39 testes rigorosos)
2. 10 Desafios de Nível Opus Hard (AST formal & pytest)
3. Medição Bare-Metal: Boot time, Prompt Processing (tok/s), Text Generation (tok/s)
"""

import os
import sys
import time
import json
import re
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, List

sys.stdout.reconfigure(encoding='utf-8')

ROTOR_ROOT = Path(r"F:\rotor-llm")
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))

from benchmark_13_areas_39_testes import BENCHMARK_SUITE
from duelo_nivel_opus_8b_vs_9b import OPUS_10_TESTS
from router.formal_verifier import formal_verifier

SERVER_BIN = r"F:\tools\lc_b10749\llama-server.exe"
PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"

PROOF_FILE = Path(r"F:\data\proof_torneio_desafiantes_100m_200m.json")
LOG_FILE = Path(r"F:\data\tournament_desafiantes_100m_200m.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_desafiantes_100m_200m.log")

CONTENDERS = [
    {
        "id": "qwen25_02b_q4_k_m",
        "name": "Qwen2.5-0.2B",
        "local_path": r"F:\models\desafiantes_100m_200m\Qwen2.5-0.2B.Q4_K_M.gguf",
        "size_mb": 201.4,
        "params": "200M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "Alibaba Qwen2.5 Dense Native",
    },
    {
        "id": "qwen3_pruned_02b_q4_k_m",
        "name": "Qwen3-0.6B-Pruned-0.2B",
        "local_path": r"F:\models\desafiantes_100m_200m\Qwen3-0.6B-Pruned-0.2B.Q4_K_M.gguf",
        "size_mb": 145.3,
        "params": "200M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "Qwen3 Structural Pruning",
    },
    {
        "id": "falcon_h1_tiny_100m_q4_k_m",
        "name": "Falcon-H1-Tiny-Multilingual-100M-Instruct",
        "local_path": r"F:\models\desafiantes_100m_200m\Falcon-H1-Tiny-Multilingual-100M-Instruct.Q4_K_M.gguf",
        "size_mb": 70.5,
        "params": "100M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "TII Falcon H1 Multilingual Instruct",
    },
    {
        "id": "zephyr_smol_llama_100m_dpo_q4_k_m",
        "name": "zephyr-smol_llama-100m-dpo",
        "local_path": r"F:\models\desafiantes_100m_200m\zephyr-smol_llama-100m-dpo-full.q4_k_m.gguf",
        "size_mb": 63.3,
        "params": "100M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "Zephyr DPO Alignment (SmolLlama 100M)",
    },
    {
        "id": "smollm2_135m_heretic_q4_k_m",
        "name": "SmolLM2-135M-Instruct-heretic",
        "local_path": r"F:\models\desafiantes_100m_200m\SmolLM2-135M-Instruct-heretic.Q4_K_M.gguf",
        "size_mb": 100.6,
        "params": "135M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "SmolLM2 FineWeb-Edu Heretic Tuned",
    },
    {
        "id": "mobilellm_143m_q4_k_m",
        "name": "MobileLLM-143M",
        "local_path": r"F:\models\desafiantes_100m_200m\MobileLLM-143M-Q4_K_M.gguf",
        "size_mb": 101.6,
        "params": "143M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "Meta MobileLLM Native Architecture",
    },
    {
        "id": "sheared_pythia_160m_platypus_q4_k_m",
        "name": "Sheared-Pythia-160m-Platypus",
        "local_path": r"F:\models\desafiantes_100m_200m\Sheared-Pythia-160m-Platypus.Q4_K_M.gguf",
        "size_mb": 104.7,
        "params": "160M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "Platypus STEM Alignment (Pythia 160M)",
    },
    {
        "id": "cerebras_gpt_111m_instruction_q4_k_m",
        "name": "Cerebras-GPT-111M-instruction",
        "local_path": r"F:\models\desafiantes_100m_200m\Cerebras-GPT-111M-instruction.Q4_K_M.gguf",
        "size_mb": 81.3,
        "params": "111M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "Cerebras CS-2 Compute Instruction",
    },
    {
        "id": "distil_deepseek_v4_minute_01b_q4_k_m",
        "name": "Distil-Deepseek.V4.Pro.Minute.Codex-0.1B",
        "local_path": r"F:\models\desafiantes_100m_200m\Distil-Deepseek.V4.Pro.Minute.Codex.NSFW-0.1B.Q4_K_M.gguf",
        "size_mb": 59.9,
        "params": "100M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "DeepSeek V4 Pro Minute Codex",
    },
    {
        "id": "distil_gpt55_minute_01b_q4_k_m",
        "name": "Distil-GPT5.5-Minute.Codex-0.1B",
        "local_path": r"F:\models\desafiantes_100m_200m\Distil-GPT5.5-Minute.Codex.NSFW-0.1B.Q4_K_M.gguf",
        "size_mb": 59.9,
        "params": "100M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "OpenAI GPT-5.5 Minute Codex",
    },
    {
        "id": "lite_mistral_150m_v2_q4_k_l",
        "name": "Lite-Mistral-150M-v2-Instruct",
        "local_path": r"F:\models\desafiantes_100m_200m\Lite-Mistral-150M-v2-Instruct-Q4_K_L.gguf",
        "size_mb": 112.7,
        "params": "150M",
        "tier": "100M-200M",
        "quant": "Q4_K_L",
        "teacher": "Mistral AI Architecture v2",
    }
]

def log(msg: str):
    ts = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{ts} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def stop_server_on_port(proc=None):
    if proc:
        try:
            proc.terminate()
            proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"(Get-NetTCPConnection -LocalPort {PORT} -ErrorAction SilentlyContinue).OwningProcess"],
            capture_output=True, text=True, timeout=5
        )
        for line in res.stdout.strip().split():
            pid = line.strip()
            if pid and pid.isdigit():
                subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
    except Exception:
        pass
    time.sleep(0.5)

def start_server(model_path: Path) -> tuple[subprocess.Popen, float]:
    stop_server_on_port()
    cmd = [
        SERVER_BIN,
        "-m", str(model_path),
        "-c", "3072",
        "-b", "512",
        "-ub", "512",
        "-t", "14",
        "--port", str(PORT),
        "--host", "127.0.0.1"
    ]
    log(f"-> Subindo llama-server Turbo (14 threads Xeon AVX2): {model_path.name}...")
    server_out = open(SERVER_LOG_FILE, "w", encoding="utf-8")
    t0 = time.time()
    proc = subprocess.Popen(cmd, stdout=server_out, stderr=subprocess.STDOUT, text=True, errors="replace", creationflags=0x00004000)

    for _ in range(40):
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

    stop_server_on_port(proc)
    raise RuntimeError(f"Timeout esperando llama-server responder na porta {PORT}")

def measure_speed(boot_s: float) -> Dict[str, float]:
    log("  [*] Medindo throughput bare-metal (PP e TG)...")
    payload = json.dumps({
        "prompt": "Explique brevemente o principio da conservacao de energia em fisica classica.",
        "n_predict": 48,
        "temperature": 0.0
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=15.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    elapsed = max(0.001, time.time() - t0)
    tok_pred = data.get("tokens_predicted", 48)
    tg_s = round(tok_pred / elapsed, 2)

    long_p = "Analise detalhadamente o comportamento de um sistema dinâmico linear invariante no tempo sujeito a realimentação de estados. " * 6
    p_len = len(long_p.split()) * 2
    payload_pp = json.dumps({
        "prompt": long_p,
        "n_predict": 1,
        "temperature": 0.0
    }).encode("utf-8")
    req_pp = urllib.request.Request(f"{BASE_URL}/completion", data=payload_pp, headers={"Content-Type": "application/json"})
    t0_pp = time.time()
    with urllib.request.urlopen(req_pp, timeout=15.0) as resp:
        json.loads(resp.read().decode("utf-8"))
    el_pp = max(0.001, time.time() - t0_pp)
    pp_s = round(p_len / el_pp, 2)

    log(f"   [+] Velocidades: Boot: {boot_s}s | Prompt Processing: {pp_s} tok/s | Text Generation: {tg_s} tok/s")
    return {
        "boot_seconds": boot_s,
        "prompt_per_second": pp_s,
        "predicted_per_second": tg_s
    }

def extract_text_after_think(text: str) -> str:
    if "</think>" in text:
        return text.split("</think>")[-1].strip()
    return text.strip()

def clean_python_code(text: str) -> str:
    t = extract_text_after_think(text)
    if "```python" in t:
        code = t.split("```python")[1].split("```")[0].strip()
        return code
    elif "```" in t:
        code = t.split("```")[1].split("```")[0].strip()
        return code
    return t.strip()

STOP_TOKENS = ["<|im_end|>", "<|endoftext|>", "</s>", "Human:", "User:", "Question:"]

def query_model(prompt: str, is_code: bool = False, max_tokens: int = 160) -> str:
    clean = prompt.replace("/no_think", "").strip()
    eff_prompt = f"{clean}\nResponda APENAS com a funcao Python pura, sem comentarios, sem markdown." if is_code else clean

    # 1. Chat completions (preferido para modelos instruídos)
    payload = json.dumps({
        "messages": [{"role": "user", "content": eff_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens,
        "stop": STOP_TOKENS
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if content:
                return content
    except Exception:
        pass

    # 2. Raw completions fallback
    payload2 = json.dumps({
        "prompt": eff_prompt,
        "n_predict": max_tokens,
        "temperature": 0.0,
        "stop": STOP_TOKENS
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=8.0) as r2:
            d2 = json.loads(r2.read().decode("utf-8"))
            return d2.get("content", "").strip()
    except Exception as e:
        return f"[ERROR: {e}]"

def run_13_areas() -> Dict[str, Any]:
    log("  [*] Executando Bateria 13 Áreas Cognitivas (39 testes)...")
    passed_count = 0
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

            out = query_model(p, is_code=is_code, max_tokens=220 if is_code else 140)
            val_input = clean_python_code(out) if is_code else extract_text_after_think(out)
            ok = False
            try:
                ok = bool(validator(val_input))
            except Exception:
                try:
                    ok = bool(validator(out))
                except Exception:
                    ok = False

            if ok:
                a_pass += 1
                passed_count += 1

        if a_pass == len(area["tests"]):
            perfect_count += 1
        areas[a_id] = {
            "name": a_name,
            "baseline_passed": a_pass,
            "passed": a_pass,
            "total": len(area["tests"])
        }
        log(f"    -> Área {a_id} ({a_name[:25]}): {a_pass}/3")

    pct = round((passed_count / 39) * 100, 2)
    log(f"  [+] Pontuação Final 13 Áreas: {passed_count}/39 ({pct}%) | Gabaritadas 3/3: {perfect_count}")
    return {
        "baseline_passed": passed_count,
        "baseline_pct": pct,
        "passed": passed_count,
        "total": 39,
        "pct": pct,
        "perfect_areas_count": perfect_count,
        "areas": areas
    }

def run_opus_10() -> Dict[str, Any]:
    log("  [*] Executando Bateria 10 Desafios Opus (Verificação Formal AST & pytest)...")
    passed_count = 0
    details = {}

    for test in OPUS_10_TESTS:
        t_id = test["id"]
        p = test["prompt"]
        assertions = test.get("assertions", [])

        out = query_model(p, is_code=True, max_tokens=256)
        code = clean_python_code(out)
        ok = False
        try:
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=4.0)
            ok = ver.passed
        except Exception:
            ok = False

        if ok:
            passed_count += 1
            details[t_id] = "PASS"
        else:
            details[t_id] = "FAIL"

    pct = round((passed_count / 10) * 100, 2)
    log(f"  [+] Pontuação Final Opus: {passed_count}/10 ({pct}%)")
    return {
        "baseline_passed": passed_count,
        "baseline_pct": pct,
        "passed": passed_count,
        "total": 10,
        "pct": pct,
        "details": details
    }

def main():
    log("=" * 80)
    log("AETHERMIND — TORNEIO MUNDIAL DOS DESAFIANTES DE 100M A 200M — TIER-1 TEACHERS")
    log("=" * 80)

    results = {}
    if PROOF_FILE.exists():
        try:
            with open(PROOF_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = {}

    for idx, c in enumerate(CONTENDERS, 1):
        c_id = c["id"]
        c_name = c["name"]
        m_path = Path(c["local_path"])

        if c_id in results and results[c_id].get("areas_13", {}).get("total", 0) == 39 and results[c_id].get("opus_10", {}).get("total", 0) == 10:
            log(f"[*] [{idx}/{len(CONTENDERS)}] {c_name} JÁ AVALIADO ({results[c_id]['areas_13']['passed']}/39 | Opus: {results[c_id]['opus_10']['passed']}/10). Pulando...")
            continue

        if not m_path.exists():
            log(f"[-] [{idx}/{len(CONTENDERS)}] {c_name} NÃO ENCONTRADO em {m_path}. Pulando...")
            continue

        log("\n" + "#" * 80)
        log(f"[*] [{idx}/{len(CONTENDERS)}] PROCESSANDO DESAFIANTE 100M-200M: {c_name} ({c['size_mb']} MB)")
        log(f"    Parâmetros: {c['params']} | Professor: {c['teacher']} | Quantização: {c['quant']}")
        log("#" * 80)

        proc = None
        try:
            proc, boot_s = start_server(m_path)
            speeds = measure_speed(boot_s)

            areas_res = run_13_areas()
            opus_res = run_opus_10()

            results[c_id] = {
                "name": c_name,
                "local_path": str(m_path),
                "params": c["params"],
                "tier": c["tier"],
                "quant": c["quant"],
                "teacher": c["teacher"],
                "size_mb": c["size_mb"],
                "speeds": speeds,
                "areas_13": areas_res,
                "opus_10": opus_res,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(PROOF_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            log(f"[+] Prova gravada com sucesso em {PROOF_FILE.name}!")

        except Exception as e:
            log(f"[!] ERRO ao processar {c_name}: {e}")
        finally:
            stop_server_on_port(proc)
            time.sleep(1)

    log("\n" + "=" * 80)
    log("[+] TORNEIO MUNDIAL DE 100M A 200M CONCLUÍDO COM SUCESSO ABSOLUTO!")
    log("=" * 80)

if __name__ == "__main__":
    main()
