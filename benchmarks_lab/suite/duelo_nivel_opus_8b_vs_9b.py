# -*- coding: utf-8 -*-
"""
DUELO EXTREMO NÍVEL CLAUDE OPUS / GRANDMASTER (10 TESTES ALGORÍTMICOS IMPLACÁVEIS):
[8b-rlm] (rlm-qwen3-8b-v0.1-Q4_K_M | 4.68 GB) vs [9b-heretic] (Qwen3.8-9B-Heretic-IQ4_XS | 4.99 GB)

Cada desafio contém armadilhas formais de casos de borda que reprovam soluções ingênuas ou decoradas.
Arquiteto & Líder: Mestre Ruan
Protocolo O.M.E.G.A. & Radical Truth Protocol
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROTOR_ROOT = Path(r"F:\rotor-llm")
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))

from router.formal_verifier import formal_verifier
from router.heterogeneous_rlm_harness import (
    GPU_PLUGGABLE_CATALOG,
    HeterogeneousRLMHarness,
)

PROOF_OPUS_PATH = Path(r"F:\data\proof_duelo_opus_8b_vs_9b.json")

OPUS_10_TESTS: list[dict[str, Any]] = [
    {
        "id": "OPUS_01_regex_plus_star_dot",
        "name": "01. Motor Regex Puro com '.', '*' e '+' (Sem módulo re)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `casamento_padrao(texto, padrao)` (sem comentários e SEM importar `re`) "
            "que faz o casamento exato da string inteira `texto` com `padrao`, onde '.' casa qualquer caractere, "
            "'*' casa zero ou mais do caractere anterior, e '+' casa UMA ou mais vezes o caractere anterior."
        ),
        "assertions": [
            "import inspect; assert 're.' not in inspect.getsource(casamento_padrao)",
            "assert casamento_padrao('aa', 'a') is False",
            "assert casamento_padrao('aa', 'a*') is True",
            "assert casamento_padrao('a', 'ab*') is True",
            "assert casamento_padrao('a', 'ab+') is False",
            "assert casamento_padrao('abbb', 'ab+') is True",
            "assert casamento_padrao('aab', 'c*a+b') is True",
            "assert casamento_padrao('mississippi', 'mis*is*p*.') is False",
        ],
    },
    {
        "id": "OPUS_02_parser_unario_potencia_direita",
        "name": "02. Parser Algébrico Sem eval() c/ Unário e '^' Associativo à Direita",
        "prompt": (
            "/no_think Escreva em Python apenas a função `avaliar_expr(expr)` (sem comentários e PROIBIDO usar `eval`, `exec` ou `compile`) "
            "que avalia uma expressão matemática com inteiros, '+', '-', '*', '//', parênteses '()', menos unário (ex: '-5 + 2' ou '2 * (-3)') "
            "e potência '^' associativa à direita (ex: '2 ^ 3 ^ 2' = 2**(3**2) = 512)."
        ),
        "assertions": [
            "import inspect; src = inspect.getsource(avaliar_expr); assert 'eval(' not in src and 'exec(' not in src",
            "assert avaliar_expr('2 + 3 * 4') == 14",
            "assert avaliar_expr('2 * (-3 + 1)') == -4",
            "assert avaliar_expr('-5 + 2') == -3",
            "assert avaliar_expr('2 ^ 3 ^ 2') == 512",
            "assert avaliar_expr('(10 - 2) // 3') == 2",
        ],
    },
    {
        "id": "OPUS_03_dijkstra_k_pedagios_gratis",
        "name": "03. Dijkstra 2D no Espaço de Estados (Até K Arestas Grátis)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `menor_custo_k_gratis(n, arestas, k)` (sem comentários) "
            "onde `n` é o número de nós (0 a n-1), `arestas` é uma lista de tuplas `(u, v, peso)` bidirecionais e `k` é o número "
            "máximo de arestas cujo peso pode ser zerado no caminho. Retorne o menor custo de 0 até n-1 (ou -1 se inalcançável)."
        ),
        "assertions": [
            "assert menor_custo_k_gratis(4, [(0,1,10), (1,3,10), (0,2,1), (2,3,100)], 1) == 1",
            "assert menor_custo_k_gratis(4, [(0,1,10), (1,3,10), (0,2,1), (2,3,100)], 0) == 20",
            "assert menor_custo_k_gratis(3, [(0,1,5)], 1) == -1",
            "assert menor_custo_k_gratis(3, [(0,1,5), (1,2,7)], 2) == 0",
        ],
    },
    {
        "id": "OPUS_04_maior_retangulo_matriz_binaria",
        "name": "04. Pilha Monotônica 2D: Maior Retângulo de 1s em Matriz",
        "prompt": (
            "/no_think Escreva em Python apenas a função `maior_retangulo_binario(matriz)` (sem comentários) "
            "que recebe uma matriz 2D de inteiros 0 e 1 e retorna a área do maior retângulo contendo apenas 1s (para [] retorna 0)."
        ),
        "assertions": [
            "assert maior_retangulo_binario([[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]) == 6",
            "assert maior_retangulo_binario([[0]]) == 0",
            "assert maior_retangulo_binario([[1]]) == 1",
            "assert maior_retangulo_binario([[1,1],[1,1]]) == 4",
            "assert maior_retangulo_binario([]) == 0",
        ],
    },
    {
        "id": "OPUS_05_bitmask_dp_tsp_aberto",
        "name": "05. Bitmask DP: Caminho Hamiltoniano Mínimo (TSP Aberto)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `tsp_aberto(dist)` (sem comentários) que recebe uma matriz "
            "quadrada `dist` (N x N) e retorna o custo mínimo para começar no nó 0 e visitar todos os N nós exatamente uma vez (sem voltar ao 0)."
        ),
        "assertions": [
            "assert tsp_aberto([[0]]) == 0",
            "assert tsp_aberto([[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]) == 65",
            "assert tsp_aberto([[0, 1, 10], [1, 0, 2], [10, 2, 0]]) == 3",
        ],
    },
    {
        "id": "OPUS_06_mediana_dois_arrays_ordenados",
        "name": "06. Busca Particionada: Mediana de Dois Arrays Ordenados",
        "prompt": (
            "/no_think Escreva em Python apenas a função `mediana_ordenada(a, b)` (sem comentários) "
            "que retorna a mediana exata como `float` de duas listas ordenadas `a` e `b`."
        ),
        "assertions": [
            "assert float(mediana_ordenada([1, 3], [2])) == 2.0",
            "assert float(mediana_ordenada([1, 2], [3, 4])) == 2.5",
            "assert float(mediana_ordenada([], [1])) == 1.0",
            "assert float(mediana_ordenada([-5, 3, 6, 12, 15], [-12, -10, -6, -3, 4, 10])) == 3.0",
        ],
    },
    {
        "id": "OPUS_07_maior_parenteses_valido_trap",
        "name": "07. DP/Pilha de Índices: Maior Substring de Parênteses Válidos",
        "prompt": (
            "/no_think Escreva em Python apenas a função `maior_parenteses_valido(s)` (sem comentários) "
            "que retorna o tamanho da maior substring contínua de parênteses bem formados em `s` (ex: para '()(()' retorna 2, para ')()())' retorna 4)."
        ),
        "assertions": [
            "assert maior_parenteses_valido('(()') == 2",
            "assert maior_parenteses_valido(')()())') == 4",
            "assert maior_parenteses_valido('()(()') == 2",
            "assert maior_parenteses_valido('()(())') == 6",
            "assert maior_parenteses_valido('') == 0",
        ],
    },
    {
        "id": "OPUS_08_trapping_rain_water",
        "name": "08. Two-Pointers: Água da Chuva Retida entre Barras",
        "prompt": (
            "/no_think Escreva em Python apenas a função `agua_retida(alturas)` (sem comentários) "
            "que recebe uma lista de inteiros não-negativos representando alturas de barras e retorna o total de água retida após chover."
        ),
        "assertions": [
            "assert agua_retida([0,1,0,2,1,0,1,3,2,1,2,1]) == 6",
            "assert agua_retida([4,2,0,3,2,5]) == 9",
            "assert agua_retida([3, 2, 1]) == 0",
            "assert agua_retida([]) == 0",
            "assert agua_retida([5, 0, 5]) == 5",
        ],
    },
    {
        "id": "OPUS_09_arvore_caminho_maximo_negativos",
        "name": "09. Árvore Binária: Maior Soma de Caminho Any-to-Any (c/ Negativos)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `maior_caminho_arvore(raiz)` (sem comentários) "
            "onde cada nó é um dict `{'v': int, 'l': dict|None, 'r': dict|None}`. Retorne a maior soma de qualquer caminho "
            "não-vazio entre dois nós quaisquer da árvore (atenção: se a árvore for `{'v': -3, 'l': None, 'r': None}`, deve retornar -3)."
        ),
        "assertions": [
            "assert maior_caminho_arvore({'v': 1, 'l': {'v': 2, 'l': None, 'r': None}, 'r': {'v': 3, 'l': None, 'r': None}}) == 6",
            "assert maior_caminho_arvore({'v': -10, 'l': {'v': 9, 'l': None, 'r': None}, 'r': {'v': 20, 'l': {'v': 15, 'l': None, 'r': None}, 'r': {'v': 7, 'l': None, 'r': None}}}) == 42",
            "assert maior_caminho_arvore({'v': -3, 'l': None, 'r': None}) == -3",
            "assert maior_caminho_arvore({'v': 2, 'l': {'v': -1, 'l': None, 'r': None}, 'r': None}) == 2",
        ],
    },
    {
        "id": "OPUS_10_solver_dpll_sat_cnf",
        "name": "10. Solver Lógico DPLL SAT para Fórmulas CNF",
        "prompt": (
            "/no_think Escreva em Python apenas a função `resolver_sat_cnf(num_vars, clausulas)` (sem comentários) "
            "onde `num_vars` é o total de variáveis (1 a num_vars) e `clausulas` é uma lista de listas de literais inteiros "
            "(ex: `[1, -2]` significa x1=True ou x2=False). Retorne um dict `{1: bool, ..., num_vars: bool}` que satisfaça todas as cláusulas, ou `None` se for insatisfatível (UNSAT)."
        ),
        "assertions": [
            "r1 = resolver_sat_cnf(2, [[1, 2], [1, -2], [-1, 2]]); assert isinstance(r1, dict) and r1[1] is True and r1[2] is True",
            "assert resolver_sat_cnf(1, [[1], [-1]]) is None",
            "assert resolver_sat_cnf(2, [[1, 2], [-1, 2], [1, -2], [-1, -2]]) is None",
            "r2 = resolver_sat_cnf(3, [[1], [-1, 2], [-2, 3]]); assert isinstance(r2, dict) and r2[1] is True and r2[2] is True and r2[3] is True",
        ],
    },
]


def run_opus_duel() -> int:
    contenders = ["8b-rlm", "9b-heretic"]
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duel": "ROUND 2: Duelo Extremo Nível Claude Opus (10 Algoritmos Hardcore)",
        "contenders": {},
    }

    for prof_key in contenders:
        spec = GPU_PLUGGABLE_CATALOG[prof_key]
        print("\n" + "=" * 88)
        print(f" [ROUND 2: NÍVEL CLAUDE OPUS - 10 TESTES] MODELO: [{prof_key}] ({spec.model_name})")
        print("=" * 88, flush=True)

        harness = HeterogeneousRLMHarness(gpu_profile=prof_key, gpu_port=8081, max_repair_turns=1)
        try:
            boot_info = harness.start_pluggable_gpu_server(prof_key, timeout_s=75.0)
            print(f" -> [GPU ONLINE] Carregado em {boot_info['load_time_s']}s na RX 580 Vulkan.", flush=True)

            zero_shot_passes = 0
            final_passes = 0
            repaired_count = 0
            tps_list: list[float] = []
            eff_tps_list: list[float] = []
            total_ms = 0.0
            test_results: list[dict[str, Any]] = []

            for test in OPUS_10_TESTS:
                t_start = time.perf_counter()
                attempts = 0
                current_prompt = test["prompt"]
                first_try_passed = False
                final_passed = False
                initial_ce: str | None = None
                last_code = ""
                last_raw_tps = 0.0
                last_eff_tps = 0.0

                while attempts < 2:
                    attempts += 1
                    last_code, ff_m = harness.query_completion(
                        prompt=current_prompt,
                        port=8081,
                        n_predict=320,
                        schema_type="python_func",
                    )
                    last_raw_tps = ff_m.raw_tok_per_s
                    last_eff_tps = ff_m.effective_tok_per_s

                    ver = formal_verifier.verify_python_code(last_code, test["assertions"], timeout_s=4.0)
                    if ver.passed:
                        final_passed = True
                        if attempts == 1:
                            first_try_passed = True
                        break

                    if attempts == 1:
                        initial_ce = ver.counterexample
                        current_prompt = (
                            f"{test['prompt']}\n\n"
                            f"Sua tentativa anterior falhou no verificador formal:\n{ver.counterexample}\n"
                            f"Corrija o algoritmo para passar em todos os casos de borda (sem comentários)."
                        )

                elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                total_ms += elapsed_ms
                if first_try_passed:
                    zero_shot_passes += 1
                if final_passed:
                    final_passes += 1
                if final_passed and attempts > 1:
                    repaired_count += 1
                if last_raw_tps > 0:
                    tps_list.append(last_raw_tps)
                    eff_tps_list.append(last_eff_tps)

                status_badge = (
                    "PASS (1ª Tentativa)"
                    if first_try_passed
                    else ("PASS (Reparado 2ª)" if final_passed else "FAIL (Não escapou)")
                )
                print(
                    f"    [{prof_key:10s}] {test['name']:62s} | {status_badge:18s} | "
                    f"Vel: {last_raw_tps:5.2f} t/s | Tempo: {elapsed_ms:7.1f} ms",
                    flush=True,
                )

                test_results.append(
                    {
                        "test_id": test["id"],
                        "test_name": test["name"],
                        "zero_shot_pass": first_try_passed,
                        "final_pass": final_passed,
                        "attempts": attempts,
                        "repaired": (final_passed and attempts > 1),
                        "initial_counterexample": initial_ce,
                        "raw_tok_per_s": last_raw_tps,
                        "effective_tok_per_s": last_eff_tps,
                        "latency_ms": elapsed_ms,
                        "code_generated": last_code,
                    }
                )

            avg_raw = round(sum(tps_list) / max(1, len(tps_list)), 2)
            avg_eff = round(sum(eff_tps_list) / max(1, len(eff_tps_list)), 2)
            report["contenders"][prof_key] = {
                "boot_info": boot_info,
                "zero_shot_passes": zero_shot_passes,
                "final_passes": final_passes,
                "repaired_passes": repaired_count,
                "total_tests": len(OPUS_10_TESTS),
                "zero_shot_pct": round((zero_shot_passes / len(OPUS_10_TESTS)) * 100.0, 1),
                "final_pass_pct": round((final_passes / len(OPUS_10_TESTS)) * 100.0, 1),
                "avg_raw_tok_per_s": avg_raw,
                "avg_effective_tok_per_s": avg_eff,
                "total_time_s": round(total_ms / 1000.0, 2),
                "tests": test_results,
            }
            PROOF_OPUS_PATH.parent.mkdir(parents=True, exist_ok=True)
            PROOF_OPUS_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(
                f" -> [{prof_key} CONCLUÍDO]: De 1ª={zero_shot_passes}/10 ({zero_shot_passes*10}%) | "
                f"Final(c/ Reparo)={final_passes}/10 ({final_passes*10}%) | "
                f"Vel Média={avg_raw} t/s | Tempo Total={total_ms/1000.0:.2f}s",
                flush=True,
            )
        finally:
            harness.stop_gpu_server()

    print("\n" + "=" * 88)
    print(" [PLACAR FINAL DO ROUND 2 (NÍVEL CLAUDE OPUS): 8B-RLM vs 9B-HERETIC]")
    print("=" * 88)
    for pk, cdata in report["contenders"].items():
        print(
            f" * [{pk:10s}] Acerto de 1ª: {cdata['zero_shot_passes']:2d}/10 ({cdata['zero_shot_pct']:5.1f}%) | "
            f"Final c/ Reparo: {cdata['final_passes']:2d}/10 ({cdata['final_pass_pct']:5.1f}%) | "
            f"Vel: {cdata['avg_raw_tok_per_s']:5.2f} t/s | Tempo: {cdata['total_time_s']:6.2f}s"
        )
    print("=" * 88, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_opus_duel())
