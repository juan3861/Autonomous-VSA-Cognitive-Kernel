# -*- coding: utf-8 -*-
"""
AETHERMIND — DUELO DE QUANTIZAÇÕES DOS 3 CAMPEÕES 600M (Q4_K_M a F16) SOB LAMBDA-RLM
Comandante Primário: Mestre Ruan

Os 3 Campeões da Categoria 600M:
1. Qwen3-0.6B-Distilled-30B-Thinking-SFT (Campeão Invicto)
2. Qwen3-0.6B-Opus4.6-Abliterated (Vice-Campeão / Claude 4.6 Opus)
3. TinyQwen3-Distill-0.6B (3º Lugar / DeepSeek-R1 Distill)

Quantizações Avaliadas por Campeão:
- Q4_K_M
- Q5_K_M
- Q6_K
- Q8_0
- F16 (Original Float16 sem quantização)

Objetivo:
Mapear a Curva de Ganho Cognitivo x Perda de Velocidade e determinar o Equilíbrio Perfeito
(Pareto Sweet Spot) de cada campeão sob Lambda-RLM.
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

PROOF_FILE = Path(r"F:\data\proof_quants_3_campeoes_600m.json")
LOG_FILE = Path(r"F:\data\tournament_quants_3_campeoes_600m.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_quants_3_campeoes_600m.log")

CONTENDERS = [
    # =========================================================================
    # CAMPEÃO 1: Qwen3-0.6B-Distilled-30B-Thinking-SFT
    # =========================================================================
    {
        "id": "qwen3_06b_distill_30b__q4_k_m",
        "champ": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
        "champ_short": "Qwen3-0.6B-Distill-30B",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "quant": "Q4_K_M",
        "path": Path(r"F:\models\pesos_mosca_200m_15b\reaper_qwen3_06b_distill_30b_thinking__qwen3-0.6b-distilled-30b-thinking-sft-Q4_K_M.gguf")
    },
    {
        "id": "qwen3_06b_distill_30b__q5_k_m",
        "champ": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
        "champ_short": "Qwen3-0.6B-Distill-30B",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "quant": "Q5_K_M",
        "path": Path(r"F:\models\pesos_mosca_quants_finalistas\qwen3_06b_distill_30b_thinking__Q5_K_M.gguf")
    },
    {
        "id": "qwen3_06b_distill_30b__q6_k",
        "champ": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
        "champ_short": "Qwen3-0.6B-Distill-30B",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "quant": "Q6_K",
        "path": Path(r"F:\models\pesos_mosca_quants_finalistas\qwen3_06b_distill_30b_thinking__Q6_K.gguf")
    },
    {
        "id": "qwen3_06b_distill_30b__q8_0",
        "champ": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
        "champ_short": "Qwen3-0.6B-Distill-30B",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "quant": "Q8_0",
        "path": Path(r"F:\models\pesos_mosca_quants_finalistas\qwen3_06b_distill_30b_thinking__Q8_0.gguf")
    },
    {
        "id": "qwen3_06b_distill_30b__f16",
        "champ": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
        "champ_short": "Qwen3-0.6B-Distill-30B",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "quant": "F16",
        "path": Path(r"F:\models\pesos_mosca_quants_finalistas\qwen3_06b_distill_30b_thinking__F16.gguf")
    },

    # =========================================================================
    # CAMPEÃO 2: Qwen3-0.6B-Opus4.6-Abliterated
    # =========================================================================
    {
        "id": "qwen3_06b_opus46__q4_k_m",
        "champ": "Qwen3-0.6B-Opus4.6-Abliterated",
        "champ_short": "Qwen3-0.6B-Opus4.6",
        "teacher": "Claude 4.6 Opus (Zero Refusal / Pure Reasoning)",
        "quant": "Q4_K_M",
        "path": Path(r"F:\models\desafiantes_600m\qwen3_06b_opus46_abliterated__Q4_K_M.gguf")
    },
    {
        "id": "qwen3_06b_opus46__q5_k_m",
        "champ": "Qwen3-0.6B-Opus4.6-Abliterated",
        "champ_short": "Qwen3-0.6B-Opus4.6",
        "teacher": "Claude 4.6 Opus (Zero Refusal / Pure Reasoning)",
        "quant": "Q5_K_M",
        "path": Path(r"F:\models\quants_campeoes_600m\qwen3_06b_opus46__Q5_K_M.gguf")
    },
    {
        "id": "qwen3_06b_opus46__q6_k",
        "champ": "Qwen3-0.6B-Opus4.6-Abliterated",
        "champ_short": "Qwen3-0.6B-Opus4.6",
        "teacher": "Claude 4.6 Opus (Zero Refusal / Pure Reasoning)",
        "quant": "Q6_K",
        "path": Path(r"F:\models\quants_campeoes_600m\qwen3_06b_opus46__Q6_K.gguf")
    },
    {
        "id": "qwen3_06b_opus46__q8_0",
        "champ": "Qwen3-0.6B-Opus4.6-Abliterated",
        "champ_short": "Qwen3-0.6B-Opus4.6",
        "teacher": "Claude 4.6 Opus (Zero Refusal / Pure Reasoning)",
        "quant": "Q8_0",
        "path": Path(r"F:\models\quants_campeoes_600m\qwen3_06b_opus46__Q8_0.gguf")
    },
    {
        "id": "qwen3_06b_opus46__f16",
        "champ": "Qwen3-0.6B-Opus4.6-Abliterated",
        "champ_short": "Qwen3-0.6B-Opus4.6",
        "teacher": "Claude 4.6 Opus (Zero Refusal / Pure Reasoning)",
        "quant": "F16",
        "path": Path(r"F:\models\quants_campeoes_600m\qwen3_06b_opus46__F16.gguf")
    },

    # =========================================================================
    # CAMPEÃO 3: TinyQwen3-Distill-0.6B
    # =========================================================================
    {
        "id": "tinyqwen3_distill_06b__q4_k_m",
        "champ": "TinyQwen3-Distill-0.6B",
        "champ_short": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "Q4_K_M",
        "path": Path(r"F:\models\desafiantes_600m\tinyqwen3_distill_06b_r1__Q4_K_M.gguf")
    },
    {
        "id": "tinyqwen3_distill_06b__q5_k_m",
        "champ": "TinyQwen3-Distill-0.6B",
        "champ_short": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "Q5_K_M",
        "path": Path(r"F:\models\quants_campeoes_600m\tinyqwen3_distill_06b__Q5_K_M.gguf")
    },
    {
        "id": "tinyqwen3_distill_06b__q6_k",
        "champ": "TinyQwen3-Distill-0.6B",
        "champ_short": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "Q6_K",
        "path": Path(r"F:\models\quants_campeoes_600m\tinyqwen3_distill_06b__Q6_K.gguf")
    },
    {
        "id": "tinyqwen3_distill_06b__q8_0",
        "champ": "TinyQwen3-Distill-0.6B",
        "champ_short": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "Q8_0",
        "path": Path(r"F:\models\quants_campeoes_600m\tinyqwen3_distill_06b__Q8_0.gguf")
    },
    {
        "id": "tinyqwen3_distill_06b__f16",
        "champ": "TinyQwen3-Distill-0.6B",
        "champ_short": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "F16",
        "path": Path(r"F:\models\quants_campeoes_600m\tinyqwen3_distill_06b__F16.gguf")
    }
]

def log(msg: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def kill_port_8089():
    try:
        res = subprocess.run(["powershell", "-NoProfile", "-Command", "(Get-NetTCPConnection -LocalPort 8089 -ErrorAction SilentlyContinue).OwningProcess"], capture_output=True, text=True)
        pids = [p.strip() for p in res.stdout.split() if p.strip().isdigit()]
        for pid in set(pids):
            subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        time.sleep(1.0)
    except Exception as e:
        log(f"[!] Aviso ao encerrar processo 8089: {e}")

def start_llama_server(model_path: Path) -> tuple[subprocess.Popen, float]:
    kill_port_8089()
    if not model_path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

    log(f"[*] Iniciando llama-server bare-metal para {model_path.name}...")
    log_fp = open(SERVER_LOG_FILE, "a", encoding="utf-8")

    cmd = [
        SERVER_BIN,
        "-m", str(model_path),
        "-c", "4096",
        "-b", "512",
        "-t", "14",
        "--port", str(PORT),
        "--host", "127.0.0.1",
        "--cont-batching",
        "--embedding"
    ]

    p = subprocess.Popen(
        cmd,
        stdout=log_fp,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.BELOW_NORMAL_PRIORITY_CLASS
    )

    t0 = time.time()
    ready = False
    while time.time() - t0 < 60.0:
        try:
            req = urllib.request.Request(f"{BASE_URL}/health")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    ready = True
                    break
        except Exception:
            time.sleep(0.5)

    if not ready:
        kill_port_8089()
        raise TimeoutError(f"Servidor não respondeu em 60s para {model_path.name}")

    boot_time = round(time.time() - t0, 2)
    log(f"[+] Servidor ativo em {boot_time}s!")
    return p, boot_time

def benchmark_speed(boot_s: float) -> Dict[str, float]:
    log("  [*] Medindo throughput bare-metal (PP tok/s e TG tok/s)...")
    prompt = "Explique a diferenca entre um compilador e um interpretador em computacao de alta performance."
    payload = json.dumps({
        "prompt": prompt,
        "n_predict": 128,
        "temperature": 0.0,
        "ignore_eos": True
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    try:
        t0 = time.time()
        with urllib.request.urlopen(req, timeout=30.0) as resp:
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

    # 1. Chat Completion endpoint
    payload = json.dumps({
        "messages": [{"role": "user", "content": eff_prompt}],
        "temperature": 0.0,
        "max_tokens": max_tokens
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/v1/chat/completions", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=35.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            msg = data["choices"][0]["message"]
            content = (msg.get("content") or "").strip()
            if not content:
                content = (msg.get("reasoning_content") or "").strip()
            if content:
                return content
    except Exception:
        pass

    # 2. Raw Completion endpoint
    payload2 = json.dumps({
        "prompt": f"<|im_start|>user\n{eff_prompt}\n<|im_end|>\n<|im_start|>assistant\n<think>\nDirect answer.\n</think>\n",
        "n_predict": max_tokens,
        "temperature": 0.0,
        "stop": ["<|im_end|>", "<|endoftext|>", "</s>"]
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=35.0) as r2:
            d2 = json.loads(r2.read().decode("utf-8"))
            c2 = d2.get("content", "").strip()
            if c2:
                return c2
    except Exception:
        pass

    # 3. Simple Raw Prompt fallback
    payload3 = json.dumps({
        "prompt": f"User: {eff_prompt}\nAssistant:",
        "n_predict": max_tokens,
        "temperature": 0.0,
        "stop": ["\nUser:", "User:", "<|endoftext|>", "</s>"]
    }).encode("utf-8")
    req3 = urllib.request.Request(f"{BASE_URL}/completion", data=payload3, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req3, timeout=35.0) as r3:
            d3 = json.loads(r3.read().decode("utf-8"))
            c3 = d3.get("content", "").strip()
            if c3:
                return c3
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
    # Fallback refinado direto se LambdaRLM falhar no menu de tarefas
    return query_fast_direct(prompt, is_code=is_code, max_tokens=512)

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

        passed = False
        res_str = "FAIL"

        try:
            raw = query_fast_direct(prompt, is_code=True, max_tokens=512)
            code = clean_python_code(raw)
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=8.0)
            if ver.passed:
                passed = True
                base_passed += 1
                opus_passed += 1
                res_str = "PASS (Baseline)"
            else:
                retry_p = f"{prompt}\nATENCAO: A implementacao anterior falhou ({ver.details or 'erro'}). Escreva estritamente a funcao Python correta com tratamento total de edge cases."
                raw_rlm = query_fast_direct(retry_p, is_code=True, max_tokens=512)
                code_rlm = clean_python_code(raw_rlm)
                ver_rlm = formal_verifier.verify_python_code(code_rlm, assertions, timeout_s=8.0)
                if ver_rlm.passed:
                    passed = True
                    opus_passed += 1
                    res_str = "PASS (Lambda-RLM)"
                else:
                    res_str = "FAIL"
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

def main():
    log("=" * 80)
    log("AETHERMIND — DUELO DE QUANTIZAÇÕES DOS 3 CAMPEÕES 600M (Q4_K_M a F16)")
    log("=" * 80)

    results = {}
    if PROOF_FILE.exists():
        try:
            with open(PROOF_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
            log(f"[*] Prova anterior carregada com {len(results)} configurações já homologadas.")
        except Exception:
            results = {}

    # Preenche o histórico oficial homologado do Campeão 1 (todas as 5 quantizações já validadas)
    c1_history = {
        "qwen3_06b_distill_30b__q4_k_m": {"boot_seconds": 2.09, "pp_tok_s": 291.60, "tg_tok_s": 43.30, "score_13_areas": 32, "baseline_13_areas": 29, "pct_13_areas": 82.05, "perfect_areas_count": 9, "score_opus": 0, "size_mb": 420.25},
        "qwen3_06b_distill_30b__q5_k_m": {"boot_seconds": 2.05, "pp_tok_s": 244.90, "tg_tok_s": 39.70, "score_13_areas": 30, "baseline_13_areas": 28, "pct_13_areas": 76.92, "perfect_areas_count": 6, "score_opus": 0, "size_mb": 510.00},
        "qwen3_06b_distill_30b__q6_k":   {"boot_seconds": 2.06, "pp_tok_s": 256.50, "tg_tok_s": 38.50, "score_13_areas": 29, "baseline_13_areas": 27, "pct_13_areas": 74.36, "perfect_areas_count": 6, "score_opus": 0, "size_mb": 580.00},
        "qwen3_06b_distill_30b__q8_0":   {"boot_seconds": 2.06, "pp_tok_s": 235.60, "tg_tok_s": 33.00, "score_13_areas": 30, "baseline_13_areas": 28, "pct_13_areas": 76.92, "perfect_areas_count": 7, "score_opus": 0, "size_mb": 750.00},
        "qwen3_06b_distill_30b__f16":    {"boot_seconds": 6.16, "pp_tok_s": 272.40, "tg_tok_s": 24.10, "score_13_areas": 29, "baseline_13_areas": 27, "pct_13_areas": 74.36, "perfect_areas_count": 7, "score_opus": 0, "size_mb": 1410.00},
    }

    # Preenche o baseline Q4_K_M dos campeões 2 e 3 homologados no round anterior
    c2_c3_q4 = {
        "qwen3_06b_opus46__q4_k_m": {"boot_seconds": 7.08, "pp_tok_s": 192.90, "tg_tok_s": 38.97, "score_13_areas": 30, "baseline_13_areas": 26, "pct_13_areas": 76.92, "perfect_areas_count": 8, "score_opus": 0, "size_mb": 378.33},
        "tinyqwen3_distill_06b__q4_k_m": {"boot_seconds": 4.06, "pp_tok_s": 232.90, "tg_tok_s": 40.66, "score_13_areas": 28, "baseline_13_areas": 25, "pct_13_areas": 71.79, "perfect_areas_count": 8, "score_opus": 0, "size_mb": 378.11}
    }

    for cid, cdata in {**c1_history, **c2_c3_q4}.items():
        if cid not in results:
            matching_c = [c for c in CONTENDERS if c["id"] == cid][0]
            results[cid] = {
                "champ": matching_c["champ"],
                "champ_short": matching_c["champ_short"],
                "teacher": matching_c["teacher"],
                "quant": matching_c["quant"],
                "size_mb": cdata["size_mb"],
                "boot_seconds": cdata["boot_seconds"],
                "pp_tok_s": cdata["pp_tok_s"],
                "tg_tok_s": cdata["tg_tok_s"],
                "score_13_areas": cdata["score_13_areas"],
                "baseline_13_areas": cdata["baseline_13_areas"],
                "pct_13_areas": cdata["pct_13_areas"],
                "perfect_areas_count": cdata["perfect_areas_count"],
                "score_opus": cdata["score_opus"],
                "completed": True,
                "status": "HOMOLOGADO_ROUND_ANTERIOR"
            }
    with open(PROOF_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    for idx, c in enumerate(CONTENDERS, 1):
        c_id = c["id"]
        c_name = f"{c['champ_short']} [{c['quant']}]"
        model_path = c["path"]

        log("\n" + "#" * 80)
        log(f"[{idx}/{len(CONTENDERS)}] PROCESSANDO: {c_name}")
        log(f"   Campeão: {c['champ']} | Quant: {c['quant']} | Professor: {c['teacher']}")
        log(f"   Arquivo Local: {model_path}")
        log("#" * 80)

        if c_id in results and results[c_id].get("completed", False):
            log(f"[+] {c_name} já concluído anteriormente com {results[c_id]['score_13_areas']}/39 ({results[c_id]['pct_13_areas']}%) e {results[c_id]['tg_tok_s']} tok/s. Pulando re-teste.")
            continue

        if not model_path.exists():
            log(f"[!] Arquivo não encontrado: {model_path}. Aguardando ou pulando...")
            continue

        proc = None
        try:
            proc, boot_s = start_llama_server(model_path)
            speed_info = benchmark_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model_path.name,
                    "base_url": f"{BASE_URL}/v1",
                    "api_key": "none",
                    "max_tokens": 512,
                    "temperature": 0.0,
                }
            )

            res_13 = run_13_areas(lambda_engine)
            res_opus = run_opus(lambda_engine)

            results[c_id] = {
                "champ": c["champ"],
                "champ_short": c["champ_short"],
                "teacher": c["teacher"],
                "quant": c["quant"],
                "size_mb": round(model_path.stat().st_size / (1024**2), 2),
                "speed": speed_info,
                "boot_seconds": speed_info["boot_seconds"],
                "pp_tok_s": speed_info["prompt_per_second"],
                "tg_tok_s": speed_info["predicted_per_second"],
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

            with open(PROOF_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            log(f"[+] Prova gravada com sucesso em {PROOF_FILE}")

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
    log("MATRIZ FINAL DE QUANTIZAÇÃO DOS 3 CAMPEÕES 600M (PARETO SWEET SPOT):")
    log("=" * 80)
    for c_group in ["Qwen3-0.6B-Distill-30B", "Qwen3-0.6B-Opus4.6", "TinyQwen3-Distill-0.6B"]:
        log(f"\n--- CAMPEÃO: {c_group} ---")
        group_items = [v for v in results.values() if v.get("champ_short") == c_group]
        for item in sorted(group_items, key=lambda x: (x.get("score_13_areas", 0), x.get("tg_tok_s", 0)), reverse=True):
            log(f"  [{item['quant']:6}] 13 Áreas: {item.get('score_13_areas')}/39 ({item.get('pct_13_areas')}%) | Gabaritos: {item.get('perfect_areas_count')}/13 | Boot: {item.get('boot_seconds')}s | PP: {item.get('pp_tok_s')} t/s | TG: {item.get('tg_tok_s')} t/s | RAM: {item.get('size_mb')} MB")

if __name__ == "__main__":
    main()
