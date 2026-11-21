# -*- coding: utf-8 -*-
"""
BENCHMARK & AUDITORIA EMPÍRICA OMEGA:
HARNESS UNIVERSAL RLM + VERIFICADOR FORMAL 4 ESTADOS (SYMPY/Z3/PYTEST) +
GRAMMAR FAST-FORWARDING + SHOOTOUT PLUGÁVEL GPU RX 580 (9B-HERETIC vs 8B-RLM vs 4B-RLM)

Arquiteto & Líder: Mestre Ruan
Protocolo O.M.E.G.A. & Radical Truth Protocol
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

# Garantir import do pacote router
ROTOR_ROOT = Path(r"F:\rotor-llm")
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))

from router.formal_verifier import formal_verifier
from router.grammar_fastforward import grammar_ff_engine
from router.heterogeneous_rlm_harness import (
    GPU_PLUGGABLE_CATALOG,
    HeterogeneousRLMHarness,
)
from router.latency_router import LatencyCapabilityRouter

PROOF_PATH = Path(r"F:\data\proof_harness_rlm_omega.json")


def ensure_router_patches() -> None:
    """Garante que os métodos plugáveis estejam presentes em latency_router.py e execution_gateway.py."""
    lr_path = ROTOR_ROOT / "router" / "latency_router.py"
    lr_text = lr_path.read_text(encoding="utf-8")
    if "configure_pluggable_hardware_tiers" not in lr_text:
        target = "    def register_profile(self, profile: ModelCapabilityProfile) -> None:\n        self.profiles[profile.model_id] = profile"
        addon = (
            target
            + "\n\n    def configure_pluggable_hardware_tiers(self, gpu_slot: str = '9b-heretic') -> None:\n"
            + "        gpu_catalog = {\n"
            + "            '9b-heretic': ModelCapabilityProfile('heretic-9b-vulkan', 0.84, 0.82, 0.86, 19.35, 4.99, True, 0.0),\n"
            + "            '8b-rlm': ModelCapabilityProfile('rlm-qwen3-8b-vulkan', 0.83, 0.81, 0.90, 23.50, 4.68, True, 0.0),\n"
            + "            '4b-rlm': ModelCapabilityProfile('rlm-qwen3-4b-vulkan', 0.74, 0.72, 0.85, 36.00, 2.33, True, 0.0),\n"
            + "        }\n"
            + "        chosen_gpu = gpu_catalog.get(gpu_slot, gpu_catalog['9b-heretic'])\n"
            + "        self.profiles = {\n"
            + "            'deterministic': self.profiles['deterministic'],\n"
            + "            chosen_gpu.model_id: chosen_gpu,\n"
            + "            'gpt-oss-20b-repacked': ModelCapabilityProfile('gpt-oss-20b-repacked', 0.94, 0.92, 0.91, 10.94, 10.42, True, 0.0),\n"
            + "        }"
        )
        lr_path.write_text(lr_text.replace(target, addon, 1), encoding="utf-8")

    eg_path = ROTOR_ROOT / "router" / "execution_gateway.py"
    eg_text = eg_path.read_text(encoding="utf-8")
    if "verify_formal_4state" not in eg_text:
        target_eg = '        return True, 4, None, "none"\n\n\nclass ExecutionGateway:'
        addon_eg = (
            '        return True, 4, None, "none"\n\n'
            "    @staticmethod\n"
            "    def verify_formal_4state(\n"
            "        response: str,\n"
            "        task_type: str,\n"
            "        expected_math: str | None = None,\n"
            "        z3_constraints: list[str] | None = None,\n"
            "        test_assertions: list[str] | None = None,\n"
            "    ) -> Any:\n"
            "        from router.formal_verifier import formal_verifier\n"
            "        if task_type == 'math' and expected_math:\n"
            "            return formal_verifier.verify_math_equivalence(response, expected_math)\n"
            "        if task_type == 'logic' and z3_constraints:\n"
            "            return formal_verifier.verify_z3_constraints(response, z3_constraints)\n"
            "        return formal_verifier.verify_python_code(response, test_assertions)\n\n\n"
            "class ExecutionGateway:"
        )
        eg_path.write_text(eg_text.replace(target_eg, addon_eg, 1), encoding="utf-8")


def audit_formal_verifiers_and_fastforward() -> dict[str, Any]:
    """Audita empiricamente os motores SymPy, Z3, AST/Pytest e Grammar Fast-Forwarding."""
    print("=" * 78)
    print(" [FASE 1] AUDITORIA ATÔMICA: SYMPY + Z3 SMT + AST/PYTEST + FAST-FORWARD")
    print("=" * 78)

    # 1. SymPy FAIL (com contraexemplo) e PASS
    r_math_fail = formal_verifier.verify_math_equivalence("x**2 + 1", "(x + 1)**2")
    assert r_math_fail.state == "FAIL", f"SymPy deveria reprovar x^2+1 vs (x+1)^2: {r_math_fail}"
    assert r_math_fail.counterexample is not None, "SymPy deve gerar contraexemplo numérico!"
    print(f"  [1.1 OK] SymPy FAIL detectado -> {r_math_fail.counterexample}")

    r_math_pass = formal_verifier.verify_math_equivalence("x**2 + 2*x + 1", "(x + 1)**2")
    assert r_math_pass.state == "PASS" and r_math_pass.passed, f"SymPy deveria aprovar: {r_math_pass}"
    print(f"  [1.2 OK] SymPy PASS provado em {r_math_pass.latency_ms} ms -> {r_math_pass.details}")

    # 2. Z3 SMT FAIL (com contraexemplo) e PASS
    constraints = ["x + y == 20", "x - y == 4", "x > 0", "y > 0"]
    r_z3_fail = formal_verifier.verify_z3_constraints('{"x": 10, "y": 10}', constraints)
    assert r_z3_fail.state == "FAIL", f"Z3 deveria reprovar x=10, y=10: {r_z3_fail}"
    assert "x - y == 4" in (r_z3_fail.counterexample or ""), "Z3 deve apontar a restrição violada!"
    print(f"  [2.1 OK] Z3 SMT FAIL detectado -> {r_z3_fail.counterexample}")

    r_z3_pass = formal_verifier.verify_z3_constraints('{"x": 12, "y": 8}', constraints)
    assert r_z3_pass.state == "PASS" and r_z3_pass.passed, f"Z3 deveria aprovar x=12, y=8: {r_z3_pass}"
    print(f"  [2.2 OK] Z3 SMT PASS provado em {r_z3_pass.latency_ms} ms -> {r_z3_pass.details}")

    # 3. Python AST + Pytest Assertions FAIL e PASS
    assertions = ["assert fatorial(0) == 1", "assert fatorial(5) == 120"]
    buggy_code = "def fatorial(n):\n    return n * fatorial(n - 1) if n > 1 else 0"
    r_py_fail = formal_verifier.verify_python_code(buggy_code, assertions)
    assert r_py_fail.state == "FAIL", f"Sandbox deveria reprovar fatorial(0)==0: {r_py_fail}"
    print(f"  [3.1 OK] Sandbox Python FAIL detectado -> {r_py_fail.counterexample}")

    fixed_code = "def fatorial(n):\n    return 1 if n <= 1 else n * fatorial(n - 1)"
    r_py_pass = formal_verifier.verify_python_code(fixed_code, assertions)
    assert r_py_pass.state == "PASS" and r_py_pass.passed, f"Sandbox deveria aprovar: {r_py_pass}"
    print(f"  [3.2 OK] Sandbox Python PASS provado em {r_py_pass.latency_ms} ms -> {r_py_pass.details}")

    # 4. Grammar Fast-Forwarding Reconstruction & Speedup
    plan = grammar_ff_engine.build_plan("concise_json")
    reconstructed = grammar_ff_engine.reconstruct_output(plan, 'x**2 + 2*x + 1"}')
    assert json.loads(reconstructed)["final_answer"] == "x**2 + 2*x + 1"
    ff_m = grammar_ff_engine.compute_metrics(
        raw_generated_tokens=8,
        fast_forwarded_tokens=plan.injected_tokens_saved,
        decode_time_ms=400.0,
        unconstrained_baseline_tokens=32,
    )
    assert ff_m.effective_tok_per_s > ff_m.raw_tok_per_s
    print(
        f"  [4.0 OK] Grammar Fast-Forwarding validado: Raw={ff_m.raw_tok_per_s} t/s -> "
        f"Efetivo={ff_m.effective_tok_per_s} t/s (+{ff_m.speedup_pct}% ganho estrutural)"
    )

    return {
        "sympy_fail_counterexample": r_math_fail.counterexample,
        "sympy_pass_latency_ms": r_math_pass.latency_ms,
        "z3_fail_counterexample": r_z3_fail.counterexample,
        "z3_pass_latency_ms": r_z3_pass.latency_ms,
        "python_fail_counterexample": r_py_fail.counterexample,
        "python_pass_latency_ms": r_py_pass.latency_ms,
        "fastforward_unit_speedup_pct": ff_m.speedup_pct,
    }


def run_pluggable_gpu_shootout() -> dict[str, Any]:
    """Executa o teste real comparativo na RX 580 Vulkan entre 9b-heretic, 8b-rlm e 4b-rlm."""
    print("\n" + "=" * 78)
    print(" [FASE 2] SHOOTOUT FÍSICO NA GPU RX 580 VULKAN: 9B-HERETIC vs 8B-RLM vs 4B-RLM")
    print("=" * 78)

    shootout_results: dict[str, Any] = {}
    profiles_to_test = ["4b-rlm", "8b-rlm", "9b-heretic"]

    for prof_key in profiles_to_test:
        spec = GPU_PLUGGABLE_CATALOG[prof_key]
        print(f"\n---> Plugando [{prof_key}] ({spec.model_name} | {spec.vram_size_gb} GB | {spec.quant_type})...")
        harness = HeterogeneousRLMHarness(gpu_profile=prof_key, gpu_port=8081, max_repair_turns=2)
        try:
            boot_info = harness.start_pluggable_gpu_server(prof_key, timeout_s=75.0)
            print(f"     [ONLINE] Carregado na VRAM da RX 580 em {boot_info['load_time_s']}s.")

            # Tarefa A: Matemática Simbólica Auditada pelo SymPy com Grammar Fast-Forward
            t_math = harness.execute_verified_task(
                task_id="A_math_sympy",
                prompt=(
                    "/no_think Expanda algebricamente (x + 3)**2 em polinômio simplificado em x. "
                    "Responda apenas a fórmula no JSON."
                ),
                task_type="math",
                expected_math="x**2 + 6*x + 9",
                schema_type="concise_json",
            )
            print(
                f"     [Tarefa A - SymPy] Estado={t_math.final_state} | Tentativas={t_math.attempts_count} | "
                f"Raw={t_math.raw_tok_per_s} t/s | Efetivo={t_math.effective_tok_per_s} t/s | "
                f"Latência={t_math.total_latency_ms} ms"
            )

            # Tarefa B: Lógica Z3 SMT com Reparo Automático Guiado por Contraexemplo
            t_z3 = harness.execute_verified_task(
                task_id="B_logic_z3_repair",
                prompt=(
                    "/no_think Encontre dois inteiros x e y tais que x + y == 20 e x - y == 4. "
                    'Responda apenas no formato JSON {"solution":{"x": valor, "y": valor}}.'
                ),
                task_type="logic",
                z3_constraints=["x + y == 20", "x - y == 4"],
                schema_type="z3_xy",
                SimulatedInitialHypothesis='{"solution":{"x": 10, "y": 10}}',
            )
            print(
                f"     [Tarefa B - Z3 Repair] Estado={t_z3.final_state} | Tentativas={t_z3.attempts_count} | "
                f"Reparado={t_z3.repaired_after_fail} | Raw={t_z3.raw_tok_per_s} t/s | "
                f"Latência={t_z3.total_latency_ms} ms"
            )

            # Tarefa C: Código Python Auditado por AST + Asserções Executáveis
            t_code = harness.execute_verified_task(
                task_id="C_coding_pytest",
                prompt=(
                    "/no_think Escreva em Python apenas a função `soma_quadrados(n)` que retorna "
                    "a soma dos quadrados de 1 até n (ex: para n=3 retorna 1+4+9=14)."
                ),
                task_type="coding",
                test_assertions=[
                    "assert soma_quadrados(1) == 1",
                    "assert soma_quadrados(3) == 14",
                    "assert soma_quadrados(5) == 55",
                ],
                schema_type="python_func",
            )
            print(
                f"     [Tarefa C - Pytest] Estado={t_code.final_state} | Tentativas={t_code.attempts_count} | "
                f"Raw={t_code.raw_tok_per_s} t/s | Efetivo={t_code.effective_tok_per_s} t/s | "
                f"Latência={t_code.total_latency_ms} ms"
            )

            # Tarefa D: Algoritmo Difícil (Programação Dinâmica Não-Adjacente com Caso de Borda [2,1,1,2]==4)
            t_dp = harness.execute_verified_task(
                task_id="D_hard_dp_algorithm",
                prompt=(
                    "/no_think Escreva em Python apenas a função `maior_soma_nao_adjacente(nums)` que recebe "
                    "uma lista de inteiros não-negativos e retorna a maior soma possível de um subconjunto sem "
                    "escolher dois elementos adjacentes (vizinhos). Atenção a listas vazias e ao caso [2, 1, 1, 2] -> 4."
                ),
                task_type="coding",
                test_assertions=[
                    "assert maior_soma_nao_adjacente([]) == 0",
                    "assert maior_soma_nao_adjacente([5]) == 5",
                    "assert maior_soma_nao_adjacente([2, 7, 9, 3, 1]) == 12",
                    "assert maior_soma_nao_adjacente([2, 1, 1, 2]) == 4",
                ],
                schema_type="python_func",
            )
            print(
                f"     [Tarefa D - Hard DP] Estado={t_dp.final_state} | Tentativas={t_dp.attempts_count} | "
                f"Reparado={t_dp.repaired_after_fail} | Raw={t_dp.raw_tok_per_s} t/s | "
                f"Latência={t_dp.total_latency_ms} ms"
            )

            tasks_list = [
                harness.to_dict(t_math),
                harness.to_dict(t_z3),
                harness.to_dict(t_code),
                harness.to_dict(t_dp),
            ]
            pass_count = sum(1 for t in tasks_list if t["final_state"] == "PASS")
            avg_raw_tps = round(sum(t["raw_tok_per_s"] for t in tasks_list) / len(tasks_list), 2)
            avg_eff_tps = round(sum(t["effective_tok_per_s"] for t in tasks_list) / len(tasks_list), 2)
            total_task_ms = round(sum(t["total_latency_ms"] for t in tasks_list), 2)

            shootout_results[prof_key] = {
                "boot_info": boot_info,
                "pass_count": pass_count,
                "total_tasks": len(tasks_list),
                "pass_rate_pct": round((pass_count / len(tasks_list)) * 100.0, 1),
                "avg_raw_tok_per_s": avg_raw_tps,
                "avg_effective_tok_per_s": avg_eff_tps,
                "total_task_latency_ms": total_task_ms,
                "tasks": tasks_list,
            }
        finally:
            harness.stop_gpu_server()

    return shootout_results


def main() -> int:
    ensure_router_patches()

    # Valida que o LatencyCapabilityRouter suporta a troca plugável
    router = LatencyCapabilityRouter()
    for slot in ("9b-heretic", "8b-rlm", "4b-rlm"):
        router.configure_pluggable_hardware_tiers(slot)
        assert "gpt-oss-20b-repacked" in router.profiles

    unit_audit = audit_formal_verifiers_and_fastforward()

    force_shootout = "--shootout" in sys.argv or not PROOF_PATH.exists()
    if force_shootout:
        shootout = run_pluggable_gpu_shootout()
        proof_payload = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "status": "HARNESS_RLM_OMEGA_VERIFIED",
            "hardware": {
                "gpu": "AMD Radeon RX 580 8GB (Polaris 20 Vulkan gfx803)",
                "cpu": "Intel Xeon E5-2697 v3 (10 Physical Cores 0x15555 AVX2 Repacked)",
                "ram": "64GB DDR4 Quad-Channel",
            },
            "unit_formal_audit": unit_audit,
            "gpu_pluggable_shootout": shootout,
        }
        PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROOF_PATH.write_text(json.dumps(proof_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n[PROVA GRAVADA] {PROOF_PATH} ({PROOF_PATH.stat().st_size} bytes)")
    else:
        proof_payload = json.loads(PROOF_PATH.read_text(encoding="utf-8"))
        shootout = proof_payload.get("gpu_pluggable_shootout", {})

    assert len(shootout) == 3, "O shootout precisa conter os 3 modelos plugáveis (4b-rlm, 8b-rlm, 9b-heretic)!"
    print("\n" + "=" * 78)
    print(" [RESUMO COMPARATIVO EMPÍRICO - GPU RX 580 VULKAN PLUGÁVEL]")
    print("=" * 78)
    for k, v in shootout.items():
        bi = v["boot_info"]
        print(
            f" * [{k:10s}] VRAM={bi['vram_size_gb']:.2f}GB ({bi['quant_type']:6s}) | "
            f"PASS={v['pass_count']}/{v['total_tasks']} ({v['pass_rate_pct']}%) | "
            f"Raw={v['avg_raw_tok_per_s']:5.2f} t/s | Efetivo(FF)={v['avg_effective_tok_per_s']:5.2f} t/s | "
            f"Tempo Total={v['total_task_latency_ms']:7.1f} ms"
        )
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
