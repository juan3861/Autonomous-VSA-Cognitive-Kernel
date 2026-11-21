# -*- coding: utf-8 -*-
"""
AETHERMIND — GRANDE DUELO DOS DESAFIANTES 600M (SUB-800M) TIER-1
Comandante Primário: Mestre Ruan

Objetivo:
Submeter a teste bare-metal rigoroso (14 threads Xeon AVX2, prioridade BelowNormal)
os modelos mais promissores da faixa 600M destilados com outros professores Tier-1
(DeepSeek-R1, DeepSeek-V3 671B, Claude 4.6 Opus, OpenAI o1, GRPO RL e TinyQwen R1),
para verificar se algum consegue superar o Campeão Atual:
Qwen3-0.6B-Distilled-30B-Thinking-SFT-Q4_K_M (32/39 = 82.05%, 9 gabaritos, 43.3 tok/s).
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

SERVER_BIN = r"F:\tools\lc_b10749\llama-server.exe"
PORT = 8089
BASE_URL = f"http://127.0.0.1:{PORT}"

PROOF_FILE = Path(r"F:\data\proof_duelo_desafiantes_600m.json")
LOG_FILE = Path(r"F:\data\tournament_600m_desafiantes.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_600m_desafiantes.log")

CONTENDERS = [
    # -------------------------------------------------------------
    # 1. DESAFIANTE: DeepSeek-R1 Coder Draft 0.6B
    # -------------------------------------------------------------
    {
        "id": "deepseek_r1_0528_coder_draft_06b",
        "name": "DeepSeek-R1-0528-CODER-DRAFT-0.6B",
        "role": "DESAFIANTE (DeepSeek-R1 Coder)",
        "teacher": "DeepSeek-R1 (Tier-1 Reasoning/Code)",
        "repo": "mradermacher/DeepSeek-R1-0528-CODER-DRAFT-0.6B-v1.1-GGUF",
        "path": Path(r"F:\models\desafiantes_600m\deepseek_r1_0528_coder_draft_06b__Q4_K_M.gguf"),
        "quant": "Q4_K_M",
        "params": "600M"
    },
    # -------------------------------------------------------------
    # 2. DESAFIANTE: DeepSeek-V3 0324 Coder Draft 0.6B
    # -------------------------------------------------------------
    {
        "id": "deepseek_v3_0324_coder_draft_06b",
        "name": "DeepSeek-V3-0324-CODER-DRAFT-0.6B",
        "role": "DESAFIANTE (DeepSeek-V3 671B MoE)",
        "teacher": "DeepSeek-V3 (671B MoE Architecture)",
        "repo": "mradermacher/DeepSeek-V3-0324-CODER-DRAFT-0.6B-v1.0-GGUF",
        "path": Path(r"F:\models\desafiantes_600m\deepseek_v3_0324_coder_draft_06b__Q4_K_M.gguf"),
        "quant": "Q4_K_M",
        "params": "600M"
    },
    # -------------------------------------------------------------
    # 3. DESAFIANTE: G1-0.6B (OpenAI o1 Reasoning Distill)
    # -------------------------------------------------------------
    {
        "id": "g1_06b_o1_reasoning",
        "name": "G1-0.6B-O1-Reasoning",
        "role": "DESAFIANTE (OpenAI o1 Reasoning)",
        "teacher": "OpenAI o1-preview dynamic reasoning",
        "repo": "mradermacher/G1-0.6B-GGUF",
        "path": Path(r"F:\models\desafiantes_600m\g1_06b_o1_reasoning__Q4_K_M.gguf"),
        "quant": "Q4_K_M",
        "params": "600M"
    },
    # -------------------------------------------------------------
    # 4. DESAFIANTE: Qwen3-0.6B Opus 4.6 Abliterated
    # -------------------------------------------------------------
    {
        "id": "qwen3_06b_opus46_abliterated",
        "name": "Qwen3-0.6B-Opus4.6-Abliterated",
        "role": "DESAFIANTE (Claude 4.6 Opus)",
        "teacher": "Claude 4.6 Opus (Zero Refusal / Pure Reasoning)",
        "repo": "szili2011/Qwen3-0.6B-Opus4.6-Abliterated-GGUF",
        "path": Path(r"F:\models\desafiantes_600m\qwen3_06b_opus46_abliterated__Q4_K_M.gguf"),
        "quant": "Q4_K_M",
        "params": "600M"
    },
    # -------------------------------------------------------------
    # 5. DESAFIANTE: GRPO-Qwen3-0.6B Reinforcement Learning
    # -------------------------------------------------------------
    {
        "id": "grpo_qwen3_06b_rl",
        "name": "GRPO-Qwen3-0.6B-RL",
        "role": "DESAFIANTE (GRPO DeepSeek RL)",
        "teacher": "DeepSeek GRPO (Group Relative Policy Optimization)",
        "repo": "mradermacher/GRPO-Qwen3-0.6B-GGUF",
        "path": Path(r"F:\models\desafiantes_600m\grpo_qwen3_06b_rl__Q4_K_M.gguf"),
        "quant": "Q4_K_M",
        "params": "600M"
    },
    # -------------------------------------------------------------
    # 6. DESAFIANTE: TinyQwen3-Distill-0.6B (DeepSeek-R1 Distill)
    # -------------------------------------------------------------
    {
        "id": "tinyqwen3_distill_06b_r1",
        "name": "TinyQwen3-Distill-0.6B",
        "role": "DESAFIANTE (DeepSeek-R1 TinyQwen)",
        "teacher": "DeepSeek-R1 Distillation",
        "repo": "mradermacher/TinyQwen3-distill-0.6B-GGUF",
        "path": Path(r"F:\models\desafiantes_600m\tinyqwen3_distill_06b_r1__Q4_K_M.gguf"),
        "quant": "Q4_K_M",
        "params": "600M"
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

def start_llama_server(model_path: Path) -> subprocess.Popen:
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

def query_model(prompt: str, is_code: bool = False, max_tokens: int = 512, retry: bool = False) -> str:
    clean = prompt.replace("/no_think", "").strip()
    if retry:
        eff_prompt = f"ATENCAO: Seja estritamente conciso e preciso. {clean}\nResponda APENAS com a solucao exata, sem explicacoes adicionais."
    else:
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

def run_13_areas() -> Dict[str, Any]:
    log("  [*] Executando Bateria 13 Áreas Cognitivas (39 testes: Baseline + Refinamento Direto)...")
    base_passed = 0
    refined_passed = 0
    areas = {}
    perfect_count = 0

    for i, area in enumerate(BENCHMARK_SUITE, 1):
        a_id = area.get("area_id", str(i))
        a_name = area.get("area_name", f"Area_{i}")
        a_base_pass = 0
        a_refined_pass = 0
        for test in area["tests"]:
            p = test["prompt"]
            validator = test.get("verify") or test.get("validator")
            is_code = (test.get("schema_type") == "python_func" or "Escreva em Python" in p or "função `" in p)

            # Pass 1: Baseline
            out = query_model(p, is_code=is_code, max_tokens=512 if is_code else 384, retry=False)
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
                a_refined_pass += 1
                refined_passed += 1
            else:
                # Pass 2: Retry refinado
                out_r = query_model(p, is_code=is_code, max_tokens=512 if is_code else 384, retry=True)
                val_r = clean_python_code(out_r) if is_code else extract_text_after_think(out_r)
                ok_r = False
                try:
                    ok_r = bool(validator(val_r))
                except Exception:
                    try:
                        ok_r = bool(validator(out_r))
                    except Exception:
                        ok_r = False
                if ok_r:
                    a_refined_pass += 1
                    refined_passed += 1

        if a_refined_pass == len(area["tests"]):
            perfect_count += 1
        areas[a_id] = {
            "name": a_name,
            "baseline_passed": a_base_pass,
            "passed": a_refined_pass,
            "total": len(area["tests"])
        }
        log(f"    -> Área {a_id} ({a_name[:25]}): Baseline {a_base_pass}/{len(area['tests'])} | Refinado {a_refined_pass}/{len(area['tests'])}")

    base_pct = round((base_passed / 39) * 100, 2)
    ref_pct = round((refined_passed / 39) * 100, 2)
    log(f"  [+] Pontuação Final 13 Áreas: Baseline {base_passed}/39 ({base_pct}%) ➔ Refinado {refined_passed}/39 ({ref_pct}%) | Gabaritadas 3/3: {perfect_count}")
    return {
        "baseline_passed": base_passed,
        "baseline_pct": base_pct,
        "passed": refined_passed,
        "total": 39,
        "pct": ref_pct,
        "perfect_areas_count": perfect_count,
        "areas": areas
    }

def run_opus() -> Dict[str, Any]:
    log("  [*] Executando Bateria 10 Desafios Opus (Verificação Formal AST & pytest)...")
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
            raw = query_model(prompt, is_code=True, max_tokens=640, retry=False)
            code = clean_python_code(raw)
            ver = formal_verifier.verify_python_code(code, assertions, timeout_s=8.0)
            if ver.passed:
                passed = True
                base_passed += 1
                opus_passed += 1
                res_str = "PASS (Baseline)"
            else:
                # 1 retry rápido com instrução reforçada
                retry_p = f"{prompt}\nATENCAO: A implementacao anterior falhou. Escreva estritamente a funcao Python correta com tratamento total de edge cases."
                raw_r = query_model(retry_p, is_code=True, max_tokens=640, retry=True)
                code_r = clean_python_code(raw_r)
                ver_r = formal_verifier.verify_python_code(code_r, assertions, timeout_s=8.0)
                if ver_r.passed:
                    passed = True
                    opus_passed += 1
                    res_str = "PASS (Retry)"
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
    log("AETHERMIND — TORNEIO DOS DESAFIANTES 600M (SUB-800M) TIER-1")
    log("=" * 80)

    results = {}
    if PROOF_FILE.exists():
        try:
            with open(PROOF_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
            log(f"[*] Prova anterior carregada com {len(results)} modelos já auditados.")
        except Exception:
            results = {}

    # Preenche o Campeão Atual com seus dados históricos oficiais homologados
    if "qwen3_06b_distill_30b_thinking_q4_k_m" not in results:
        results["qwen3_06b_distill_30b_thinking_q4_k_m"] = {
            "name": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
            "role": "CAMPEÃO ATUAL (Defesa de Cinturão)",
            "teacher": "Qwen3-30B-A3B-Thinking SFT",
            "repo": "reaperdoesntknow/Qwen3-0.6B-Distilled-30B-A3B-Thinking-SFT-GGUF",
            "quant": "Q4_K_M",
            "size_mb": 420.25,
            "boot_seconds": 2.09,
            "pp_tok_s": 291.6,
            "tg_tok_s": 43.3,
            "score_13_areas": 32,
            "baseline_13_areas": 29,
            "pct_13_areas": 82.05,
            "perfect_areas_count": 9,
            "score_opus": 0,
            "baseline_opus": 0,
            "pct_opus": 0.0,
            "completed": True,
            "status": "DEFENDING_CHAMPION"
        }
        with open(PROOF_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    for idx, c in enumerate(CONTENDERS, 1):
        c_id = c["id"]
        c_name = c["name"]
        model_path = c["path"]

        log("\n" + "#" * 80)
        log(f"[{idx}/{len(CONTENDERS)}] TESTANDO: {c_name} ({c['role']})")
        log(f"   Modelo: {c_name} | Professor: {c['teacher']} | Quant: {c['quant']}")
        log(f"   Arquivo Local: {model_path} ({model_path.stat().st_size / (1024**2):.2f} MB)")
        log("#" * 80)

        if not model_path.exists():
            log(f"[!] Arquivo não encontrado: {model_path}. Pulando...")
            continue

        if c_id in results and results[c_id].get("completed", False):
            log(f"[+] {c_name} já concluído anteriormente com {results[c_id]['score_13_areas']}/39. Pulando re-teste.")
            continue

        proc = None
        try:
            proc, boot_s = start_llama_server(model_path)
            speed_info = benchmark_speed(boot_s)

            res_13 = run_13_areas()
            res_opus = run_opus()

            results[c_id] = {
                "name": c_name,
                "role": c["role"],
                "teacher": c["teacher"],
                "repo": c["repo"],
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
    log("CLASSIFICAÇÃO FINAL DO TORNEIO DE DESAFIANTES 600M:")
    log("=" * 80)
    sorted_res = sorted(results.values(), key=lambda x: (x.get("score_13_areas", 0), x.get("score_opus", 0), x.get("tg_tok_s", 0)), reverse=True)
    for pos, r in enumerate(sorted_res, 1):
        log(f"{pos}º: {r['name']:40} | 13 Áreas: {r.get('score_13_areas', 0)}/39 ({r.get('pct_13_areas', 0)}%) | Gabaritos: {r.get('perfect_areas_count', 0)}/13 | Opus: {r.get('score_opus', 0)}/10 | TG: {r.get('tg_tok_s', 0)} tok/s")

if __name__ == "__main__":
    main()
