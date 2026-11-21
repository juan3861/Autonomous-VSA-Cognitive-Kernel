# -*- coding: utf-8 -*-
"""
DUELO PESADO DE ENGENHARIA DE CÓDIGO (10 TESTES ALGORÍTMICOS VERIFICADOS POR AST/PYTEST):
[8b-rlm] (rlm-qwen3-8b-v0.1-Q4_K_M | 4.68 GB) vs [9b-heretic] (Qwen3.8-9B-Heretic-IQ4_XS | 4.99 GB)
4b-rlm desclassificado pelo Mestre Ruan (restrito a triagem simples).

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

PROOF_DUEL_PATH = Path(r"F:\data\proof_duelo_codigo_8b_vs_9b.json")

CODING_10_TESTS: list[dict[str, Any]] = [
    {
        "id": "C01_busca_binaria_rotacionada",
        "name": "01. Busca Binária em Array Rotacionado",
        "prompt": (
            "/no_think Escreva em Python apenas a função `busca_rotacionada(nums, target)` (sem comentários) "
            "que retorna o índice de `target` em uma lista ordenada rotacionada `nums` ou -1 se não existir."
        ),
        "assertions": [
            "assert busca_rotacionada([4, 5, 6, 7, 0, 1, 2], 0) == 4",
            "assert busca_rotacionada([4, 5, 6, 7, 0, 1, 2], 3) == -1",
            "assert busca_rotacionada([1], 0) == -1",
            "assert busca_rotacionada([3, 1], 1) == 1",
        ],
    },
    {
        "id": "C02_palindromo_alfanumerico",
        "name": "02. Palíndromo Alfanumérico (Ignorando Pontuação/Espaços)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `eh_palindromo_limpo(s)` (sem comentários) que filtra "
            "apenas caracteres alfanuméricos (`c.isalnum()`) em minúsculas e retorna True se for palíndromo ou False caso contrário."
        ),
        "assertions": [
            "assert eh_palindromo_limpo('A man, a plan, a canal: Panama') is True",
            "assert eh_palindromo_limpo('Socorram-me, subi no onibus em Marrocos!') is True",
            "assert eh_palindromo_limpo('race a car') is False",
            "assert eh_palindromo_limpo(' ') is True",
        ],
    },
    {
        "id": "C03_dp_soma_nao_adjacente",
        "name": "03. DP 1D: Maior Soma Não-Adjacente (House Robber)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `max_nao_adj(nums)` (sem comentários) que retorna a maior "
            "soma possível de elementos não-adjacentes da lista `nums` (para [] retorna 0, para [2, 1, 1, 2] retorna 4)."
        ),
        "assertions": [
            "assert max_nao_adj([]) == 0",
            "assert max_nao_adj([5]) == 5",
            "assert max_nao_adj([2, 7, 9, 3, 1]) == 12",
            "assert max_nao_adj([2, 1, 1, 2]) == 4",
        ],
    },
    {
        "id": "C04_dp_troco_minimo",
        "name": "04. DP: Troco Mínimo de Moedas (Armadilha Anti-Gulosa [1,3,4]->6)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `troco_minimo(moedas, valor)` (sem comentários) usando "
            "programação dinâmica que retorna a quantidade mínima de moedas para somar `valor`, ou -1 se impossível."
        ),
        "assertions": [
            "assert troco_minimo([1, 2, 5], 11) == 3",
            "assert troco_minimo([2], 3) == -1",
            "assert troco_minimo([1], 0) == 0",
            "assert troco_minimo([1, 3, 4], 6) == 2",
        ],
    },
    {
        "id": "C05_dp_levenshtein",
        "name": "05. DP 2D: Distância de Edição de Levenshtein",
        "prompt": (
            "/no_think Escreva em Python apenas a função `distancia_edicao(s1, s2)` (sem comentários) usando "
            "programação dinâmica 2D que retorna o número mínimo de operações (inserir, remover, substituir) para converter `s1` em `s2`."
        ),
        "assertions": [
            "assert distancia_edicao('horse', 'ros') == 3",
            "assert distancia_edicao('intention', 'execution') == 5",
            "assert distancia_edicao('', 'abc') == 3",
            "assert distancia_edicao('abc', 'abc') == 0",
        ],
    },
    {
        "id": "C06_dp_lis_crescente",
        "name": "06. DP: Maior Subsequência Estritamente Crescente (LIS)",
        "prompt": (
            "/no_think Escreva em Python apenas a função `tamanho_lis(nums)` (sem comentários) que retorna o "
            "comprimento da maior subsequência estritamente crescente de `nums` (para [] retorna 0)."
        ),
        "assertions": [
            "assert tamanho_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4",
            "assert tamanho_lis([0, 1, 0, 3, 2, 3]) == 4",
            "assert tamanho_lis([7, 7, 7, 7]) == 1",
            "assert tamanho_lis([]) == 0",
        ],
    },
    {
        "id": "C07_fusao_intervalos",
        "name": "07. Varredura: Fusão de Intervalos Sobrepostos",
        "prompt": (
            "/no_think Escreva em Python apenas a função `fundir_intervalos(intervalos)` (sem comentários) que ordena "
            "uma lista de intervalos `[inicio, fim]` e funde todos os intervalos sobrepostos retornando listas `[inicio, fim]`."
        ),
        "assertions": [
            "assert [list(x) for x in fundir_intervalos([[1, 3], [2, 6], [8, 10], [15, 18]])] == [[1, 6], [8, 10], [15, 18]]",
            "assert [list(x) for x in fundir_intervalos([[1, 4], [4, 5]])] == [[1, 5]]",
            "assert [list(x) for x in fundir_intervalos([[4, 7], [1, 4]])] == [[1, 7]]",
        ],
    },
    {
        "id": "C08_pilha_parenteses",
        "name": "08. Pilha: Validador de Delimitadores Balanceados ()[]{}",
        "prompt": (
            "/no_think Escreva em Python apenas a função `parenteses_validos(s)` (sem comentários) usando pilha que "
            "retorna True se os caracteres '()', '[]' e '{}' na string `s` estiverem perfeitamente balanceados, ou False caso contrário."
        ),
        "assertions": [
            "assert parenteses_validos('()[]{}') is True",
            "assert parenteses_validos('([{}])') is True",
            "assert parenteses_validos('(]') is False",
            "assert parenteses_validos('([)]') is False",
            "assert parenteses_validos('(') is False",
        ],
    },
    {
        "id": "C09_sliding_window_unica",
        "name": "09. Sliding Window: Maior Substring Sem Caracteres Repetidos",
        "prompt": (
            "/no_think Escreva em Python apenas a função `maior_substring_unica(s)` (sem comentários) que retorna o "
            "comprimento da maior substring contínua de `s` sem caracteres repetidos."
        ),
        "assertions": [
            "assert maior_substring_unica('abcabcbb') == 3",
            "assert maior_substring_unica('bbbbb') == 1",
            "assert maior_substring_unica('pwwkew') == 3",
            "assert maior_substring_unica('') == 0",
        ],
    },
    {
        "id": "C10_grafo_deteccao_ciclo",
        "name": "10. Grafos: Detecção de Ciclo em Dependências Dirigidas",
        "prompt": (
            "/no_think Escreva em Python apenas a função `pode_concluir_tarefas(n, dependencias)` (sem comentários) "
            "onde `n` é o número de nós (0 a n-1) e `dependencias` é uma lista de pares `[a, b]` (a depende de b). "
            "Retorne True se o grafo dirigido for acíclico (DAG) ou False se houver ciclo."
        ),
        "assertions": [
            "assert pode_concluir_tarefas(2, [[1, 0]]) is True",
            "assert pode_concluir_tarefas(2, [[1, 0], [0, 1]]) is False",
            "assert pode_concluir_tarefas(4, [[1, 0], [2, 1], [3, 2]]) is True",
            "assert pode_concluir_tarefas(3, [[0, 1], [1, 2], [2, 0]]) is False",
        ],
    },
]


def run_coding_duel() -> int:
    contenders = ["8b-rlm", "9b-heretic"]
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "duel": "Engenharia de Código (10 Testes Algorítmicos Verificados por Pytest/AST)",
        "disqualified": "4b-rlm (restrito a triagem simples)",
        "contenders": {},
    }

    for prof_key in contenders:
        spec = GPU_PLUGGABLE_CATALOG[prof_key]
        print("\n" + "=" * 84)
        print(f" [DUELO DE ENGENHARIA DE CÓDIGO - 10 TESTES] MODELO: [{prof_key}] ({spec.model_name})")
        print("=" * 84, flush=True)

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

            for test in CODING_10_TESTS:
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
                        n_predict=220,
                        schema_type="python_func",
                    )
                    last_raw_tps = ff_m.raw_tok_per_s
                    last_eff_tps = ff_m.effective_tok_per_s

                    ver = formal_verifier.verify_python_code(last_code, test["assertions"])
                    if ver.passed:
                        final_passed = True
                        if attempts == 1:
                            first_try_passed = True
                        break

                    if attempts == 1:
                        initial_ce = ver.counterexample
                        current_prompt = (
                            f"{test['prompt']}\n\n"
                            f"Sua tentativa anterior falhou no teste:\n{ver.counterexample}\n"
                            f"Reescreva a função corrigindo o bug (sem comentários)."
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
                    else ("PASS (Reparado 2ª)" if final_passed else "FAIL")
                )
                print(
                    f"    [{prof_key:10s}] {test['name']:58s} | {status_badge:18s} | "
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
                "total_tests": len(CODING_10_TESTS),
                "zero_shot_pct": round((zero_shot_passes / len(CODING_10_TESTS)) * 100.0, 1),
                "final_pass_pct": round((final_passes / len(CODING_10_TESTS)) * 100.0, 1),
                "avg_raw_tok_per_s": avg_raw,
                "avg_effective_tok_per_s": avg_eff,
                "total_time_s": round(total_ms / 1000.0, 2),
                "tests": test_results,
            }
            PROOF_DUEL_PATH.parent.mkdir(parents=True, exist_ok=True)
            PROOF_DUEL_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(
                f" -> [{prof_key} CONCLUÍDO]: De 1ª={zero_shot_passes}/10 ({zero_shot_passes*10}%) | "
                f"Final(c/ Reparo)={final_passes}/10 ({final_passes*10}%) | "
                f"Vel Média={avg_raw} t/s | Tempo Total={total_ms/1000.0:.2f}s",
                flush=True,
            )
        finally:
            harness.stop_gpu_server()

    print("\n" + "=" * 84)
    print(" [PLACAR FINAL DO DUELO DE ENGENHARIA DE CÓDIGO: 8B-RLM vs 9B-HERETIC]")
    print("=" * 84)
    for pk, cdata in report["contenders"].items():
        print(
            f" * [{pk:10s}] Acerto de 1ª: {cdata['zero_shot_passes']:2d}/10 ({cdata['zero_shot_pct']:5.1f}%) | "
            f"Final c/ Reparo: {cdata['final_passes']:2d}/10 ({cdata['final_pass_pct']:5.1f}%) | "
            f"Vel: {cdata['avg_raw_tok_per_s']:5.2f} t/s | Tempo: {cdata['total_time_s']:6.2f}s"
        )
    print("=" * 84, flush=True)
    return 0


if __name__ == "__main__":
    if "--audit-only" in sys.argv and PROOF_DUEL_PATH.exists():
        data = json.loads(PROOF_DUEL_PATH.read_text(encoding="utf-8"))
        assert set(data.get("contenders", {}).keys()) == {"8b-rlm", "9b-heretic"}
        assert len(data["contenders"]["8b-rlm"]["tests"]) == 10
        assert len(data["contenders"]["9b-heretic"]["tests"]) == 10
        print("[OK] Prova do duelo 8b-rlm vs 9b-heretic (10 testes de código) validada com sucesso!")
        sys.exit(0)
    sys.exit(run_coding_duel())
