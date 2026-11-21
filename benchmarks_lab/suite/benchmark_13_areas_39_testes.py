# -*- coding: utf-8 -*-
"""
GRANDE BENCHMARK MULTIDIMENSIONAL OMEGA: 13 ÁREAS COGNITIVAS x 3 TESTES = 39 TESTES POR MODELO
(117 Execuções Físicas na GPU AMD Radeon RX 580 8GB Vulkan)

Modelos Plugados Comparados:
  1. 4b-rlm     (Qwen3-4B-Instruct-2507-RLM-SFT-v3-Q4_K_M | 2.33 GB VRAM)
  2. 8b-rlm     (rlm-qwen3-8b-v0.1-Q4_K_M                 | 4.68 GB VRAM)
  3. 9b-heretic (Qwen3.8-9B-Heretic-IQ4_XS                | 4.99 GB VRAM)

Arquiteto & Líder: Mestre Ruan
Protocolo O.M.E.G.A. & Radical Truth Protocol
"""

from __future__ import annotations

import json
import re
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Callable

ROTOR_ROOT = Path(r"F:\rotor-llm")
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))

from router.formal_verifier import formal_verifier
from router.heterogeneous_rlm_harness import (
    GPU_PLUGGABLE_CATALOG,
    HeterogeneousRLMHarness,
)

PROOF_OUT = Path(r"F:\data\proof_benchmark_13_areas_39_testes.json")


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s.lower().strip()


# ==============================================================================
# DEFINIÇÃO DOS 39 TESTES (13 ÁREAS x 3 TESTES CADA) COM VERIFICAÇÃO ESTRITA
# ==============================================================================

BENCHMARK_SUITE: list[dict[str, Any]] = [
    # 01. Reflexo / Triagem
    {
        "area_id": "01_reflexo_triagem",
        "area_name": "01. Reflexo / Triagem (Intenção e despacho ágil)",
        "tests": [
            {
                "id": "T01_1",
                "name": "Classificação de Emergência Infra",
                "prompt": "/no_think Classifique o alerta 'O banco PostgreSQL parou por disco cheio' escolhendo APENAS UMA etiqueta entre: INFRA_EMERGENCY, CHITCHAT, MATH. Responda somente a etiqueta.",
                "n_predict": 24,
                "verify": lambda out: "infra_emergency" in _norm(out),
            },
            {
                "id": "T01_2",
                "name": "Despacho de Tier por Complexidade",
                "prompt": '/no_think Para a tarefa "Prove o Teorema de Incompletude e implemente o verificador formal", escolha o tier em JSON exato {"tier": 2} (Tier 2 Pesado) ou {"tier": 0} (Trivial). Responda apenas o JSON.',
                "n_predict": 24,
                "verify": lambda out: '"tier": 2' in out or '"tier":2' in out or "2" in out,
            },
            {
                "id": "T01_3",
                "name": "Extração Léxica Rápida",
                "prompt": '/no_think Extraia o valor numérico e a conta da frase "Transferir 450 para conta 9981" no formato exato 450|9981. Responda apenas os números separados por barra vertical.',
                "n_predict": 24,
                "verify": lambda out: "450" in out and "9981" in out,
            },
        ],
    },
    # 02. Engenharia de Código
    {
        "area_id": "02_engenharia_codigo",
        "area_name": "02. Engenharia de Código (Código, Refactor, Patches)",
        "tests": [
            {
                "id": "T02_1",
                "name": "Busca Binária Exata",
                "prompt": "/no_think Escreva em Python apenas a função `busca_binaria(arr, x)` (sem comentários) que retorna o índice de `x` na lista ordenada `arr` ou -1 se não existir.",
                "n_predict": 160,
                "schema_type": "python_func",
                "verify": lambda out: formal_verifier.verify_python_code(
                    out,
                    [
                        "assert busca_binaria([1, 3, 5, 7, 9], 7) == 3",
                        "assert busca_binaria([1, 3, 5], 4) == -1",
                    ],
                ).passed,
            },
            {
                "id": "T02_2",
                "name": "Patch de Palíndromo Normalizado",
                "prompt": "/no_think Escreva em Python apenas a função `eh_palindromo(s)` (sem comentários) que retorna True se a string `s` for palíndromo ignorando espaços e maiúsculas/minúsculas, ou False caso contrário.",
                "n_predict": 160,
                "schema_type": "python_func",
                "verify": lambda out: formal_verifier.verify_python_code(
                    out,
                    [
                        "assert eh_palindromo('Ame a ema') is True",
                        "assert eh_palindromo('rotor') is True",
                        "assert eh_palindromo('python') is False",
                    ],
                ).passed,
            },
            {
                "id": "T02_3",
                "name": "Programação Dinâmica (Maior Soma Não-Adjacente)",
                "prompt": "/no_think Escreva em Python apenas a função `max_nao_adj(nums)` (sem comentários) que retorna a maior soma de elementos não-adjacentes da lista `nums` (para [] retorna 0, para [2, 1, 1, 2] retorna 4).",
                "n_predict": 160,
                "schema_type": "python_func",
                "verify": lambda out: formal_verifier.verify_python_code(
                    out,
                    [
                        "assert max_nao_adj([]) == 0",
                        "assert max_nao_adj([2, 7, 9, 3, 1]) == 12",
                        "assert max_nao_adj([2, 1, 1, 2]) == 4",
                    ],
                ).passed,
            },
        ],
    },
    # 03. Matemática & Provas
    {
        "area_id": "03_matematica_provas",
        "area_name": "03. Matemática & Provas (Raciocínio formal e cálculo)",
        "tests": [
            {
                "id": "T03_1",
                "name": "Expansão Polinomial Simbólica (SymPy)",
                "prompt": "/no_think Expanda algebricamente (2*x - 3)**2 em polinômio simplificado em x. Responda apenas a expressão no JSON.",
                "n_predict": 48,
                "schema_type": "concise_json",
                "verify": lambda out: formal_verifier.verify_math_equivalence(out, "4*x**2 - 12*x + 9").passed,
            },
            {
                "id": "T03_2",
                "name": "Derivada Simbólica (SymPy)",
                "prompt": "/no_think Calcule a derivada primeira em relação a x da função f(x) = x**3 - 5*x**2 + 6*x - 2. Responda apenas a expressão derivada no JSON.",
                "n_predict": 48,
                "schema_type": "concise_json",
                "verify": lambda out: formal_verifier.verify_math_equivalence(out, "3*x**2 - 10*x + 6").passed,
            },
            {
                "id": "T03_3",
                "name": "Sistema de Restrições Inteira (Z3 SMT)",
                "prompt": '/no_think Encontre inteiros x e y tais que x + y == 30 e 2*x - y == 15. Responda apenas no JSON {"solution":{"x": valor, "y": valor}}.',
                "n_predict": 36,
                "schema_type": "z3_xy",
                "verify": lambda out: formal_verifier.verify_z3_constraints(
                    out, ["x + y == 30", "2*x - y == 15"]
                ).passed,
            },
        ],
    },
    # 04. Automação de SO / RPA
    {
        "area_id": "04_automacao_so_rpa",
        "area_name": "04. Automação de SO / RPA (Desktop, telas, janelas)",
        "tests": [
            {
                "id": "T04_1",
                "name": "Seleção de Coordenada OCR Closed-Loop",
                "prompt": '/no_think O OCR da tela detectou: [{"text":"Salvar","x":420,"y":310},{"text":"Cancelar","x":520,"y":310}]. Qual o par x,y exato para clicar em Salvar? Responda apenas 420,310.',
                "n_predict": 24,
                "verify": lambda out: "420" in out and "310" in out,
            },
            {
                "id": "T04_2",
                "name": "Prevenção de Clique Cego (Zero Open-Loop)",
                "prompt": '/no_think Precisamos clicar no botão "Confirmar", mas o OCR atual da tela só mostra [{"text":"Carregando..."}]. Pela regra de Tolerância Zero a RPA Cego, escolha APENAS UMA ação: WAIT_AND_RESCAN ou BLIND_CLICK.',
                "n_predict": 24,
                "verify": lambda out: "wait_and_rescan" in _norm(out),
            },
            {
                "id": "T04_3",
                "name": "Cmdlet Nativo PowerShell de Processos",
                "prompt": "/no_think Qual é o nome exato do cmdlet nativo do PowerShell (Verbo-Substantivo) usado para listar os processos em execução no Windows? Responda apenas o cmdlet.",
                "n_predict": 24,
                "verify": lambda out: "get-process" in _norm(out),
            },
        ],
    },
    # 05. Memória Perene
    {
        "area_id": "05_memoria_perene",
        "area_name": "05. Memória Perene (Conhecimento contínuo e Grafo)",
        "tests": [
            {
                "id": "T05_1",
                "name": "Extração de Tripla para Grafo HippoRAG",
                "prompt": '/no_think Extraia a tripla da frase "O Xeon E5-2697 v3 possui arquitetura Haswell-EP" em formato JSON contendo "Xeon E5-2697 v3" e "Haswell-EP". Responda apenas o JSON.',
                "n_predict": 48,
                "verify": lambda out: "xeon" in _norm(out) and "haswell" in _norm(out),
            },
            {
                "id": "T05_2",
                "name": "Resolução de Conflito Temporal (KAIROS)",
                "prompt": "/no_think Memória t=1: 'A porta ativa do servidor é 8080'. Memória t=2 (mais recente): 'A porta ativa foi migrada para 8083'. Qual é o número da porta ativa atual? Responda apenas o número.",
                "n_predict": 24,
                "verify": lambda out: "8083" in out and "8080" not in out.strip()[:6],
            },
            {
                "id": "T05_3",
                "name": "Deduplicação de Fatos Redundantes",
                "prompt": "/no_think Temos 3 registros: (1) 'A RX 580 tem 8GB de VRAM', (2) 'O chip é Polaris 20', (3) 'A memória de vídeo da RX 580 é de 8GB'. Após deduplicar sinônimos, quantos fatos distintos restam? Responda apenas o número inteiro.",
                "n_predict": 20,
                "verify": lambda out: re.search(r"\b2\b", out) is not None,
            },
        ],
    },
    # 06. Metacognição
    {
        "area_id": "06_metacognicao",
        "area_name": "06. Metacognição (Auto-correção e estabilidade LTI)",
        "tests": [
            {
                "id": "T06_1",
                "name": "Detecção de Premissa Contraditória",
                "prompt": "/no_think Um problema pede: 'Encontre um número inteiro que seja simultaneamente par e ímpar'. Essa tarefa tem solução numérica ou é IMPOSSIVEL por contradição lógica? Responda apenas IMPOSSIVEL se for contraditória.",
                "n_predict": 24,
                "verify": lambda out: any(k in _norm(out) for k in ("impossivel", "contradic", "nao existe")),
            },
            {
                "id": "T06_2",
                "name": "Auto-Correção de Alucinação Numérica",
                "prompt": "/no_think Um rascunho anterior afirmou erroneamente que 2 elevado a 10 (2**10) é 1000. Corrija o erro e responda apenas o valor inteiro exato de 2**10.",
                "n_predict": 24,
                "verify": lambda out: "1024" in out,
            },
            {
                "id": "T06_3",
                "name": "Critério de Estabilidade LTI Discreta",
                "prompt": "/no_think Para um sistema dinâmico linear discreto h_{t+1} = A * h_t convergir de forma assintoticamente estável sem explodir, o raio espectral rho(A) deve ser MENOR_QUE_1 ou MAIOR_QUE_1? Responda apenas uma das opções.",
                "n_predict": 24,
                "verify": lambda out: "menor" in _norm(out) or "< 1" in out or "<1" in out,
            },
        ],
    },
    # 07. Cadinho Red-Team
    {
        "area_id": "07_cadinho_redteam",
        "area_name": "07. Cadinho Red-Team (Fuzzing, segurança e auditoria)",
        "tests": [
            {
                "id": "T07_1",
                "name": "Auditoria de SQL Injection",
                "prompt": "/no_think Qual vulnerabilidade clássica existe na linha Python `cursor.execute(f\"SELECT * FROM users WHERE user = '{nome}'\")`? Responda apenas SQL_INJECTION ou BUFFER_OVERFLOW.",
                "n_predict": 24,
                "verify": lambda out: "sql" in _norm(out),
            },
            {
                "id": "T07_2",
                "name": "Detecção de RCE via eval()",
                "prompt": "/no_think Receber uma string JSON da internet e passá-la diretamente para `eval(payload)` em Python causa risco crítico de Execução Remota de Código (RCE). Qual função segura da biblioteca padrão `json` deve substituir `eval`? Responda apenas o nome da função.",
                "n_predict": 24,
                "verify": lambda out: "loads" in _norm(out),
            },
            {
                "id": "T07_3",
                "name": "Classificação de Path Traversal",
                "prompt": "/no_think Um fuzzer envia o parâmetro `arquivo=../../../../Windows/win.ini` para uma rota de leitura. Esse vetor de ataque é PATH_TRAVERSAL ou CSRF? Responda apenas o nome do ataque.",
                "n_predict": 24,
                "verify": lambda out: "path_traversal" in _norm(out) or "traversal" in _norm(out),
            },
        ],
    },
    # 08. Síntese Vocal
    {
        "area_id": "08_sintese_vocal",
        "area_name": "08. Síntese Vocal (Normalização fonética e prosódia TTS)",
        "tests": [
            {
                "id": "T08_1",
                "name": "Expansão Monetária para TTS",
                "prompt": "/no_think Converta o valor 'R$ 15,50' para texto escrito integralmente por extenso em português para leitura por sintetizador de voz. Responda apenas o texto por extenso.",
                "n_predict": 36,
                "verify": lambda out: "quinze reais" in _norm(out) and "cinquenta centavos" in _norm(out),
            },
            {
                "id": "T08_2",
                "name": "Expansão de Unidade Física para TTS",
                "prompt": "/no_think Escreva '100 km/h' totalmente por extenso em português para leitura natural em voz alta. Responda apenas a frase por extenso.",
                "n_predict": 32,
                "verify": lambda out: "cem quilometros por hora" in _norm(out),
            },
            {
                "id": "T08_3",
                "name": "Inserção de Tag SSML de Pausa",
                "prompt": '/no_think Insira a tag SSML `<break time="500ms"/>` exatamente entre as palavras "Concluído." e "Iniciando" na frase "Concluído. Iniciando". Responda apenas a frase resultante.',
                "n_predict": 36,
                "verify": lambda out: "<break" in _norm(out) and "500ms" in _norm(out),
            },
        ],
    },
    # 09. Multimodal & Visão
    {
        "area_id": "09_multimodal_visao",
        "area_name": "09. Multimodal & Visão (Geometria de tela, SVG, OCR)",
        "tests": [
            {
                "id": "T09_1",
                "name": "Cálculo de Área de Interseção (Bounding Boxes)",
                "prompt": "/no_think Duas janelas na tela têm coordenadas [x1, y1, x2, y2]: Janela A = [0, 0, 100, 100] e Janela B = [50, 50, 150, 150]. A interseção é o quadrado [50, 50, 100, 100] de lado 50x50. Qual é a área numérica dessa interseção? Responda apenas o número.",
                "n_predict": 24,
                "verify": lambda out: "2500" in out.replace(".", "").replace(",", ""),
            },
            {
                "id": "T09_2",
                "name": "Inspeção Geométrica de Código SVG",
                "prompt": '/no_think Analise o elemento `<svg><circle cx="100" cy="100" r="40" fill="blue"/></svg>`. Sabendo que o raio r é 40, qual é o valor numérico do diâmetro (2 * r) desse círculo? Responda apenas o número.',
                "n_predict": 24,
                "verify": lambda out: re.search(r"\b80\b", out) is not None,
            },
            {
                "id": "T09_3",
                "name": "Restauração de Texto OCR com Ruído Leetspeak",
                "prompt": "/no_think Restaure o texto corrompido por OCR 'O s1st3m4 f0i v4l1d4d0' para o português correto. Responda apenas a frase limpa.",
                "n_predict": 28,
                "verify": lambda out: "o sistema foi validado" in _norm(out),
            },
        ],
    },
    # 10. Planejamento Deliberativo
    {
        "area_id": "10_planejamento_deliberativo",
        "area_name": "10. Planejamento Deliberativo (Planos encadeados e PDDL)",
        "tests": [
            {
                "id": "T10_1",
                "name": "Ordenação Topológica de Dependências",
                "prompt": "/no_think Temos 3 etapas: [A: Compilar DLL (exige B pronta)], [B: Escrever código C++ (sem dependências)], [C: Rodar teste Python (exige A pronta)]. Qual a ordem correta de execução? Responda apenas B->A->C.",
                "n_predict": 24,
                "verify": lambda out: re.search(r"b\s*(?:->|,|>|-|\s)\s*a\s*(?:->|,|>|-|\s)\s*c", _norm(out)) is not None,
            },
            {
                "id": "T10_2",
                "name": "Sequenciamento Causal PDDL",
                "prompt": "/no_think Para ler um arquivo dentro de um disco criptografado desmontado, ordene os passos 1 (Ler arquivo), 2 (Desbloquear criptografia), 3 (Conectar disco físico) na sequência lógica correta. Responda apenas 3->2->1.",
                "n_predict": 24,
                "verify": lambda out: re.search(r"3\s*(?:->|,|>|-|\s)\s*2\s*(?:->|,|>|-|\s)\s*1", _norm(out)) is not None,
            },
            {
                "id": "T10_3",
                "name": "Diagnóstico Formal de Deadlock",
                "prompt": "/no_think O Processo A segura o Lock 1 e aguarda o Lock 2; simultaneamente, o Processo B segura o Lock 2 e aguarda o Lock 1. Como é chamado esse travamento circular em sistemas operacionais? Responda apenas DEADLOCK ou RACE_CONDITION.",
                "n_predict": 24,
                "verify": lambda out: "deadlock" in _norm(out),
            },
        ],
    },
    # 11. Raciocínio Científico
    {
        "area_id": "11_raciocinio_cientifico",
        "area_name": "11. Raciocínio Científico (Física, Química, Engenharia)",
        "tests": [
            {
                "id": "T11_1",
                "name": "Física: Dissipação de Potência (P = I^2 * R)",
                "prompt": "/no_think Um resistor de R = 10 Ohms é percorrido por uma corrente elétrica de I = 3 Amperes. Pela fórmula P = (I**2) * R, qual a potência dissipada em Watts? Responda apenas o número.",
                "n_predict": 24,
                "verify": lambda out: re.search(r"\b90\b", out) is not None,
            },
            {
                "id": "T11_2",
                "name": "Química: Balanceamento Estequiométrico",
                "prompt": "/no_think Na reação balanceada de combustão do metano: CH4 + 2 O2 -> CO2 + 2 H2O, a queima completa de 3 mols de CH4 produz quantos mols de água (H2O)? Responda apenas o número inteiro.",
                "n_predict": 24,
                "verify": lambda out: re.search(r"\b6\b", out) is not None,
            },
            {
                "id": "T11_3",
                "name": "Engenharia: Teto de Largura de Banda (Roofline)",
                "prompt": "/no_think Se um modelo lê 4 GB de pesos por token gerado e a memória entrega 80 GB/s de largura de banda efetiva, qual é a velocidade máxima teórica em tokens por segundo (80 / 4)? Responda apenas o número.",
                "n_predict": 24,
                "verify": lambda out: re.search(r"\b20\b", out) is not None,
            },
        ],
    },
    # 12. Linguagem & Discurso
    {
        "area_id": "12_linguagem_discurso",
        "area_name": "12. Linguagem & Discurso (Coerência, síntese e lógica verbal)",
        "tests": [
            {
                "id": "T12_1",
                "name": "Compressão Densa de Telemetria",
                "prompt": "/no_think Comprima a frase 'O processador Xeon finalizou o benchmark atingindo a marca de 10.94 tokens por segundo' em no máximo 5 palavras mantendo o número 10.94. Responda apenas a frase curta.",
                "n_predict": 24,
                "verify": lambda out: ("10.94" in out or "10,94" in out) and len(out.strip().split()) <= 8,
            },
            {
                "id": "T12_2",
                "name": "Dedução Silogística Estrita",
                "prompt": "/no_think Premissa 1: Todos os shaders Polaris 20 executam em frentes de onda Wave64. Premissa 2: O kernel Q4_K_M é um shader Polaris 20. Conclusão lógica: o kernel Q4_K_M executa em Wave32 ou Wave64? Responda apenas Wave64 ou Wave32.",
                "n_predict": 24,
                "verify": lambda out: "wave64" in _norm(out),
            },
            {
                "id": "T12_3",
                "name": "Resolução Correferencial (Anáfora)",
                "prompt": "/no_think Na frase 'O módulo descartou a hipótese porque ela violou a restrição Z3', o pronome 'ela' refere-se a 'módulo' ou a 'hipótese'? Responda apenas a palavra correta.",
                "n_predict": 24,
                "verify": lambda out: "hipotese" in _norm(out),
            },
        ],
    },
    # 13. Governador de Hardware
    {
        "area_id": "13_governador_hardware",
        "area_name": "13. Governador de Hardware (Clocks, temperaturas e VRAM)",
        "tests": [
            {
                "id": "T13_1",
                "name": "Prevenção de OOM em VRAM (Circuit Breaker)",
                "prompt": "/no_think A placa de vídeo possui 7.4 GB de VRAM útil. Uma requisição tenta alocar um modelo de 6.0 GB mais 2.5 GB de KV-Cache (total 8.5 GB > 7.4 GB). O Governador deve responder ALLOW ou REJECT_OOM? Responda apenas uma opção.",
                "n_predict": 24,
                "verify": lambda out: "reject" in _norm(out) or "oom" in _norm(out),
            },
            {
                "id": "T13_2",
                "name": "Proteção Térmica (Hardware Watchdog)",
                "prompt": "/no_think A temperatura do silício da GPU atingiu 90°C (acima do teto seguro de 85°C). Qual política o Watchdog deve aplicar imediatamente: THROTTLE_AND_COOL ou OVERCLOCK_BOOST? Responda apenas a política correta.",
                "n_predict": 24,
                "verify": lambda out: "throttle" in _norm(out) or "cool" in _norm(out),
            },
            {
                "id": "T13_3",
                "name": "Escalonamento de Núcleos Físicos AVX2",
                "prompt": "/no_think Para evitar contenção de registradores SIMD AVX2 entre threads virtuais (HyperThreading) no Xeon Haswell, devemos fixar a afinidade apenas nos NUCLEOS_FISICOS ou em TODOS_THREADS_VIRTUAIS? Responda apenas a opção correta.",
                "n_predict": 24,
                "verify": lambda out: "fisicos" in _norm(out) or "nucleos_fisicos" in _norm(out),
            },
        ],
    },
]


def run_full_13_areas_benchmark() -> int:
    profiles = ["4b-rlm", "8b-rlm", "9b-heretic"]
    full_report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_areas": 13,
        "tests_per_area": 3,
        "total_tests_per_model": 39,
        "total_hardware_executions": 117,
        "models": {},
    }

    for prof_key in profiles:
        spec = GPU_PLUGGABLE_CATALOG[prof_key]
        print("\n" + "=" * 82)
        print(f" [INICIANDO BATERIA DE 39 TESTES] MODELO: [{prof_key}] ({spec.model_name} | {spec.vram_size_gb} GB)")
        print("=" * 82, flush=True)

        harness = HeterogeneousRLMHarness(gpu_profile=prof_key, gpu_port=8081, max_repair_turns=0)
        try:
            boot_info = harness.start_pluggable_gpu_server(prof_key, timeout_s=75.0)
            print(f" -> [GPU ONLINE] Boot concluído em {boot_info['load_time_s']}s na RX 580 Vulkan.", flush=True)

            model_areas: dict[str, Any] = {}
            total_passed = 0
            total_tests = 0
            total_raw_tps_list: list[float] = []
            total_eff_tps_list: list[float] = []
            total_latency_ms = 0.0

            for area in BENCHMARK_SUITE:
                area_id = area["area_id"]
                area_name = area["area_name"]
                area_passed = 0
                area_lat_ms = 0.0
                area_tps_list: list[float] = []
                test_records: list[dict[str, Any]] = []

                for t in area["tests"]:
                    t0 = time.perf_counter()
                    schema_type = t.get("schema_type", None)
                    try:
                        out_text, ff_m = harness.query_completion(
                            prompt=t["prompt"],
                            port=8081,
                            n_predict=t.get("n_predict", 32),
                            schema_type=schema_type,
                        )
                        passed = bool(t["verify"](out_text))
                        raw_tps = ff_m.raw_tok_per_s
                        eff_tps = ff_m.effective_tok_per_s
                    except Exception as e:
                        out_text = f"ERROR: {e}"
                        passed = False
                        raw_tps = 0.0
                        eff_tps = 0.0

                    lat_ms = round((time.perf_counter() - t0) * 1000.0, 2)
                    total_tests += 1
                    if passed:
                        total_passed += 1
                        area_passed += 1
                    area_lat_ms += lat_ms
                    total_latency_ms += lat_ms
                    if raw_tps > 0:
                        area_tps_list.append(raw_tps)
                        total_raw_tps_list.append(raw_tps)
                        total_eff_tps_list.append(eff_tps)

                    test_records.append(
                        {
                            "test_id": t["id"],
                            "test_name": t["name"],
                            "passed": passed,
                            "raw_tok_per_s": raw_tps,
                            "effective_tok_per_s": eff_tps,
                            "latency_ms": lat_ms,
                            "output_preview": out_text[:160],
                        }
                    )

                avg_area_tps = round(sum(area_tps_list) / max(1, len(area_tps_list)), 2)
                model_areas[area_id] = {
                    "area_name": area_name,
                    "score": f"{area_passed}/3",
                    "passed_count": area_passed,
                    "avg_tok_per_s": avg_area_tps,
                    "area_latency_ms": round(area_lat_ms, 2),
                    "tests": test_records,
                }
                print(
                    f"    [{prof_key:10s}] {area_name:58s} | Nota: {area_passed}/3 | "
                    f"Vel: {avg_area_tps:5.2f} t/s | Tempo: {area_lat_ms:6.1f} ms",
                    flush=True,
                )

            overall_raw_tps = round(sum(total_raw_tps_list) / max(1, len(total_raw_tps_list)), 2)
            overall_eff_tps = round(sum(total_eff_tps_list) / max(1, len(total_eff_tps_list)), 2)
            pass_pct = round((total_passed / max(1, total_tests)) * 100.0, 2)

            full_report["models"][prof_key] = {
                "boot_info": boot_info,
                "total_passed": total_passed,
                "total_tests": total_tests,
                "accuracy_pct": pass_pct,
                "avg_raw_tok_per_s": overall_raw_tps,
                "avg_effective_tok_per_s": overall_eff_tps,
                "total_suite_latency_s": round(total_latency_ms / 1000.0, 2),
                "areas": model_areas,
            }

            # Salva incrementalmente a cada modelo concluído
            PROOF_OUT.parent.mkdir(parents=True, exist_ok=True)
            PROOF_OUT.write_text(json.dumps(full_report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(
                f" -> [MODELO {prof_key} FINALIZADO]: {total_passed}/39 ({pass_pct}%) | "
                f"Vel Média: {overall_raw_tps} t/s | Tempo Total: {total_latency_ms/1000.0:.2f}s",
                flush=True,
            )
        finally:
            harness.stop_gpu_server()

    print("\n" + "=" * 82)
    print(" [PLACAR GERAL FINAL DAS 13 ÁREAS (39 TESTES POR MODELO)]")
    print("=" * 82)
    for pk, mdata in full_report["models"].items():
        print(
            f" * [{pk:10s}] Aprovação: {mdata['total_passed']:2d}/39 ({mdata['accuracy_pct']:5.1f}%) | "
            f"Vel. Média: {mdata['avg_raw_tok_per_s']:5.2f} t/s | "
            f"Tempo Total: {mdata['total_suite_latency_s']:6.2f}s"
        )
    print("=" * 82, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_full_13_areas_benchmark())
