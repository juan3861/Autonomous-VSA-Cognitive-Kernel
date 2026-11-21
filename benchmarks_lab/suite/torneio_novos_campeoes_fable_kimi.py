# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Torneio AetherMind dos Novos Campeoes Fable, Kimi, DeepHermes & DeepSeek.
Baterias: 13 Areas Cognitivas (39 testes em Ingles) + 10 Desafios Opus (Pytest Formal com Auto-Reparo).
Runtime: Typed Functional Lambda-RLM + Bare-Metal.
Servidor: Intel Xeon AVX2 Haswell (12 threads) com Isolamento Anti-TDR.
Armazenamento: Drive I: (I:\AetherMind_Contenders).
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LAMBDA_RLM_DIR = ROOT / "lambda_rlm"
if str(LAMBDA_RLM_DIR) not in sys.path:
    sys.path.insert(0, str(LAMBDA_RLM_DIR))

from benchmark_g9v3_english import OPUS_10_TESTS_EN, SUITE_13_AREAS_EN
from rlm import LambdaRLM
from router.formal_verifier import formal_verifier

PHYSICAL_DIRS = [
    Path(r"F:\data\models"),
    Path(r"F:\AetherMind_Contenders"),
    Path(r"E:\models"),
    Path(r"E:\models\gguf\cpu_bench"),
    Path(r"D:\AetherMind_Contenders"),
    Path(r"E:\AetherMind_Preserved"),
    Path(r"F:\AetherMind_Preserved"),
    Path(r"D:\AetherMind_Preserved"),
    Path(r"I:\AetherMind_Contenders"),
]
CONTENDERS_DIR = Path(r"F:\AetherMind_Contenders")
PROOF_PATH = Path(r"F:\data\proof_torneio_novos_campeoes_fable_kimi.json")
SERVER_BIN = r"F:\tools\lc\bin\llama-server.exe"
PORT = 8089  # Porta dedicada livre de colisoes e segura

def find_model_path(filename: str) -> Path | None:
    for d in PHYSICAL_DIRS:
        p = d / filename
        try:
            if p.exists():
                return p
        except Exception:
            continue
    return None


ROSTER = [
    {
        "id": "3.0B_gpt5_distill_llama32",
        "name": "GPT-5-Distill-llama3.2-3B-Instruct",
        "filename": "GPT-5-Distill-llama3.2-3B-Instruct-Q4_K_M.gguf",
        "tier": "Sweet Spot 3B",
        "arch": "llama",
    },
    {
        "id": "4.0B_parable_qwen3_fable5",
        "name": "Parable-Qwen3-4B-Claude-Fable-5",
        "filename": "Parable-Qwen3-4B-Claude-Fable-5-Q4_K_M.gguf",
        "tier": "Sweet Spot 4B",
        "arch": "qwen",
    },
    {
        "id": "9.0B_mimo_v26_distill_qwen",
        "name": "MiMo-V2.6-Distill-Qwen-9B",
        "filename": "MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "35.0B_qwen36_moe_a3b",
        "name": "Qwen3.6-35B-A3B-UD-MoE",
        "filename": "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf",
        "tier": "35B MoE (3B Ativos)",
        "arch": "qwen",
    },
    {
        "id": "1.5B_kimina_prover",
        "name": "Kimina-Prover-Preview-Distill-1.5B",
        "filename": "Kimina-Prover-Preview-Distill-1.5B.Q4_K_M.gguf",
        "tier": "1.5B Micro",
        "arch": "qwen",
    },
    {
        "id": "3.0B_deephermes3_llama32",
        "name": "NousResearch-DeepHermes-3-Llama3-3B",
        "filename": "NousResearch_DeepHermes-3-Llama-3-3B-Preview-Q4_K_M.gguf",
        "tier": "Sweet Spot 3B",
        "arch": "llama",
    },
    {
        "id": "3.0B_llama32_fable5_distill",
        "name": "Llama-3.2-3B-Fable-5-Distill",
        "filename": "Llama-3.2-3B-Fable-5-Distill-Q4_K_M.gguf",
        "tier": "Sweet Spot 3B",
        "arch": "llama",
    },
    {
        "id": "4.0B_qwen3_hybrid",
        "name": "unsloth-Qwen3-4B-Hybrid",
        "filename": "Qwen3-4B-Q4_K_M.gguf",
        "tier": "Sweet Spot 4B",
        "arch": "qwen",
    },
    {
        "id": "8.0B_deepseek_r1_0528_qwen3",
        "name": "unsloth-DeepSeek-R1-0528-Qwen3-8B",
        "filename": "DeepSeek-R1-0528-Qwen3-8B-Q4_K_M.gguf",
        "tier": "8B DeepSeek",
        "arch": "qwen",
    },
    {
        "id": "9.0B_deepseek_v4_pro_mtp",
        "name": "Jackrong-DeepSeek-V4-Pro-9B-MTP",
        "filename": "DeepSeek-V4-Pro-Qwen3.5-9B-MTP-Q4_K_M.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "9.0B_qwen35_kimi_k3_distill",
        "name": "mradermacher-Qwen3.5-9B-Kimi-k3-Distill",
        "filename": "Qwen3.5-9B-Kimi-k3-Distilled.Q4_K_M.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "9.0B_qwable_claude_fable5",
        "name": "empero-Qwable-9B-Claude-Fable-5",
        "filename": "Qwable-9B-Claude-Fable-5-Q4_K_M.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "9.0B_the_defiant_fable_max",
        "name": "DavidAU-The-Defiant-Fable-9B-MAX",
        "filename": "Qwen3.5-9B-The-Defiant-Fable-Uncnr-Heretic-NEO-MAX-Q4_K_M.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "9.0B_teichai_fable5_v1",
        "name": "TeichAI-Qwen3.5-9B-Fable-5-v1",
        "filename": "Qwen3.5-9B-Fable-5-Distill.q4_k_m.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "9.0B_fableopus_linear",
        "name": "bingleai-FableOpus-9B-Linear",
        "filename": "FableOpus-9B-Linear-Q4_K_M.gguf",
        "tier": "9B Teto Geral",
        "arch": "qwen",
    },
    {
        "id": "4.0B_dory_beam",
        "name": "ProCreations-Dory-Beam-4B-nGPT-Loop",
        "filename": "dory-beam-4b-q5_k_m.gguf",
        "tier": "4B nGPT Loop",
        "arch": "qwen",
    },
    {
        "id": "12.0B_gemma4_agentic_v2",
        "name": "yuxinlu1-Gemma4-12B-Agentic-Fable5-Composer25",
        "filename": "gemma4-v2-Q4_K_M.gguf",
        "tier": "12B Elite Agentes",
        "arch": "gemma",
    },
    {
        "id": "4.5B_gemma4_e4b_opus",
        "name": "deadbydawn101-Gemma4-E4B-Opus-Reasoning",
        "filename": "gemma4-e4b-opus-Q4_K_M.gguf",
        "tier": "4.5B Ultra-Leve",
        "arch": "gemma",
    },
    {
        "id": "1.0B_ibm_grok4_coder",
        "name": "IBM-Grok4-UltraFast-Coder-1B",
        "filename": "IBM-Grok4-UltraFast-Coder-1B.Q4_K_M.gguf",
        "tier": "1B Micro Coder",
        "arch": "qwen",
    },
    {
        "id": "1.5B_baby_grok3",
        "name": "IntelligentEstate-Baby-Grok3-1.5B",
        "filename": "Baby_Grok3-1.5b-iQ4_K_M.gguf",
        "tier": "1.5B Micro Reasoning",
        "arch": "qwen",
    },
    {
        "id": "4.0B_grok3_gemma3_reasoning",
        "name": "mradermacher-Grok3-Reasoning-Gemma3-4B",
        "filename": "Grok-3-reasoning-gemma3-4B-distilled-HF.Q4_K_M.gguf",
        "tier": "4B Sweet Spot Reasoning",
        "arch": "gemma",
    },
    {
        "id": "3.0B_sentie_fable5_kimi_distill",
        "name": "Sentie-3B-Claude-Fable5-KimiK3-Distill",
        "filename": "Sentie1.0-3B.Q4_K_M.gguf",
        "tier": "Sweet Spot 3B",
        "arch": "qwen",
    },
    {
        "id": "1.5B_codemate_qwen_fable5",
        "name": "micymike-CodeMate-Qwen-1.5B-Claude-Fable-5",
        "filename": "CodeMate-Qwen-1.5B-32K-Distilled-on-Claude-Fable-5.Q4_K_M.gguf",
        "tier": "1.5B Micro Code Fable 5",
        "arch": "qwen",
    },
    {
        "id": "1.5B_deepseek_r1_distill_qwen",
        "name": "unsloth-DeepSeek-R1-Distill-Qwen-1.5B",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "tier": "1.5B Micro Reasoning R1",
        "arch": "qwen",
    },
    {
        "id": "26.0B_gemma4_moe_a4b",
        "name": "TeichAI-Gemma4-26B-A4B-Opus-MoE",
        "filename": "gemma-4-26B-A4B-it-Claude-Opus-Distill.q3_k_m.gguf",
        "tier": "26B MoE (3.8B Ativos)",
        "arch": "gemma",
    },
]


def stop_any_llama_server() -> None:
    subprocess.run(["taskkill.exe", "/F", "/IM", "llama-server.exe", "/IM", "llama-cli.exe"], capture_output=True)
    time.sleep(0.5)


def start_safe_server(model_path: Path, port: int = PORT, timeout_s: float = 120.0) -> subprocess.Popen[str]:
    stop_any_llama_server()

    health_url = f"http://127.0.0.1:{port}/health"
    cmd = [
        SERVER_BIN,
        "-m", str(model_path),
        "-c", "2048",
        "-b", "512",
        "-ub", "128",
        "-t", "12",
        "-fit", "off",
        "--no-mmap",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]

    log_path = Path(r"F:\data\llama_novos_campeoes_server.log")
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, text=True)

    t0 = time.time()
    while time.time() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"Servidor encerrou prematuramente. Codigo: {proc.returncode}")
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    dt = time.time() - t0
                    print(f" -> [ONLINE ANTI-TDR] {model_path.name} pronto na porta {port} ({dt:.2f}s).", flush=True)
                    return proc
        except Exception:
            time.sleep(1.0)

    proc.terminate()
    raise TimeoutError(f"Timeout ({timeout_s}s) ao subir servidor seguro.")


def clean_code(raw: str) -> str:
    text = raw.strip()
    if "```python" in text:
        parts = text.split("```python")
        if len(parts) > 1:
            return parts[1].split("```")[0].strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            return parts[1].split("```")[0].strip()
    return text


def query_lambda_worker(lambda_engine: LambdaRLM, prompt: str, is_code: bool = False) -> tuple[str, float, float]:
    clean = prompt.replace("/no_think", "").strip()
    if is_code:
        effective_prompt = f"{clean}\nWrite concise clean Python code only, no comments, no markdown explanations."
    else:
        effective_prompt = clean

    t0 = time.perf_counter()
    try:
        res = lambda_engine.completion(effective_prompt)
        raw_text = res.response.strip()
    except Exception as e:
        raw_text = f"[ERROR: {e}]"

    elapsed_s = max(0.001, time.perf_counter() - t0)
    elapsed_ms = round(elapsed_s * 1000.0, 2)
    final_output = clean_code(raw_text) if is_code else raw_text
    est_tokens = max(1, len(raw_text) // 4)
    tps = round(est_tokens / elapsed_s, 2)
    return final_output, tps, elapsed_ms


def run_tournament() -> int:
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": "Intel Xeon E5-2680 v4 (14 Cores / 28 Threads Haswell AVX2) - Anti-TDR Safe Tier",
        "framework": "Lambda-RLM (Typed Functional Combinator Runtime)",
        "language": "English (100% Native Evaluation)",
        "contenders": {},
    }

    if PROOF_PATH.exists():
        try:
            with open(PROOF_PATH, "r", encoding="utf-8") as f:
                old = json.load(f)
                if "contenders" in old:
                    for k, v in old["contenders"].items():
                        report["contenders"][k] = v
        except Exception:
            pass

    print("\n" + "=" * 90)
    print(" [AETHERMIND] TORNEIO DOS NOVOS CAMPEOES FABLE, KIMI, DEEPHIERMES & DEEPSEEK")
    print(f" Roster: {len(ROSTER)} Modelos em Avaliacao via Combinadores Funcionais Lambda-RLM")
    print(" Baterias: 13 Areas Cognitivas (39 testes EN) + 10 Desafios Opus com Pytest e Auto-Reparo")
    print("=" * 90, flush=True)

    completed_in_run = 0

    for item in ROSTER:
        c_id = item["id"]
        c_name = item["name"]
        filename = item["filename"]
        arch = item["arch"]
        model_path = find_model_path(filename)

        if model_path is None:
            print(f"\n [AGUARDANDO DOWNLOAD] {c_name} -> {filename} nao encontrado nos discos fisicos.", flush=True)
            continue

        if c_id in report["contenders"] and report["contenders"][c_id].get("completed", False):
            print(f"\n[CACHE HIT] {c_name} ja concluido anteriormente. Pulando.", flush=True)
            continue

        print(f"\n" + "-" * 80)
        print(f"[*] INICIANDO CONTENDER EM LAMBDA-RLM: {c_name} ({item['tier']})")
        print(f"    Arquivo: {filename} ({model_path.stat().st_size / (1024**3):.2f} GB)")
        print("-" * 80, flush=True)

        try:
            proc = start_safe_server(model_path, port=PORT)
        except Exception as e:
            print(f" [ERRO AO SUBIR SERVIDOR] {e}", flush=True)
            continue

        lambda_engine = LambdaRLM(
            backend="openai",
            backend_kwargs={
                "model_name": filename,
                "base_url": f"http://127.0.0.1:{PORT}/v1",
                "api_key": "none",
                "temperature": 0.1,
                "max_tokens": 512,
            },
            context_window_chars=2000,
            verbose=False,
        )

        c_data: dict[str, Any] = {
            "name": c_name,
            "filename": filename,
            "tier": item["tier"],
            "arch": arch,
            "framework": "Lambda-RLM",
            "size_gb": round(model_path.stat().st_size / (1024**3), 2),
            "part1_13_areas": {},
            "part2_opus_10": {},
            "completed": False,
        }

        # 1. Bateria 13 Areas em Ingles via Lambda-RLM
        total_areas_pass = 0
        total_areas_count = 0
        area_speeds: list[float] = []

        print(f"\n--- BATERIA 1: 13 AREAS COGNITIVAS EM INGLES (39 TESTES VIA LAMBDA-RLM) ---", flush=True)
        for area in SUITE_13_AREAS_EN:
            area_id = area["area_id"]
            a_res = {"name": area["area_name"], "passed": 0, "total": len(area["tests"]), "tests": []}
            for t in area["tests"]:
                total_areas_count += 1
                out, tps, lat_ms = query_lambda_worker(lambda_engine, t["prompt"], is_code=t.get("is_code", False))
                try:
                    passed = bool(t["verify"](out))
                except Exception:
                    passed = False

                if passed:
                    a_res["passed"] += 1
                    total_areas_pass += 1
                if tps > 0:
                    area_speeds.append(tps)

                badge = "PASS" if passed else "FAIL"
                print(f"  [{badge:4s}] {t['name']:40s} | {tps:5.2f} t/s | {lat_ms:6.1f}ms", flush=True)
                a_res["tests"].append({
                    "id": t["id"],
                    "name": t["name"],
                    "passed": passed,
                    "tps": round(tps, 2),
                    "latency_ms": lat_ms,
                    "output_preview": out[:120].replace("\n", " "),
                })

            c_data["part1_13_areas"][area_id] = a_res
            print(f" -> Placar {a_res['name']}: {a_res['passed']}/{a_res['total']} aprovados.", flush=True)

        # 2. Bateria 10 Desafios Opus com Pytest Formal e Auto-Reparo
        print(f"\n--- BATERIA 2: 10 DESAFIOS OPUS EM INGLES (PYTEST FORMAL VIA LAMBDA-RLM) ---", flush=True)
        opus_passed_count = 0
        opus_first_passed = 0
        opus_speeds: list[float] = []

        for op in OPUS_10_TESTS_EN:
            op_id = op["id"]
            prompt = op["prompt"]
            first_pass = False
            final_pass = False
            last_code = ""
            last_tps = 0.0
            attempts = 0
            err_msg = ""

            while attempts < 2:
                attempts += 1
                last_code, last_tps, lat_ms = query_lambda_worker(lambda_engine, prompt, is_code=True)
                if last_tps > 0:
                    opus_speeds.append(last_tps)
                v_res = formal_verifier.verify_python_code(last_code, op["assertions"], timeout_s=4.0)
                if v_res.passed:
                    final_pass = True
                    if attempts == 1:
                        first_pass = True
                    break
                else:
                    err_msg = getattr(v_res, "details", getattr(v_res, "counterexample", ""))
                    if attempts < 2:
                        prompt = f"{op['prompt']}\nPrevious attempt failed with error:\n{err_msg}\nPlease fix the logic and output only the corrected Python code."

            if final_pass:
                opus_passed_count += 1
            badge = "PASS" if final_pass else "FAIL"
            attempt_str = f"(1st try)" if first_pass else (f"(2nd try - repaired)" if final_pass else f"(FAILED)")
            print(f"  [{badge:4s}] {op['name']:35s} {attempt_str:22s} | {last_tps:5.2f} t/s", flush=True)

            c_data["part2_opus_10"][op_id] = {
                "name": op["name"],
                "passed": final_pass,
                "first_try_passed": first_pass,
                "attempts": attempts,
                "tps": round(last_tps, 2),
                "error": err_msg if not final_pass else None,
            }

        avg_speed_areas = round(sum(area_speeds) / max(len(area_speeds), 1), 2)
        avg_speed_opus = round(sum(opus_speeds) / max(len(opus_speeds), 1), 2)

        c_data["summary"] = {
            "part1_passed": total_areas_pass,
            "part1_total": total_areas_count,
            "part1_pct": round((total_areas_pass / max(total_areas_count, 1)) * 100.0, 2),
            "opus_passed": opus_passed_count,
            "opus_total": len(OPUS_10_TESTS_EN),
            "opus_pct": round((opus_passed_count / len(OPUS_10_TESTS_EN)) * 100.0, 2),
            "avg_speed_areas_tps": avg_speed_areas,
            "avg_speed_opus_tps": avg_speed_opus,
        }
        c_data["completed"] = True

        report["contenders"][c_id] = c_data
        with open(PROOF_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n [SALVO] Prova de {c_name} gravada com sucesso em {PROOF_PATH}!", flush=True)

        proc.terminate()
        stop_any_llama_server()
        time.sleep(2.0)
        completed_in_run += 1

    print("\n" + "=" * 90)
    print(f" [FIM DA RODADA] {completed_in_run} novos modelos avaliados em Lambda-RLM.")
    print("=" * 90, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_tournament())
