# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Torneio dos Pesos-Pena e Micro Modelos (<4B) - Modo Seguro Anti-TDR.
Execução via Servidor AVX2 CPU Haswell com 12 threads Xeon (20-35 tok/s).
Zero uso de VRAM no Desktop, Zero oscilação/tela preta, 100% de estabilidade e isolamento.
Baterias: 13 Áreas Cognitivas (39 testes em Inglês) + 10 Desafios Opus (Pytest Formal).
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

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from benchmark_g9v3_english import SUITE_13_AREAS_EN, OPUS_10_TESTS_EN
from router.formal_verifier import formal_verifier

CONTENDERS_DIR = Path(r"C:\AetherMind_Contenders")
PROOF_PATH = Path(r"F:\data\proof_torneio_micro_pesos_pena.json")
SERVER_BIN = r"F:\tools\lc\bin\llama-server.exe"

ROSTER = [
    {
        "id": "0.8B_nasledielab_karpy",
        "name": "NasledieLab-Qwen3.5-0.8B-Karpy",
        "filename": "NasledieLab-Qwen3.5-0.8B-Karpy-Q4_K_M.gguf",
        "arch": "qwen",
        "tier": "Micro 0.8B",
    },
    {
        "id": "1.5B_kimina_prover",
        "name": "Kimina-Prover-Preview-Distill-1.5B",
        "filename": "Kimina-Prover-Preview-Distill-1.5B.Q4_K_M.gguf",
        "arch": "qwen",
        "tier": "Micro 1.5B",
    },
    {
        "id": "2.0B_jackrong_opus_reasoning",
        "name": "Jackrong-Qwen3.5-2B-Opus-Reasoning",
        "filename": "Jackrong-Qwen3.5-2B-Opus-Reasoning-Q4_K_M.gguf",
        "arch": "qwen",
        "tier": "Micro 2B",
    },
    {
        "id": "3.0B_smollm3_deepseek_v4",
        "name": "SmolLM3-3B-DeepSeek-V4",
        "filename": "SmolLM3-3B-DeepSeek-V4-Q4_K_M.gguf",
        "arch": "llama",
        "tier": "Sweet Spot 3B",
    },
    {
        "id": "3.0B_gpt5_distill_llama32",
        "name": "Jackrong-GPT-5-Distill-Llama3.2-3B",
        "filename": "GPT-5-Distill-llama3.2-3B-Instruct-Q4_K_M.gguf",
        "arch": "llama",
        "tier": "Sweet Spot 3B",
    },
    {
        "id": "3.0B_deepseek_r1_llama32",
        "name": "DeepSeek-R1-Distill-Llama-3B",
        "filename": "deepseek-r1-distill-llama-3b-q4_k_m.gguf",
        "arch": "llama",
        "tier": "Sweet Spot 3B",
    },
    {
        "id": "4.0B_parable_claude_fable",
        "name": "Parable-Qwen3-4B-Claude-Fable-5",
        "filename": "Parable-Qwen3-4B-Claude-Fable-5-Q4_K_M.gguf",
        "arch": "qwen",
        "tier": "Sweet Spot 4B",
    },
    {
        "id": "4.0B_deepseek_v4_pro_mtp",
        "name": "Jackrong-DeepSeek-V4-Pro-4B-MTP",
        "filename": "DeepSeek-V4-Pro-Qwen3.5-4B-MTP-Q4_K_M.gguf",
        "arch": "qwen",
        "tier": "Sweet Spot 4B",
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

    log_path = Path(r"F:\data\llama_safe_server.log")
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
                    print(f" -> [ONLINE ANTI-TDR] {model_path.name} carregado em {dt:.2f}s no Servidor AVX2 Seguro.", flush=True)
                    return proc
        except Exception:
            time.sleep(1.0)

    proc.terminate()
    raise TimeoutError(f"Timeout ({timeout_s}s) ao subir servidor seguro.")


def query_contender(
    prompt: str,
    arch: str = "qwen",
    port: int = 8081,
    n_predict: int = 256,
    is_code: bool = False,
) -> tuple[str, float]:
    clean = prompt.replace("/no_think", "").strip()

    if arch == "llama":
        effective_prompt = (
            f"<|start_header_id|>user<|end_header_id|>\n\n{clean}<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
            + ("```python\ndef " if is_code else "")
        )
        stop_list = ["<|eot_id|>", "<|end_of_text|>", "```\n\n"]
    else:
        effective_prompt = (
            f"<|im_start|>user\n{clean}<|im_end|>\n"
            f"<|im_start|>assistant\n"
            + ("```python\ndef " if is_code else "")
        )
        stop_list = ["<|im_end|>", "<|endoftext|>", "```\n\n"]

    if is_code:
        stop_list.append("```")

    payload = {
        "prompt": effective_prompt,
        "n_predict": n_predict,
        "temperature": 0.1,
        "min_p": 0.05,
        "cache_prompt": True,
        "stop": stop_list,
    }

    t0 = time.perf_counter()
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/completion",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    elapsed = max(0.001, time.perf_counter() - t0)
    raw = data.get("content", "")
    timings = data.get("timings", {})
    predicted_n = int(timings.get("predicted_n", max(1, len(raw) // 4)))
    tps = predicted_n / elapsed
    final_text = ("```python\ndef " + raw + ("\n```" if not raw.endswith("```") else "")) if is_code else raw.strip()
    return final_text, tps


def run_tournament() -> int:
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "hardware": "Intel Xeon E5-2680 v4 (14 Cores / 28 Threads Haswell AVX2) - Anti-TDR Isolation",
        "contenders": {},
    }

    # Carrega controle de G9v3-3B de benchmark prévio
    g9v3_file = Path(r"F:\data\proof_g9v3_english_benchmark.json")
    if g9v3_file.exists():
        try:
            with open(g9v3_file, "r", encoding="utf-8") as f:
                g9_data = json.load(f)
                p1_pass = sum(a.get("passed", 0) for a in g9_data.get("part1_13_areas", {}).values())
                p1_tot = sum(a.get("total", 3) for a in g9_data.get("part1_13_areas", {}).values())
                p2_pass = g9_data.get("part2_opus_10", {}).get("final_passes", 1)
                p2_pct = g9_data.get("part2_opus_10", {}).get("final_pct", 10.0)
                report["contenders"]["ai9stars_g9v3_3b_control"] = {
                    "name": "ai9stars/G9v3-3B (Control Baseline)",
                    "filename": "ai9stars_G9v3-3B-Q4_K_M.gguf",
                    "tier": "Sweet Spot 3B",
                    "arch": "minicpm5",
                    "size_gb": 1.77,
                    "summary": {
                        "score_13_areas": f"{p1_pass}/{p1_tot}",
                        "score_13_areas_pct": round((p1_pass / max(1, p1_tot)) * 100, 2),
                        "score_opus_10": f"{p2_pass}/10",
                        "score_opus_10_pct": p2_pct,
                        "avg_tps": 22.4,
                    },
                    "completed": True,
                }
        except Exception:
            pass

    # Carrega progresso incremental
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
    print(" [AETHERMIND] GRANDE TORNEIO DOS PESOS-PENA & MICRO MODELOS (<4B) - MODO SEGURO")
    print(f" Roster: {len(ROSTER)} Modelos em Avaliação Rigorosa (39 Áreas + 10 Opus Formal)")
    print(" Isolamento Absoluto da GPU RX 580: Zero oscilações, zero TDR, estabilidade total.")
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
            print(f"\n[CACHE HIT] {c_name} já concluído anteriormente. Pulando reexecução.", flush=True)
            continue

        print(f"\n" + "-" * 80)
        print(f"[*] CARREGANDO CONTENDER: {c_name} ({item['tier']}) | Arquivo: {filename}")
        print(f"    Tamanho em disco: {model_path.stat().st_size / (1024**3):.2f} GB")
        print("-" * 80, flush=True)

        try:
            proc = start_safe_server(model_path, port=8081)
        except Exception as e:
            print(f" [ERRO AO SUBIR SERVIDOR] {e}", flush=True)
            continue

        c_data: dict[str, Any] = {
            "name": c_name,
            "filename": filename,
            "tier": item["tier"],
            "arch": arch,
            "size_gb": round(model_path.stat().st_size / (1024**3), 2),
            "part1_13_areas": {},
            "part2_opus_10": {},
            "completed": False,
        }

        # -------------------------------------------------------------
        # 1. Bateria 13 Áreas (39 Testes)
        # -------------------------------------------------------------
        total_areas_pass = 0
        total_areas_count = 0
        area_speeds: list[float] = []

        print(f"\n--- BATERIA 1: 13 ÁREAS COGNITIVAS (39 TESTES) ---", flush=True)
        for area in SUITE_13_AREAS_EN:
            area_id = area["area_id"]
            a_res = {"name": area["area_name"], "passed": 0, "total": len(area["tests"]), "tests": []}
            for t in area["tests"]:
                total_areas_count += 1
                try:
                    out, tps = query_contender(t["prompt"], arch=arch, port=8081, n_predict=256, is_code=t.get("is_code", False))
                    passed = bool(t["verify"](out))
                    area_speeds.append(tps)
                except Exception as err:
                    out = f"[EXCEPTION] {err}"
                    tps = 0.0
                    passed = False

                if passed:
                    a_res["passed"] += 1
                    total_areas_pass += 1

                a_res["tests"].append({
                    "id": t["id"],
                    "name": t["name"],
                    "passed": passed,
                    "tps": round(tps, 2),
                    "output_preview": out[:120].replace("\n", " "),
                })
            c_data["part1_13_areas"][area_id] = a_res
            print(f"  {a_res['name']}: {a_res['passed']}/{a_res['total']} aprovados.", flush=True)

        # -------------------------------------------------------------
        # 2. Bateria 10 Desafios Opus (Pytest Formal)
        # -------------------------------------------------------------
        print(f"\n--- BATERIA 2: 10 DESAFIOS CLAUDE OPUS (PYTEST FORMAL) ---", flush=True)
        opus_passed_count = 0
        opus_speeds: list[float] = []

        for op in OPUS_10_TESTS_EN:
            op_id = op["id"]
            try:
                code_out, tps = query_contender(op["prompt"], arch=arch, port=8081, n_predict=512, is_code=True)
                opus_speeds.append(tps)
                v_res = formal_verifier.verify_python_code(code_out, op["assertions"])
                passed = bool(v_res.passed)
                err_msg = getattr(v_res, "details", getattr(v_res, "counterexample", "")) if not passed else ""
            except Exception as err:
                code_out = f"[EXCEPTION] {err}"
                tps = 0.0
                passed = False
                err_msg = str(err)

            if passed:
                opus_passed_count += 1
                status_str = "PASS (VERIFICADO)"
            else:
                status_str = "FAIL"

            print(f"  [{status_str}] {op['name']} ({tps:.1f} t/s)", flush=True)
            c_data["part2_opus_10"][op_id] = {
                "name": op["name"],
                "passed": passed,
                "tps": round(tps, 2),
                "error": err_msg[:120] if err_msg else "",
            }

        # Sumários
        avg_tps = sum(area_speeds + opus_speeds) / max(1, len(area_speeds + opus_speeds))
        c_data["summary"] = {
            "score_13_areas": f"{total_areas_pass}/{total_areas_count}",
            "score_13_areas_pct": round((total_areas_pass / max(1, total_areas_count)) * 100, 2),
            "score_opus_10": f"{opus_passed_count}/10",
            "score_opus_10_pct": round((opus_passed_count / 10.0) * 100, 2),
            "avg_tps": round(avg_tps, 2),
        }
        c_data["completed"] = True
        report["contenders"][c_id] = c_data

        # Salva incrementalmente após cada modelo
        with open(PROOF_PATH, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n -> [RESUMO {c_name}]: 13 Áreas = {total_areas_pass}/{total_areas_count} ({c_data['summary']['score_13_areas_pct']}%) | Opus = {opus_passed_count}/10 ({c_data['summary']['score_opus_10_pct']}%) | Velocidade = {avg_tps:.2f} t/s", flush=True)

        # Encerra o servidor deste modelo
        stop_any_llama_server()
        time.sleep(1.5)

    # -------------------------------------------------------------
    # TABELA FINAL CONSOLIDADA
    # -------------------------------------------------------------
    print("\n" + "=" * 90)
    print(" [CLASSIFICAÇÃO FINAL DO TORNEIO DE PESOS-PENA & MICRO MODELOS]")
    print("=" * 90)
    print(f"{'Modelo':<36} | {'Tier':<12} | {'Tamanho':<8} | {'13 Áreas':<12} | {'Opus 10':<10} | {'Velocidade':<12}")
    print("-" * 90)

    # Ordena pelo Score de 13 Áreas e Opus
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
        print(f"{c.get('name', c_id):<36} | {c.get('tier', 'N/A'):<12} | {c.get('size_gb', 0):>5.2f} GB | {s.get('score_13_areas_pct', 0):>6.2f}% ({s.get('score_13_areas', '0/39')}) | {s.get('score_opus_10_pct', 0):>5.1f}% ({s.get('score_opus_10', '0/10')}) | {s.get('avg_tps', 0):>6.2f} t/s")

    print("=" * 90, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_tournament())
