# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Torneio Lambda-RLM dos Campeões Peso-Pena (<4B) em Inglês.
Baterias: 13 Áreas Cognitivas (39 testes em Inglês) + 10 Desafios Opus (Pytest Formal com Auto-Reparo).
Runtime: Typed Functional Lambda-RLM (Combinadores, Poda e Decomposição de Contexto).
Servidor: Intel Xeon AVX2 Haswell (12 threads) com Isolamento Anti-TDR.
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

CONTENDERS_DIR = Path(r"C:\AetherMind_Contenders")
PROOF_PATH = Path(r"F:\data\proof_torneio_lambda_rlm_champions.json")
SERVER_BIN = r"F:\tools\lc\bin\llama-server.exe"
PORT = 8081

ROSTER = [
    {
        "id": "3.0B_gpt5_distill_llama32",
        "name": "Jackrong-GPT-5-Distill-Llama3.2-3B",
        "filename": "GPT-5-Distill-llama3.2-3B-Instruct-Q4_K_M.gguf",
        "tier": "Sweet Spot 3B",
        "arch": "llama",
    },
    {
        "id": "4.0B_parable_claude_fable",
        "name": "Parable-Qwen3-4B-Claude-Fable-5",
        "filename": "Parable-Qwen3-4B-Claude-Fable-5-Q4_K_M.gguf",
        "tier": "Sweet Spot 4B",
        "arch": "qwen",
    },
    {
        "id": "3.0B_deepseek_r1_llama32",
        "name": "DeepSeek-R1-Distill-Llama-3B",
        "filename": "deepseek-r1-distill-llama-3b-q4_k_m.gguf",
        "tier": "Sweet Spot 3B",
        "arch": "llama",
    },
]


def stop_any_llama_server() -> None:
    subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name llama-server, llama-cli -ErrorAction SilentlyContinue | Stop-Process -Force"], capture_output=True)
    time.sleep(1.0)


def start_safe_server(model_path: Path, port: int = 8081, timeout_s: float = 60.0) -> subprocess.Popen[str]:
    stop_any_llama_server()

    health_url = f"http://127.0.0.1:{port}/health"
    cmd = [
        SERVER_BIN,
        "-m", str(model_path),
        "-c", "2048",
        "-b", "512",
        "-ub", "128",
        "-t", "12",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]

    log_path = Path(r"F:\data\llama_lambda_server.log")
    log_file = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT, text=True)

    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"Servidor encerrou prematuramente (código: {proc.poll()}).")
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status == 200:
                    dt = time.perf_counter() - t0
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

    # Carrega baseline de controle de G9v3-3B em Lambda-RLM
    g9v3_file = Path(r"F:\data\proof_g9v3_lambda_rlm_english.json")
    if g9v3_file.exists():
        try:
            with open(g9v3_file, "r", encoding="utf-8") as f:
                g9_data = json.load(f)
                p1_pass = g9_data.get("part1_summary", {}).get("passed", 38)
                p1_tot = g9_data.get("part1_summary", {}).get("total", 39)
                p1_pct = g9_data.get("part1_summary", {}).get("pct", 97.44)
                p2_pass = g9_data.get("part2_opus_10", {}).get("final_passes", 1)
                p2_pct = g9_data.get("part2_opus_10", {}).get("final_pct", 10.0)
                report["contenders"]["ai9stars_g9v3_3b_control"] = {
                    "name": "ai9stars/G9v3-3B (Control Baseline Lambda-RLM)",
                    "filename": "ai9stars_G9v3-3B-Q4_K_M.gguf",
                    "tier": "Sweet Spot 3B",
                    "arch": "minicpm5",
                    "size_gb": 1.77,
                    "summary": {
                        "score_13_areas": f"{p1_pass}/{p1_tot}",
                        "score_13_areas_pct": p1_pct,
                        "score_opus_10": f"{p2_pass}/10",
                        "score_opus_10_pct": p2_pct,
                        "avg_tps": g9_data.get("part1_summary", {}).get("avg_tps", 20.0),
                    },
                    "completed": True,
                }
        except Exception:
            pass

    # Carrega progresso anterior se existir
    if PROOF_PATH.exists():
        try:
            with open(PROOF_PATH, "r", encoding="utf-8") as f:
                saved = json.load(f)
                if isinstance(saved.get("contenders"), dict):
                    for k, v in saved["contenders"].items():
                        report["contenders"][k] = v
        except Exception:
            pass

    print("\n" + "=" * 90)
    print(" [AETHERMIND] GRANDE TORNEIO LAMBDA-RLM DOS CAMPEÕES PESO-PENA (<4B) EM INGLÊS")
    print(f" Roster: {len(ROSTER)} Modelos em Avaliação via Combinadores Funcionais Lambda-RLM")
    print(" Baterias: 13 Áreas Cognitivas (39 testes EN) + 10 Desafios Opus com Pytest e Auto-Reparo")
    print("=" * 90, flush=True)

    for item in ROSTER:
        c_id = item["id"]
        c_name = item["name"]
        filename = item["filename"]
        arch = item["arch"]
        model_path = CONTENDERS_DIR / filename

        if not model_path.exists():
            print(f" [ALERTA] Modelo não encontrado no disco: {model_path}. Pulando.", flush=True)
            continue

        if c_id in report["contenders"] and report["contenders"][c_id].get("completed", False):
            print(f"\n[CACHE HIT] {c_name} já concluído anteriormente em Lambda-RLM. Pulando.", flush=True)
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

        # Instancia Lambda-RLM apontando para o servidor seguro
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

        # ----------------------------------------------------------------------
        # 1. Bateria 13 Áreas em Inglês via Lambda-RLM
        # ----------------------------------------------------------------------
        total_areas_pass = 0
        total_areas_count = 0
        area_speeds: list[float] = []

        print(f"\n--- BATERIA 1: 13 ÁREAS COGNITIVAS EM INGLÊS (39 TESTES VIA LAMBDA-RLM) ---", flush=True)
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

        # ----------------------------------------------------------------------
        # 2. Bateria 10 Desafios Opus com Pytest Formal e Auto-Reparo
        # ----------------------------------------------------------------------
        print(f"\n--- BATERIA 2: 10 DESAFIOS OPUS EM INGLÊS (PYTEST FORMAL VIA LAMBDA-RLM) ---", flush=True)
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
                    err_msg = getattr(v_res, "counterexample", getattr(v_res, "details", ""))
                    if attempts == 1:
                        prompt = (
                            f"{op['prompt']}\n\n"
                            f"Your previous attempt failed the formal verifier with:\n{err_msg}\n"
                            f"Rewrite the function correctly to pass all test cases (concise clean Python code only, no comments)."
                        )

            if final_pass:
                opus_passed_count += 1
            if first_pass:
                opus_first_passed += 1

            status_str = "PASS (1st)" if first_pass else ("PASS (Repaired 2nd)" if final_pass else "FAIL")
            print(f"  [{status_str:18s}] {op['name']:55s} | {last_tps:.1f} t/s", flush=True)

            c_data["part2_opus_10"][op_id] = {
                "name": op["name"],
                "passed": final_pass,
                "first_passed": first_pass,
                "attempts": attempts,
                "tps": round(last_tps, 2),
                "error": err_msg[:120] if not final_pass else "",
            }

        # Sumários
        avg_tps = sum(area_speeds + opus_speeds) / max(1, len(area_speeds + opus_speeds))
        c_data["summary"] = {
            "score_13_areas": f"{total_areas_pass}/{total_areas_count}",
            "score_13_areas_pct": round((total_areas_pass / max(1, total_areas_count)) * 100, 2),
            "score_opus_10": f"{opus_passed_count}/10",
            "score_opus_10_pct": round((opus_passed_count / 10.0) * 100, 2),
            "opus_first_passed": opus_first_passed,
            "avg_tps": round(avg_tps, 2),
        }
        c_data["completed"] = True
        report["contenders"][c_id] = c_data

        # Salva incrementalmente
        with open(PROOF_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n -> [RESUMO LAMBDA-RLM {c_name}]: 13 Áreas = {total_areas_pass}/{total_areas_count} ({c_data['summary']['score_13_areas_pct']}%) | Opus = {opus_passed_count}/10 ({c_data['summary']['score_opus_10_pct']}%) | Velocidade = {avg_tps:.2f} t/s", flush=True)

        # Encerra o servidor deste modelo
        stop_any_llama_server()
        time.sleep(1.5)

    # --------------------------------------------------------------------------
    # TABELA FINAL CONSOLIDADA LAMBDA-RLM
    # --------------------------------------------------------------------------
    print("\n" + "=" * 90)
    print(" [CLASSIFICAÇÃO FINAL DOS CAMPEÕES PESO-PENA VIA LAMBDA-RLM EM INGLÊS]")
    print("=" * 90)
    print(f"{'Modelo':<38} | {'Tier':<12} | {'Tamanho':<8} | {'13 Áreas':<12} | {'Opus 10':<10} | {'Velocidade':<12}")
    print("-" * 90)

    sorted_contenders = sorted(
        report["contenders"].items(),
        key=lambda x: (
            x[1].get("summary", {}).get("score_13_areas_pct", 0),
            x[1].get("summary", {}).get("score_opus_10_pct", 0),
        ),
        reverse=True,
    )

    for c_id, c in sorted_contenders:
        s = c.get("summary", {})
        print(f"{c.get('name', c_id):<38} | {c.get('tier', 'N/A'):<12} | {c.get('size_gb', 0):>5.2f} GB | {s.get('score_13_areas_pct', 0):>6.2f}% ({s.get('score_13_areas', '0/39')}) | {s.get('score_opus_10_pct', 0):>5.1f}% ({s.get('score_opus_10', '0/10')}) | {s.get('avg_tps', 0):>6.2f} t/s")

    print("=" * 90, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_tournament())
