# -*- coding: utf-8 -*-
"""
AETHERMIND — DUELO OPUS HARD (10 DESAFIOS) COM MODO PENSANTE ATIVO + LAMBDA-RLM
PARA OS CAMPEÕES 600M A PARTIR DE 32 ACERTOS (>= 32/39)
Comandante Primário: Mestre Ruan

Campeões Qualificados (>= 32/39 nas 13 Áreas Cognitivas):
1. TinyQwen3-Distill-0.6B [Q5_K_M] — 34/39 (87.18%) | DeepSeek-R1 Distill
2. TinyQwen3-Distill-0.6B [Q6_K]   — 33/39 (84.62%) | DeepSeek-R1 Distill
3. Qwen3-0.6B-Distill-30B [Q4_K_M] — 32/39 (82.05%) | Qwen3-30B Thinking SFT
4. Qwen3-0.6B-Opus4.6 [Q8_0]       — 32/39 (82.05%) | Claude 4.6 Opus Pure Reasoning

Arquitetura de Execução:
- Modo Pensante Estritamente Ativo (/think + bloco <think>...</think> aberto).
- Síntese de 2 Estágios Anti-Truncamento: se a cadeia <think> atingir o limite de tokens de raciocínio
  sem fechar </think>, o motor preserva o raciocínio gerado, fecha </think> e solicita a emissão imediata
  do código Python final fundamentado no pensamento recém-construído.
- Pass 1: Modo Pensante Ativo Zero-Shot.
- Pass 2: Decomposição Lambda-RLM + Reparo Guiado por Contraexemplo Formal (AST/pytest) em Modo Pensante Ativo.
"""

import os
import sys
import time
import json
import re
import urllib.request
import subprocess
from pathlib import Path
from typing import Dict, Any, Tuple

sys.stdout.reconfigure(encoding='utf-8')

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

PROOF_FILE = Path(r"F:\data\proof_opus_thinking_lambda_campeoes_32plus.json")
MAIN_QUANTS_PROOF = Path(r"F:\data\proof_quants_3_campeoes_600m.json")
LOG_FILE = Path(r"F:\data\tournament_opus_thinking_lambda_32plus.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_opus_thinking_32plus.log")

ELITE_32PLUS_CHAMPIONS = [
    {
        "id": "tinyqwen3_distill_06b__q5_k_m",
        "name": "TinyQwen3-Distill-0.6B [Q5_K_M]",
        "champ": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "Q5_K_M",
        "score_13_areas": 34,
        "pct_13_areas": 87.18,
        "path": Path(r"F:\models\quants_campeoes_600m\tinyqwen3_distill_06b__Q5_K_M.gguf")
    },
    {
        "id": "tinyqwen3_distill_06b__q6_k",
        "name": "TinyQwen3-Distill-0.6B [Q6_K]",
        "champ": "TinyQwen3-Distill-0.6B",
        "teacher": "DeepSeek-R1 Distillation",
        "quant": "Q6_K",
        "score_13_areas": 33,
        "pct_13_areas": 84.62,
        "path": Path(r"F:\models\quants_campeoes_600m\tinyqwen3_distill_06b__Q6_K.gguf")
    },
    {
        "id": "qwen3_06b_distill_30b__q4_k_m",
        "name": "Qwen3-0.6B-Distill-30B [Q4_K_M]",
        "champ": "Qwen3-0.6B-Distilled-30B-Thinking-SFT",
        "teacher": "Qwen3-30B-A3B-Thinking SFT",
        "quant": "Q4_K_M",
        "score_13_areas": 32,
        "pct_13_areas": 82.05,
        "path": Path(r"F:\models\pesos_mosca_200m_15b\reaper_qwen3_06b_distill_30b_thinking__qwen3-0.6b-distilled-30b-thinking-sft-Q4_K_M.gguf")
    },
    {
        "id": "qwen3_06b_opus46__q8_0",
        "name": "Qwen3-0.6B-Opus4.6 [Q8_0]",
        "champ": "Qwen3-0.6B-Opus4.6-Abliterated",
        "teacher": "Claude 4.6 Opus (Pure Reasoning)",
        "quant": "Q8_0",
        "score_13_areas": 32,
        "pct_13_areas": 82.05,
        "path": Path(r"F:\models\quants_campeoes_600m\qwen3_06b_opus46__Q8_0.gguf")
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

def start_llama_server(model_path: Path) -> Tuple[subprocess.Popen, float]:
    kill_port_8089()
    if not model_path.exists():
        raise FileNotFoundError(f"Modelo não encontrado: {model_path}")

    log(f"[*] Iniciando llama-server bare-metal (ctx=8192, Modo Pensante Ativo) para {model_path.name}...")
    log_fp = open(SERVER_LOG_FILE, "a", encoding="utf-8")

    cmd = [
        SERVER_BIN,
        "-m", str(model_path),
        "-c", "8192",
        "-b", "512",
        "-t", "14",
        "--port", str(PORT),
        "--host", "127.0.0.1",
        "--cont-batching"
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
    matches = re.findall(pattern, cleaned, re.IGNORECASE)
    if matches:
        # Pega o último bloco de código (geralmente a solução final após o raciocínio)
        for m in reversed(matches):
            if "def " in m:
                cleaned = m.strip()
                break
        else:
            cleaned = matches[-1].strip()
    m_code = re.search(r"^(?:import|from|def|class)\s+", cleaned, re.MULTILINE)
    if m_code:
        cleaned = cleaned[m_code.start():]
    return cleaned.strip()

def query_active_thinking(prompt: str, think_budget: int = 1024, code_budget: int = 512) -> Tuple[str, int]:
    """
    Executa inferência com Modo Pensante Estritamente Ativo (<think> aberto).
    Se o modelo atingir think_budget ainda dentro do <think>, fecha </think> e
    continua gerando o código Python final em 2º estágio para evitar truncamento!
    Retorna (codigo_limpo, tokens_pensados).
    """
    clean_p = prompt.replace("/no_think", "").strip()
    thinking_user_prompt = (
        f"/think\n{clean_p}\n"
        f"Pense passo a passo sobre o algoritmo e casos de borda dentro de <think>...</think> e, "
        f"ao final, escreva apenas a funcao Python completa dentro de ```python ... ```."
    )

    raw_prompt = f"<|im_start|>user\n{thinking_user_prompt}\n<|im_end|>\n<|im_start|>assistant\n<think>\n"
    payload = json.dumps({
        "prompt": raw_prompt,
        "n_predict": think_budget,
        "temperature": 0.1,
        "top_p": 0.9,
        "stop": ["<|im_end|>", "<|endoftext|>", "</s>"]
    }).encode("utf-8")

    req = urllib.request.Request(f"{BASE_URL}/completion", data=payload, headers={"Content-Type": "application/json"})
    gen_text = ""
    thought_tokens = 0
    try:
        with urllib.request.urlopen(req, timeout=120.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            gen_text = data.get("content", "")
            thought_tokens = data.get("timings", {}).get("predicted_n", len(gen_text.split()))
    except Exception as e:
        log(f"      [!] Aviso Stage 1 Thinking: {e}")

    # Verifica se o modelo fechou </think> e já entregou `def `
    if "</think>" in gen_text:
        after_think = gen_text.split("</think>", 1)[1].strip()
        if "def " in after_think:
            return clean_python_code(after_think), thought_tokens

    # Estágio 2: O modelo pensou intensamente mas não fechou </think> ou não terminou a função Python.
    # Forçamos o fechamento de </think> preservando todo o pensamento construído e pedimos o código Python!
    thought_trace = gen_text.split("</think>")[0].strip()
    stage2_prompt = (
        f"{raw_prompt}{thought_trace}\n</think>\n"
        f"```python\n"
    )
    payload2 = json.dumps({
        "prompt": stage2_prompt,
        "n_predict": code_budget,
        "temperature": 0.0,
        "stop": ["```", "<|im_end|>", "<|endoftext|>", "</s>"]
    }).encode("utf-8")

    req2 = urllib.request.Request(f"{BASE_URL}/completion", data=payload2, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req2, timeout=90.0) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
            code_out = data2.get("content", "").strip()
            thought_tokens += data2.get("timings", {}).get("predicted_n", 0)
            if code_out:
                return clean_python_code(code_out), thought_tokens
    except Exception as e:
        log(f"      [!] Aviso Stage 2 Code Synthesis: {e}")

    return clean_python_code(gen_text), thought_tokens

def run_opus_thinking_lambda(lambda_engine: LambdaRLM) -> Dict[str, Any]:
    log("  [*] Executando 10 Desafios Opus Hard (Modo Pensante Ativo + Lambda-RLM + Verificador Formal AST/pytest)...")
    base_passed = 0
    rlm_passed = 0
    opus_details = {}

    for test in OPUS_10_TESTS:
        t_id = test["id"]
        t_name = test["name"]
        prompt = test["prompt"]
        assertions = test["assertions"]

        t0 = time.time()
        passed = False
        res_str = "FAIL"
        total_toks = 0

        # ---------------------------------------------------------------------
        # PASS 1: Modo Pensante Ativo (Stage 1 Thought + Stage 2 Code Synthesis)
        # ---------------------------------------------------------------------
        code_p1, toks_p1 = query_active_thinking(prompt, think_budget=1024, code_budget=512)
        total_toks += toks_p1
        ver1 = formal_verifier.verify_python_code(code_p1, assertions, timeout_s=6.0)
        if ver1.passed:
            passed = True
            base_passed += 1
            rlm_passed += 1
            res_str = "PASS (Thinking Zero-Shot)"
        else:
            # -----------------------------------------------------------------
            # PASS 2: Decomposição Lambda-RLM + Reparo Guiado por Contraexemplo em Modo Pensante Ativo
            # -----------------------------------------------------------------
            ce_feedback = ver1.counterexample or ver1.details or "Falha de asserção nos casos de borda."
            rlm_sub_prompt = (
                f"/think Analise o seguinte problema algoritmico e o erro formal da tentativa anterior:\n"
                f"PROBLEMA: {prompt.replace('/no_think', '').strip()}\n"
                f"CODIGO ANTERIOR:\n{code_p1[:600]}\n"
                f"ERRO NO VERIFICADOR FORMAL: {ce_feedback}\n"
                f"Formule a estrategia matematica exata para corrigir o algoritmo."
            )
            rlm_hint = ""
            try:
                rlm_res = lambda_engine.completion(rlm_sub_prompt)
                rlm_hint = extract_text_after_think(rlm_res.response or "")[:600]
            except Exception:
                rlm_hint = ""

            repair_prompt = (
                f"{prompt.replace('/no_think', '').strip()}\n\n"
                f"ATENCAO: A tentativa anterior falhou no teste formal com o erro:\n{ce_feedback}\n"
                f"Diretriz de correcao Lambda-RLM: {rlm_hint}\n"
                f"Corrija o algoritmo Python garantindo que todas as assercoes passem."
            )
            code_p2, toks_p2 = query_active_thinking(repair_prompt, think_budget=1024, code_budget=512)
            total_toks += toks_p2
            ver2 = formal_verifier.verify_python_code(code_p2, assertions, timeout_s=6.0)
            if ver2.passed:
                passed = True
                rlm_passed += 1
                res_str = "PASS (Thinking + Lambda-RLM Repair)"
            else:
                # -------------------------------------------------------------
                # PASS 3: Segunda Iteração de Reparo Estrito com Contraexemplo 2
                # -------------------------------------------------------------
                ce_feedback2 = ver2.counterexample or ver2.details or "Falha de asserção."
                repair_prompt2 = (
                    f"{prompt.replace('/no_think', '').strip()}\n\n"
                    f"ERRO CRITICO NA TENTATIVA 2: {ce_feedback2}\n"
                    f"Reescreva a funcao Python do zero com logica impecavel para todos os casos de borda."
                )
                code_p3, toks_p3 = query_active_thinking(repair_prompt2, think_budget=1024, code_budget=512)
                total_toks += toks_p3
                ver3 = formal_verifier.verify_python_code(code_p3, assertions, timeout_s=6.0)
                if ver3.passed:
                    passed = True
                    rlm_passed += 1
                    res_str = "PASS (Thinking + Lambda-RLM Turn 3)"
                else:
                    res_str = f"FAIL ({(ver3.counterexample or 'AssertionError')[:45]})"

        elapsed_s = round(time.time() - t0, 2)
        opus_details[t_id] = {
            "name": t_name,
            "passed": passed,
            "result": res_str,
            "thought_and_code_tokens": total_toks,
            "elapsed_seconds": elapsed_s
        }
        log(f"    -> {t_id} ({t_name[:32]}): {res_str} [{total_toks} toks | {elapsed_s}s]")

    base_pct = round((base_passed / 10) * 100, 2)
    rlm_pct = round((rlm_passed / 10) * 100, 2)
    log(f"  [+] PLACAR OPUS (MODO PENSANTE + LAMBDA-RLM): Zero-Shot {base_passed}/10 ({base_pct}%) ➔ Final {rlm_passed}/10 ({rlm_pct}%)")
    return {
        "baseline_passed": base_passed,
        "baseline_pct": base_pct,
        "passed": rlm_passed,
        "total": 10,
        "pct": rlm_pct,
        "details": opus_details
    }

def main():
    log("=" * 88)
    log("AETHERMIND — DUELO OPUS HARD (MODO PENSANTE ATIVO + LAMBDA-RLM) — CAMPEÕES >= 32 ACERTOS")
    log("=" * 88)

    results = {}
    if PROOF_FILE.exists():
        try:
            with open(PROOF_FILE, "r", encoding="utf-8") as f:
                results = json.load(f)
        except Exception:
            results = {}

    for idx, c in enumerate(ELITE_32PLUS_CHAMPIONS, 1):
        c_id = c["id"]
        c_name = c["name"]
        model_path = c["path"]

        log("\n" + "#" * 88)
        log(f"[{idx}/{len(ELITE_32PLUS_CHAMPIONS)}] TESTANDO OPUS (MODO PENSANTE + LAMBDA-RLM): {c_name}")
        log(f"   Score 13 Áreas: {c['score_13_areas']}/39 ({c['pct_13_areas']}%) | Professor: {c['teacher']}")
        log("#" * 88)

        if c_id in results and results[c_id].get("completed", False):
            log(f"[+] {c_name} já concluído com {results[c_id]['score_opus_thinking_rlm']}/10. Pulando...")
            continue

        proc = None
        try:
            proc, boot_s = start_llama_server(model_path)
            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model_path.name,
                    "base_url": f"{BASE_URL}/v1",
                    "api_key": "none",
                    "max_tokens": 768,
                    "temperature": 0.1,
                }
            )

            res_opus = run_opus_thinking_lambda(lambda_engine)

            results[c_id] = {
                "id": c_id,
                "name": c_name,
                "champ": c["champ"],
                "teacher": c["teacher"],
                "quant": c["quant"],
                "score_13_areas": c["score_13_areas"],
                "pct_13_areas": c["pct_13_areas"],
                "boot_seconds": boot_s,
                "score_opus_zero_shot_thinking": res_opus["baseline_passed"],
                "score_opus_thinking_rlm": res_opus["passed"],
                "pct_opus_thinking_rlm": res_opus["pct"],
                "details_opus": res_opus,
                "completed": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            with open(PROOF_FILE, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            # Atualiza também o arquivo principal proof_quants_3_campeoes_600m.json
            if MAIN_QUANTS_PROOF.exists():
                with open(MAIN_QUANTS_PROOF, "r", encoding="utf-8") as mf:
                    main_data = json.load(mf)
                if c_id in main_data:
                    main_data[c_id]["score_opus"] = res_opus["passed"]
                    main_data[c_id]["baseline_opus"] = res_opus["baseline_passed"]
                    main_data[c_id]["pct_opus"] = res_opus["pct"]
                    main_data[c_id]["details_opus_thinking_lambda"] = res_opus
                    with open(MAIN_QUANTS_PROOF, "w", encoding="utf-8") as mf:
                        json.dump(main_data, mf, indent=2, ensure_ascii=False)

            log(f"[+] Prova gravada com sucesso para {c_name}!")
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            kill_port_8089()

    log("\n" + "=" * 88)
    log("RESUMO FINAL — 10 DESAFIOS OPUS HARD (MODO PENSANTE ATIVO + LAMBDA-RLM):")
    log("=" * 88)
    for cid, r in results.items():
        log(f"  * {r['name']:34} | 13 Áreas: {r['score_13_areas']}/39 ({r['pct_13_areas']}%) | Opus (Thinking Zero-Shot): {r['score_opus_zero_shot_thinking']}/10 ➔ Opus (Thinking + Lambda-RLM): {r['score_opus_thinking_rlm']}/10 ({r['pct_opus_thinking_rlm']}%)")

if __name__ == "__main__":
    main()
