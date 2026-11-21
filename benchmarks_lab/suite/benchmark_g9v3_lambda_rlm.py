# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""
Benchmark Oficial: ai9stars/G9v3-3B (1.77 GB Q4_K_M) operando via Lambda-RLM na RX 580 Vulkan.
1. 13 Áreas Cognitivas x 3 Testes = 39 Testes em Inglês via LambdaRLM
2. 10 Desafios Algorítmicos Nível Claude Opus em Inglês com Pytest Formal via LambdaRLM
3. Comparativo fechado contra Bare-Metal Direto, 8B-RLM e Ornith-1.5-9B
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

if sys.platform == "win32":
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

PROOF_PATH = Path(r"F:\data\proof_g9v3_lambda_rlm_english.json")
PORT = 8081

# Instanciar motor Lambda-RLM
lambda_engine = LambdaRLM(
    backend="openai",
    backend_kwargs={
        "model_name": "ai9stars_G9v3-3B-Q4_K_M.gguf",
        "base_url": f"http://127.0.0.1:{PORT}/v1",
        "api_key": "none",
        "temperature": 0.1,
        "max_tokens": 512,
    },
    context_window_chars=2000,
    verbose=False,
)


def clean_code(raw: str) -> str:
    """Extrai código Python puro de respostas com blocos markdown."""
    text = raw.strip()
    if "```python" in text:
        parts = text.split("```python")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0].strip()
            return code_part
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            code_part = parts[1].split("```")[0].strip()
            return code_part
    return text


def query_lambda_worker(prompt: str, is_code: bool = False) -> tuple[str, float, float]:
    """Consulta via LambdaRLM, medindo latência e tokens por segundo."""
    clean = prompt.replace("/no_think", "").strip()
    if is_code:
        effective_prompt = f"{clean}\nWrite concise clean Python code only, no comments, no markdown explanations."
    else:
        effective_prompt = clean

    t0 = time.perf_counter()
    res = lambda_engine.completion(effective_prompt)
    elapsed_s = max(0.001, time.perf_counter() - t0)
    elapsed_ms = round(elapsed_s * 1000.0, 2)

    raw_text = res.response.strip()
    final_output = clean_code(raw_text) if is_code else raw_text
    est_tokens = max(1, len(raw_text) // 4)
    tps = round(est_tokens / elapsed_s, 2)
    return final_output, tps, elapsed_ms


def run_benchmark():
    print("=" * 88)
    print(" [BENCHMARK OFICIAL LAMBDA-RLM] AI9STARS / G9V3-3B NA RX 580 VULKAN")
    print(" Bateria 1: 13 Áreas Cognitivas x 3 Testes = 39 Testes em Inglês")
    print(" Bateria 2: 10 Desafios Algorítmicos Nível Claude Opus com Pytest Formal")
    print("=" * 88, flush=True)

    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "ai9stars/G9v3-3B",
        "quant": "Q4_K_M (1.77 GB)",
        "framework": "Lambda-RLM (Typed Functional Combinator Runtime)",
        "hardware": "AMD Radeon RX 580 8GB Vulkan Bare-Metal (Port 8081)",
        "part1_13_areas": {},
        "part1_summary": {},
        "part2_opus_10": {},
    }

    # --------------------------------------------------------------------------
    # PARTE 1: 13 ÁREAS COGNITIVAS EM INGLÊS (39 TESTES)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print(" [PARTE 1] EXECUTANDO AS 13 ÁREAS COGNITIVAS EM INGLÊS VIA LAMBDA-RLM...")
    print("=" * 88, flush=True)

    total_areas_pass = 0
    total_areas_tests = 0
    areas_tps_list: list[float] = []
    p1_t0 = time.perf_counter()

    for area in SUITE_13_AREAS_EN:
        area_id = area["area_id"]
        area_name = area["area_name"]
        print(f"\n--- {area_name} ---", flush=True)
        area_passes = 0
        area_tests = []

        for t in area["tests"]:
            total_areas_tests += 1
            out, tps, lat_ms = query_lambda_worker(t["prompt"], is_code=t.get("is_code", False))
            passed = False
            try:
                passed = bool(t["verify"](out))
            except Exception:
                passed = False

            if passed:
                area_passes += 1
                total_areas_pass += 1
            if tps > 0:
                areas_tps_list.append(tps)

            badge = "PASS" if passed else "FAIL"
            print(f"   [{badge:4s}] {t['name']:40s} | Vel: {tps:5.2f} t/s | Tempo: {lat_ms:6.1f}ms", flush=True)

            area_tests.append({
                "id": t["id"],
                "name": t["name"],
                "passed": passed,
                "tps": tps,
                "latency_ms": lat_ms,
                "output": out[:200],
            })

        report["part1_13_areas"][area_id] = {
            "name": area_name,
            "passed": area_passes,
            "total": len(area["tests"]),
            "score_str": f"{area_passes}/{len(area['tests'])}",
            "tests": area_tests,
        }

        # Checkpoint progressivo após cada área
        report["part1_summary"] = {
            "passed": total_areas_pass,
            "total": total_areas_tests,
            "pct": round((total_areas_pass / max(1, total_areas_tests)) * 100.0, 2),
            "avg_tps": round(sum(areas_tps_list) / max(1, len(areas_tps_list)), 2),
            "total_time_s": round(time.perf_counter() - p1_t0, 2),
        }
        PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROOF_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    p1_time = round(time.perf_counter() - p1_t0, 2)
    p1_avg_tps = round(sum(areas_tps_list) / max(1, len(areas_tps_list)), 2)
    print(f"\n -> [PARTE 1 CONCLUÍDA]: {total_areas_pass}/{total_areas_tests} ({report['part1_summary']['pct']}%) | Vel: {p1_avg_tps} t/s | Tempo: {p1_time}s", flush=True)

    # --------------------------------------------------------------------------
    # PARTE 2: 10 DESAFIOS CLAUDE OPUS EM INGLÊS COM PYTEST VIA LAMBDA-RLM
    # --------------------------------------------------------------------------
    print("\n" + "=" * 88)
    print(" [PARTE 2] EXECUTANDO OS 10 DESAFIOS CLAUDE OPUS EM INGLÊS VIA LAMBDA-RLM...")
    print("=" * 88, flush=True)

    opus_zero_shot = 0
    opus_final_passes = 0
    opus_repaired = 0
    opus_tps_list: list[float] = []
    opus_tests_results: list[dict[str, Any]] = []
    p2_t0 = time.perf_counter()

    for test in OPUS_10_TESTS_EN:
        t_test = time.perf_counter()
        attempts = 0
        prompt = test["prompt"]
        first_passed = False
        final_passed = False
        initial_ce = None
        last_code = ""
        last_tps = 0.0

        while attempts < 2:
            attempts += 1
            last_code, last_tps, lat_ms = query_lambda_worker(prompt, is_code=True)
            ver = formal_verifier.verify_python_code(last_code, test["assertions"], timeout_s=4.0)
            if ver.passed:
                final_passed = True
                if attempts == 1:
                    first_passed = True
                break

            if attempts == 1:
                initial_ce = ver.counterexample
                prompt = (
                    f"{test['prompt']}\n\n"
                    f"Your previous attempt failed the formal verifier with:\n{ver.counterexample}\n"
                    f"Rewrite the function correctly to pass all test cases (concise clean Python code only, no comments)."
                )

        elapsed_ms = round((time.perf_counter() - t_test) * 1000.0, 2)
        if first_passed:
            opus_zero_shot += 1
        if final_passed:
            opus_final_passes += 1
        if final_passed and attempts > 1:
            opus_repaired += 1
        if last_tps > 0:
            opus_tps_list.append(last_tps)

        badge = "PASS (1st)" if first_passed else ("PASS (Repaired 2nd)" if final_passed else "FAIL")
        print(f"   [{badge:18s}] {test['name']:58s} | Vel: {last_tps:5.2f} t/s | Tempo: {elapsed_ms:7.1f}ms", flush=True)

        opus_tests_results.append({
            "id": test["id"],
            "name": test["name"],
            "first_passed": first_passed,
            "final_passed": final_passed,
            "attempts": attempts,
            "repaired": (final_passed and attempts > 1),
            "counterexample": initial_ce,
            "tps": round(last_tps, 2),
            "latency_ms": elapsed_ms,
            "code": last_code,
        })

        # Checkpoint progressivo após cada teste Opus
        report["part2_opus_10"] = {
            "zero_shot_passes": opus_zero_shot,
            "final_passes": opus_final_passes,
            "repaired_passes": opus_repaired,
            "final_pct": round((opus_final_passes / len(OPUS_10_TESTS_EN)) * 100.0, 1),
            "avg_tps": round(sum(opus_tps_list) / max(1, len(opus_tps_list)), 2),
            "total_time_s": round(time.perf_counter() - p2_t0, 2),
            "tests": opus_tests_results,
        }
        PROOF_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    p2_time = round(time.perf_counter() - p2_t0, 2)
    p2_avg_tps = round(sum(opus_tps_list) / max(1, len(opus_tps_list)), 2)

    print("\n" + "=" * 88)
    print(" [RESULTADO CONSOLIDADO G9V3-3B VIA LAMBDA-RLM NA RX 580 VULKAN]")
    print("=" * 88)
    print(f" * Parte 1 (13 Áreas em Inglês): {total_areas_pass}/39 ({report['part1_summary']['pct']}%) | Vel: {p1_avg_tps} t/s | Tempo: {p1_time}s")
    print(f" * Parte 2 (10 Desafios Opus EN): {opus_final_passes}/10 ({report['part2_opus_10']['final_pct']}%) | De 1ª: {opus_zero_shot}/10 | Vel: {p2_avg_tps} t/s | Tempo: {p2_time}s")
    print("=" * 88, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_benchmark())
