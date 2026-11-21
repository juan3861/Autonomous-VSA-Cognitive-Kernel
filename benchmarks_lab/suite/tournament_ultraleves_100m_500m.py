# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO SUPREMO DOS ULTRALEVES (100M A 500M)
Comandante Primário: Mestre Ruan

Busca pela Máxima Densidade Cognitiva no Menor Tamanho Paramétrico Possível:
- 135M: SmolLM2-135M-Instruct (Q4_K_M, Q8_0, F16)
- 350M-360M: Granite 4.0 Hybrid 350M (Gemini 3 Pro Think Q4_K_M vs BF16 Original), SmolLM2-360M-Instruct
- 500M: Qwen2.5-0.5B-Open-R1-Distill (DeepSeek-R1), QwQ-0.5B-Distilled-SFT (o1 style), Gemini-Distill-Qwen2.5-0.5B, MiniCPM4-0.5B

Baterias Avaliadas:
1. Baseline Zero-Shot Direto (Sem Pensamento)
2. Modo Pensante Ativo (/think) para modelos de raciocínio
3. Reparação Recursiva Lambda-RLM
4. 13 Áreas Cognitivas (39 testes bare-metal)
5. 10 Desafios Opus Hard (Verificação Formal AST & pytest)
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

PROOF_FILE = Path(r"F:\data\proof_torneio_ultraleves_100m_500m.json")
LOG_FILE = Path(r"F:\data\tournament_ultraleves_100m_500m.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_ultraleves.log")

CONTENDERS = [
    {
        "id": "smollm2_135m_q4_k_m",
        "name": "SmolLM2-135M-Instruct-Q4_K_M",
        "local_path": r"F:\models\ultraleves_100m_500m\SmolLM2-135M-Instruct-Q4_K_M.gguf",
        "size_mb": 100.57,
        "params": "135M",
        "tier": "100M-200M",
        "quant": "Q4_K_M",
        "teacher": "SmolLM2 Foundation / HuggingFaceTB",
    },
    {
        "id": "smollm2_135m_q8_0",
        "name": "SmolLM2-135M-Instruct-Q8_0",
        "local_path": r"F:\models\ultraleves_100m_500m\SmolLM2-135M-Instruct-Q8_0.gguf",
        "size_mb": 138.10,
        "params": "135M",
        "tier": "100M-200M",
        "quant": "Q8_0",
        "teacher": "SmolLM2 Foundation / HuggingFaceTB",
    },
    {
        "id": "smollm2_135m_f16",
        "name": "SmolLM2-135M-Instruct-F16",
        "local_path": r"F:\models\ultraleves_100m_500m\SmolLM2-135M-Instruct-f16.gguf",
        "size_mb": 258.34,
        "params": "135M",
        "tier": "100M-200M",
        "quant": "F16",
        "teacher": "SmolLM2 Foundation / HuggingFaceTB",
    },
    {
        "id": "granite_4_0_h_350m_gemini3_pro_think_q4_k_m",
        "name": "granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q4_k_m",
        "local_path": r"F:\models\pesos_mosca_200m_15b\glogwa68_granite4_350m_gemini3_pro__granite-4.0-h-350m-DISTILL-gemini-3-pro-think-q4_k_m.gguf",
        "size_mb": 212.30,
        "params": "350M",
        "tier": "300M-400M",
        "quant": "Q4_K_M",
        "teacher": "Google Gemini 3 Pro Thinking",
    },
    {
        "id": "granite_4_0_h_350m_bf16",
        "name": "granite-4.0-h-350m-BF16",
        "local_path": r"F:\models\ultraleves_100m_500m\granite-4.0-h-350m-BF16.gguf",
        "size_mb": 653.20,
        "params": "350M",
        "tier": "300M-400M",
        "quant": "BF16",
        "teacher": "IBM Granite 4.0 Foundation",
    },
    {
        "id": "smollm2_360m_q4_k_m",
        "name": "SmolLM2-360M-Instruct-Q4_K_M",
        "local_path": r"E:\models\gguf\cpu_bench\SmolLM2-360M-Instruct-Q4_K_M.gguf",
        "size_mb": 258.10,
        "params": "360M",
        "tier": "300M-400M",
        "quant": "Q4_K_M",
        "teacher": "SmolLM2 Foundation / HuggingFaceTB",
    },
    {
        "id": "qwen25_05b_open_r1_distill_q4_k_m",
        "name": "Qwen2.5-0.5B-Open-R1-Distill_Q4_K_M",
        "local_path": r"F:\models\ultraleves_100m_500m\Qwen2.5-0.5B-Open-R1-Distill_Q4_K_M.gguf",
        "size_mb": 379.38,
        "params": "500M",
        "tier": "400M-500M",
        "quant": "Q4_K_M",
        "teacher": "DeepSeek-R1 Distill",
    },
    {
        "id": "qwq_05b_distilled_sft_q4_k_m",
        "name": "QwQ-0.5B-Distilled-SFT.Q4_K_M",
        "local_path": r"F:\models\ultraleves_100m_500m\QwQ-0.5B-Distilled-SFT.Q4_K_M.gguf",
        "size_mb": 379.38,
        "params": "500M",
        "tier": "400M-500M",
        "quant": "Q4_K_M",
        "teacher": "Alibaba QwQ / OpenAI o1 Reasoning",
    },
    {
        "id": "gemini_distill_qwen25_05b_q4_k_m",
        "name": "Gemini-Distill-Qwen2.5-0.5B-ead-Q4_K_M",
        "local_path": r"F:\models\pesos_mosca_200m_15b\geraldine_gemini_qwen25_05b__Gemini-Distill-Qwen2.5-0.5B-ead-Q4_K_M.gguf",
        "size_mb": 379.10,
        "params": "500M",
        "tier": "400M-500M",
        "quant": "Q4_K_M",
        "teacher": "Google Gemini Pro Distill",
    },
    {
        "id": "minicpm4_05b_q4_k_m",
        "name": "MiniCPM4-0.5B-Q4_K_M",
        "local_path": r"E:\models\gguf\cpu_bench\MiniCPM4-0.5B-Q4_K_M.gguf",
        "size_mb": 265.80,
        "params": "500M",
        "tier": "400M-500M",
        "quant": "Q4_K_M",
        "teacher": "OpenBMB MiniCPM4 Base",
    }
]

def log(msg: str):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def stop_any_llama_server():
    try:
        subprocess.run(["taskkill", "/F", "/IM", "llama-server.exe"], capture_output=True, text=True)
        time.sleep(1.0)
    except Exception:
        pass

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
    raise RuntimeError(f"Timeout esperando llama-server responder na porta {PORT}")

def measure_speed(boot_s: float) -> Dict[str, float]:
    log("  [*] Medindo throughput bare-metal (PP e TG)...")
    payload = json.dumps({
        "prompt": "Explique brevemente o principio da conservacao de energia em fisica classica.",
        "n_predict": 64,
        "temperature": 0.0
    }).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=30.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    elapsed = max(0.001, time.time() - t0)
    tok_pred = data.get("tokens_predicted", 64)
    tg_s = round(tok_pred / elapsed, 2)

    # PP
    long_p = "Analise detalhadamente o comportamento de um sistema dinâmico linear invariante no tempo sujeito a realimentação de estados com integrador e observador de Luenberger. " * 8
    p_len = len(long_p.split()) * 2
    payload_pp = json.dumps({
        "prompt": long_p,
        "n_predict": 1,
        "temperature": 0.0
    }).encode("utf-8")
    req_pp = urllib.request.Request(f"{BASE_URL}/completion", data=payload_pp, headers={"Content-Type": "application/json"})
    t0_pp = time.time()
    with urllib.request.urlopen(req_pp, timeout=30.0) as resp:
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
                return content
    except Exception:
        pass

    payload2 = json.dumps({
        "prompt": eff_prompt,
        "n_predict": max_tokens,
        "temperature": 0.0
    }).encode("utf-8")
    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=45.0) as r2:
            d2 = json.loads(r2.read().decode("utf-8"))
            return d2.get("content", "").strip()
    except Exception as e:
        return f"[ERROR: {e}]"

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
    log("AETHERMIND — GRANDE TORNEIO DOS ULTRALEVES (100M A 500M) — TIER-1 TEACHERS")
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
        model_path = Path(contender["local_path"])

        if not model_path.exists():
            log(f"[!] [{idx}/{len(CONTENDERS)}] Arquivo não encontrado: {model_path}. Pulando...")
            continue

        if c_id in proof_data and "areas_13" in proof_data[c_id] and "opus_10" in proof_data[c_id]:
            log(f"[*] [{idx}/{len(CONTENDERS)}] {c_name} já avaliado ({proof_data[c_id]['areas_13']['passed']}/39, Opus: {proof_data[c_id]['opus_10']['passed']}/10). Pulando...")
            continue

        log(f"\n################################################################################")
        log(f"[*] [{idx}/{len(CONTENDERS)}] PROCESSANDO ULTRALEVE: {c_name} ({contender['size_mb']} MB) | Classe: {contender['tier']}")
        log(f"    Parâmetros: {contender['params']} | Professor: {contender['teacher']} | Quantização: {contender['quant']}")
        log(f"################################################################################")

        try:
            proc, boot_s = start_server(model_path)
            speeds = measure_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model_path.name,
                    "base_url": f"{BASE_URL}/v1",
                    "api_key": "none",
                    "timeout": 45.0,
                    "temperature": 0.0,
                    "max_tokens": 512
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
                "local_path": str(model_path),
                "params": contender["params"],
                "tier": contender["tier"],
                "quant": contender["quant"],
                "teacher": contender["teacher"],
                "size_mb": contender["size_mb"],
                "speeds": speeds,
                "areas_13": areas_res,
                "opus_10": opus_res,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(PROOF_FILE, "w", encoding="utf-8") as f:
                json.dump(proof_data, f, indent=2, ensure_ascii=False)
            log(f"[+] Prova gravada com sucesso em {PROOF_FILE.name}!")

        except Exception as e:
            log(f"[!] ERRO ao processar {c_name}: {e}")
            stop_any_llama_server()

    log("\n================================================================================")
    log("[+] TORNEIO DOS ULTRALEVES CONCLUÍDO COM SUCESSO!")
    log("================================================================================")

if __name__ == "__main__":
    main()
