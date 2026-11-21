# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Teste de Produção em Ciclo Fechado: Arquitetura Two-Tier Consolidada
Tier 1: GPU RX 580 Vulkan (Porta 8081) -> rlm-qwen3-8b-v0.1-Q4_K_M (Titular Definitivo)
Tier 2: CPU Xeon 10C AVX2 (Porta 8083) -> gpt-oss-20b-antidoom.i1-IQ4_XS

Homologação com Verificador Formal de 4 Estados, Grammar Fast-Forwarding
e Ciclo de Autocorreção Guiado por Contraexemplo.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from router.formal_verifier import formal_verifier
from router.grammar_fastforward import grammar_ff_engine
from router.heterogeneous_rlm_harness import HeterogeneousRLMHarness

PROOF_PATH = Path(r"F:\data\proof_producao_twotier_fechado.json")


def run_production_two_tier_closed_loop() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass
    print("\n" + "=" * 88)
    print(" [PRODUÇÃO TWO-TIER] INICIANDO HOMOLOGAÇÃO DO SISTEMA CONSOLIDADO")
    print(" Tier 1 GPU (8081): rlm-qwen3-8b-v0.1 (Titular Vencedor)")
    print(" Tier 2 CPU (8083): gpt-oss-20b-antidoom (Pesado nos 10 Núcleos Xeon AVX2)")
    print("=" * 88, flush=True)

    harness = HeterogeneousRLMHarness(gpu_profile="8b-rlm", gpu_port=8081, cpu_port=8083, max_repair_turns=2)
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "architecture": "Two-Tier Heterogeneous (RX 580 8GB Vulkan + Xeon 10C AVX2 Repacked)",
        "titular_gpu": "rlm-qwen3-8b-v0.1-Q4_K_M",
        "titular_cpu": "gpt-oss-20b-antidoom.i1-IQ4_XS",
        "steps": [],
    }

    try:
        # 1. Boot Tier 1 GPU
        print(" -> [1/4] Subindo Tier 1 GPU (8b-rlm) na porta 8081...", flush=True)
        gpu_boot = harness.start_pluggable_gpu_server("8b-rlm", timeout_s=60.0)
        print(f"    [OK] GPU Online em {gpu_boot['load_time_s']}s.", flush=True)
        report["gpu_boot"] = gpu_boot

        # 2. Boot Tier 2 CPU
        print(" -> [2/4] Subindo Tier 2 CPU (gpt-oss-20b) na porta 8083...", flush=True)
        cpu_boot = harness.start_cpu_server(timeout_s=240.0)
        print(f"    [OK] CPU Online em {cpu_boot['load_time_s']}s.", flush=True)
        report["cpu_boot"] = cpu_boot

        # 3. Teste 1: Tier 1 GPU - Fast Algebraic / SymPy Pass com Grammar Fast-Forwarding
        print(" -> [3/4] Executando Cenário 1 (GPU Fast-Pass c/ Fast-Forwarding)...", flush=True)
        t0 = time.perf_counter()
        math_prompt = (
            "Dada a equação 3*x + 12 = 33, resolva para x. "
            "Responda estritamente no formato JSON: {\"final_answer\": \"<numero>\"}."
        )
        math_raw, ff_metrics = harness.query_completion(
            prompt=math_prompt,
            port=8081,
            n_predict=64,
            schema_type="concise_json",
            unconstrained_baseline_tokens=80,
        )
        ver_math = formal_verifier.verify_math_equivalence(math_raw, "7")
        elapsed_math = round((time.perf_counter() - t0) * 1000.0, 2)
        print(
            f"    [GPU Tier 1] Resposta: {math_raw[:45]}... | "
            f"Status: {ver_math.state} | Vel: {ff_metrics.raw_tok_per_s:.2f} t/s "
            f"(Efetiva: {ff_metrics.effective_tok_per_s:.2f} t/s, +{ff_metrics.speedup_pct:.1f}%) | "
            f"Latência: {elapsed_math} ms",
            flush=True,
        )
        if ver_math.state != "PASS":
            print(f"ERRO: Falha na verificação matemática: {ver_math.counterexample}")
            return 1

        report["steps"].append(
            {
                "step": "cenario_1_gpu_fast_pass",
                "tier": 1,
                "model": "8b-rlm",
                "status": ver_math.state,
                "raw_tps": ff_metrics.raw_tok_per_s,
                "effective_tps": ff_metrics.effective_tok_per_s,
                "latency_ms": elapsed_math,
                "output": math_raw,
            }
        )

        # 4. Teste 2: Tier 1 GPU - Engenharia de Código (DP 1D) com Verificação Formal Pytest
        print(" -> [4/4] Executando Cenário 2 (GPU Código Formal Pytest)...", flush=True)
        t1 = time.perf_counter()
        code_prompt = (
            "Implemente em Python a função def max_soma_nao_adjacente(nums: list[int]) -> int "
            "que calcula a maior soma de elementos não adjacentes em O(n) tempo e O(1) espaço. "
            "Não adicione comentários, apenas o código limpo."
        )
        code_raw, ff_code_m = harness.query_completion(
            prompt=code_prompt,
            port=8081,
            n_predict=220,
            schema_type="python_func",
        )
        assertions = [
            "assert max_soma_nao_adjacente([2, 7, 9, 3, 1]) == 12",
            "assert max_soma_nao_adjacente([2, 1, 1, 2]) == 4",
            "assert max_soma_nao_adjacente([]) == 0",
        ]
        ver_code = formal_verifier.verify_python_code(code_raw, assertions, timeout_s=4.0)
        elapsed_code = round((time.perf_counter() - t1) * 1000.0, 2)
        print(
            f"    [GPU Tier 1] Código gerado: {len(code_raw)} chars | "
            f"Status: {'PASS' if ver_code.passed else 'FAIL'} | "
            f"Vel: {ff_code_m.raw_tok_per_s:.2f} t/s | Latência: {elapsed_code} ms",
            flush=True,
        )
        if not ver_code.passed:
            print(f"ERRO: Código do 8b-rlm falhou: {ver_code.counterexample}")
            return 1

        report["steps"].append(
            {
                "step": "cenario_2_gpu_codigo_formal",
                "tier": 1,
                "model": "8b-rlm",
                "status": "PASS",
                "raw_tps": ff_code_m.raw_tok_per_s,
                "effective_tps": ff_code_m.effective_tok_per_s,
                "latency_ms": elapsed_code,
                "code": code_raw,
            }
        )

        # 5. Teste 3: Tier 2 CPU (Xeon 20B) - Escalonamento Zero-Lag com Verificação SMT Z3
        print(" -> [5/5] Executando Cenário 3 (Escalonamento ao Tier 2 CPU Xeon 20B com Z3)...", flush=True)
        t2 = time.perf_counter()
        cpu_prompt = (
            "Resolva o sistema de congruências lógicas em números inteiros: "
            "x + y = 20 e 2*x - y = 10. "
            "Retorne estritamente o objeto JSON: {\"solution\":{\"x\": <int>, \"y\": <int>}}."
        )
        cpu_raw, ff_cpu_m = harness.query_completion(
            prompt=cpu_prompt,
            port=8083,
            n_predict=48,
            schema_type="z3_xy",
        )
        import re
        constraints = ["x + y == 20", "2*x - y == 10"]
        mx = re.search(r'"x":\s*(-?\d+)', cpu_raw)
        my = re.search(r'"y":\s*(-?\d+)', cpu_raw)
        if mx and my:
            real_assign = {"x": int(mx.group(1)), "y": int(my.group(1))}
            ver_z3 = formal_verifier.verify_z3_constraints(real_assign, constraints)
        else:
            ver_z3 = formal_verifier.verify_z3_constraints(cpu_raw, constraints)
        elapsed_cpu = round((time.perf_counter() - t2) * 1000.0, 2)
        print(
            f"    [CPU Tier 2 Xeon] Resposta: {cpu_raw.strip()} | "
            f"Status Z3: {ver_z3.state} | Vel: {ff_cpu_m.raw_tok_per_s:.2f} t/s | "
            f"Latência: {elapsed_cpu} ms",
            flush=True,
        )
        if ver_z3.state != "PASS":
            print(f"ERRO: Verificação Z3 no Tier 2 falhou: {ver_z3.counterexample}")
            return 1

        report["steps"].append(
            {
                "step": "cenario_3_cpu_xeon_20b_z3",
                "tier": 2,
                "model": "gpt-oss-20b-antidoom",
                "status": ver_z3.state,
                "raw_tps": ff_cpu_m.raw_tok_per_s,
                "effective_tps": ff_cpu_m.effective_tok_per_s,
                "latency_ms": elapsed_cpu,
                "output": cpu_raw.strip(),
            }
        )

        report["final_status"] = "ALL_TIERS_OPERATIONAL_AND_VERIFIED"
        PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROOF_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print("\n" + "=" * 88)
        print(" [SUCESSO TOTAL] ARQUITETURA TWO-TIER HOMOLOGADA E OPERACIONAL!")
        print(f" Prova gravada em: {PROOF_PATH}")
        print("=" * 88, flush=True)
        return 0

    except Exception as e:
        import traceback
        print(f"\n[FALHA DE EXECUÇÃO]: {e}", flush=True)
        traceback.print_exc()
        return 1

    finally:
        print(" -> Encerrando processos dos servidores de teste...", flush=True)
        harness.stop_all_servers()


if __name__ == "__main__":
    sys.exit(run_production_two_tier_closed_loop())
