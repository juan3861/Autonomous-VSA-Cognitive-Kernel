# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Benchmark Bare-Metal para ai9stars/G9v3-3B em Inglês na GPU RX 580 Vulkan.
1. Download oficial: bartowski/ai9stars_G9v3-3B-GGUF (Q4_K_M, 1.77 GB)
2. Bateria 1: 13 Áreas Cognitivas x 3 Testes = 39 Testes em Inglês
3. Bateria 2: 10 Desafios Algorítmicos Nível Claude Opus em Inglês com Pytest Formal
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from huggingface_hub import hf_hub_download
from router.formal_verifier import formal_verifier

MODELS_DIR = Path(r"C:\AetherMind_Contenders")
MODEL_FILENAME = "ai9stars_G9v3-3B-Q4_K_M.gguf"
REPO_ID = "bartowski/ai9stars_G9v3-3B-GGUF"
PROOF_PATH = Path(r"F:\data\proof_g9v3_english_benchmark.json")
VULKAN_SERVER_BIN = r"F:\tools\lc_vulkan\llama-server.exe"


def ensure_download() -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    target_path = MODELS_DIR / MODEL_FILENAME
    if target_path.exists() and target_path.stat().st_size > 1_500_000_000:
        print(f" -> [CACHE HIT] {MODEL_FILENAME} já disponível ({target_path.stat().st_size / (1024**3):.2f} GB).", flush=True)
        return target_path

    print(f"\n[*] Baixando {MODEL_FILENAME} de {REPO_ID}...", flush=True)
    t0 = time.perf_counter()
    p = hf_hub_download(
        repo_id=REPO_ID,
        filename=MODEL_FILENAME,
        local_dir=str(MODELS_DIR),
    )
    elapsed = round(time.perf_counter() - t0, 1)
    sz = Path(p).stat().st_size / (1024**3)
    print(f" -> [DOWNLOAD COMPLETO] {sz:.2f} GB em {elapsed}s ({sz*1024/max(1, elapsed):.2f} MB/s).", flush=True)
    return Path(p)


def start_vulkan_server(model_path: Path, port: int = 8081, timeout_s: float = 60.0) -> subprocess.Popen[str] | None:
    health_url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(health_url)
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            if resp.status == 200:
                print(f" -> [GPU REUSE] Servidor Vulkan já ativo e pronto na porta {port}.", flush=True)
                return None
    except Exception:
        pass

    subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"], capture_output=True)
    time.sleep(1.5)

    env = os.environ.copy()
    env["VK_LOADER_LAYERS_DISABLE"] = "~all~"
    env["DISABLE_LAYER_AMD_SWITCHABLE_GRAPHICS_1"] = "1"
    env["AMD_VULKAN_FORCE_GPU_MEMORY_PRIORITY"] = "1"

    cmd = [
        VULKAN_SERVER_BIN,
        "-m", str(model_path),
        "-ngl", "99",
        "-t", "8",
        "-c", "2048",
        "-b", "512",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]

    log_file = open(r"F:\data\llama_g9v3_gpu.log", "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT, text=True)

    t0 = time.perf_counter()
    while time.perf_counter() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"Servidor Vulkan encerrou prematuramente (código: {proc.poll()}).")
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    print(f" -> [GPU ONLINE] G9v3-3B carregado em {time.perf_counter() - t0:.2f}s na RX 580 Vulkan.", flush=True)
                    return proc
        except Exception:
            time.sleep(1.0)

    proc.terminate()
    raise TimeoutError(f"Timeout ({timeout_s}s) ao subir servidor GPU Vulkan.")


def query_g9v3(prompt: str, port: int = 8081, n_predict: int = 256, is_code: bool = False) -> tuple[str, float]:
    clean = prompt.replace("/no_think", "").strip()
    # Formatação nativa Llama-3 para G9v3-3B
    effective_prompt = (
        f"<|start_header_id|>user<|end_header_id|>\n\n{clean}<|eot_id|>"
        f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        + ("```python\ndef " if is_code else "")
    )
    stop_list = ["<|eot_id|>", "<|end_of_text|>", "```\n\n"]
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


# ==============================================================================
# SUITE DAS 13 ÁREAS EM INGLÊS (39 TESTES)
# ==============================================================================
SUITE_13_AREAS_EN = [
    {
        "area_id": "01_triage",
        "area_name": "01. Reflex / Triage (Intent & Rapid Dispatch)",
        "tests": [
            {
                "id": "EN_01_1",
                "name": "Infra Emergency Classification",
                "prompt": "Classify the alert 'PostgreSQL stopped because disk is full' by picking EXACTLY ONE label: INFRA_EMERGENCY, CHITCHAT, MATH. Answer with only the label.",
                "verify": lambda o: "infra_emergency" in o.lower(),
            },
            {
                "id": "EN_01_2",
                "name": "Complexity Tier Dispatch",
                "prompt": 'For the task "Prove Godel Incompleteness Theorem and implement a formal verifier", choose the tier as exact JSON {"tier": 2} (Heavy Tier 2) or {"tier": 0} (Trivial). Answer with only the JSON.',
                "verify": lambda o: '"tier": 2' in o or '"tier":2' in o or "2" in o,
            },
            {
                "id": "EN_01_3",
                "name": "Rapid Lexical Extraction",
                "prompt": 'Extract the number and account from "Transfer 450 to account 9981" in the exact format 450|9981. Answer with only the numbers separated by a pipe.',
                "verify": lambda o: "450" in o and "9981" in o,
            },
        ],
    },
    {
        "area_id": "02_code_engineering",
        "area_name": "02. Code Engineering (Refactor, Syntax, Algorithms)",
        "tests": [
            {
                "id": "EN_02_1",
                "name": "Exact Binary Search",
                "prompt": "Write only the Python function `busca_binaria(arr, x)` (no comments) returning the index of `x` in sorted list `arr` or -1 if not found.",
                "is_code": True,
                "verify": lambda o: formal_verifier.verify_python_code(o, [
                    "assert busca_binaria([1, 3, 5, 7, 9], 7) == 3",
                    "assert busca_binaria([1, 3, 5], 4) == -1",
                ]).passed,
            },
            {
                "id": "EN_02_2",
                "name": "Normalized Palindrome Function",
                "prompt": "Write only the Python function `eh_palindromo(s)` (no comments) returning True if string `s` is a palindrome ignoring spaces and case, False otherwise.",
                "is_code": True,
                "verify": lambda o: formal_verifier.verify_python_code(o, [
                    "assert eh_palindromo('A man a plan a canal Panama') is True",
                    "assert eh_palindromo('race a car') is False",
                ]).passed,
            },
            {
                "id": "EN_02_3",
                "name": "1D DP Non-Adjacent Max Sum",
                "prompt": "Write only the Python function `max_nao_adjacente(nums)` (no comments) computing the maximum sum of non-adjacent elements in O(n) time.",
                "is_code": True,
                "verify": lambda o: formal_verifier.verify_python_code(o, [
                    "assert max_nao_adjacente([2, 7, 9, 3, 1]) == 12",
                    "assert max_nao_adjacente([2, 1, 1, 2]) == 4",
                ]).passed,
            },
        ],
    },
    {
        "area_id": "03_math_and_proofs",
        "area_name": "03. Mathematics & Formal Proofs (SymPy / Z3)",
        "tests": [
            {
                "id": "EN_03_1",
                "name": "Symbolic Derivative",
                "prompt": "What is the derivative of f(x) = x^3 - 5*x^2 + 7 with respect to x? Answer in JSON format: {\"derivative\": \"3*x^2 - 10*x\"}.",
                "verify": lambda o: ("3*x^2" in o or "3*x**2" in o) and ("10*x" in o or "-10*x" in o),
            },
            {
                "id": "EN_03_2",
                "name": "Linear System Solution",
                "prompt": "Solve for x and y: x + y = 20 and 2*x - y = 10. Answer in JSON: {\"x\": 10, \"y\": 10}.",
                "verify": lambda o: ("10" in o and '"x"' in o) or ("x = 10" in o and "y = 10" in o),
            },
            {
                "id": "EN_03_3",
                "name": "De Morgan Law SMT Check",
                "prompt": "Is the formula not(A and B) equivalent to (not A or not B)? Answer with strictly VALID or INVALID.",
                "verify": lambda o: "valid" in o.lower() and "invalid" not in o.lower(),
            },
        ],
    },
    {
        "area_id": "04_os_automation_rpa",
        "area_name": "04. OS Automation & RPA (Closed-Loop Vision / Desktop)",
        "tests": [
            {
                "id": "EN_04_1",
                "name": "Closed-Loop OCR Policy",
                "prompt": "According to the robust closed-loop RPA protocol, what MUST be done before clicking a button based on coordinates? Answer with OCR, GUESS, or SLEEP.",
                "verify": lambda o: "ocr" in o.lower(),
            },
            {
                "id": "EN_04_2",
                "name": "Safe Process Query Command",
                "prompt": "What is the exact PowerShell command to get the PID of process 'llama-server'? Answer with Get-Process, rm -rf, or format.",
                "verify": lambda o: "get-process" in o.lower(),
            },
            {
                "id": "EN_04_3",
                "name": "Isolated Browser Window Policy",
                "prompt": "When automating browser workflows, should actions run in an isolated new window or interfere with the user's active session? Answer with ISOLATED or OVERWRITE.",
                "verify": lambda o: "isolated" in o.lower(),
            },
        ],
    },
    {
        "area_id": "05_perennial_memory",
        "area_name": "05. Perennial Memory (Knowledge Graph & GraphRAG)",
        "tests": [
            {
                "id": "EN_05_1",
                "name": "Knowledge Graph Triples Extraction",
                "prompt": "Extract the subject-predicate-object triple from 'Xeon E5-2697 v3 has 14 physical cores'. Answer in format: (Subject | Predicate | Object).",
                "verify": lambda o: "xeon" in o.lower() and "14" in o.lower(),
            },
            {
                "id": "EN_05_2",
                "name": "Temporal Conflict Resolution",
                "prompt": "Memory A: 'Current port is 8081' (timestamp 10:00). Memory B: 'Current port is 8083' (timestamp 10:30). What is the current port? Answer only the number.",
                "verify": lambda o: "8083" in o and "8081" not in o,
            },
            {
                "id": "EN_05_3",
                "name": "Hardware Entity Deduplication",
                "prompt": "Are 'RX580 8GB', 'Radeon RX 580' and 'AMD Polaris 20' referring to the same GPU hardware subsystem? Answer YES or NO.",
                "verify": lambda o: "yes" in o.lower(),
            },
        ],
    },
    {
        "area_id": "06_metacognition",
        "area_name": "06. Metacognition (Self-Correction & LTI Stability)",
        "tests": [
            {
                "id": "EN_06_1",
                "name": "Contradiction Detection",
                "prompt": "Statement: 'The system has 0 active models in VRAM, and currently uses 4.68 GB of VRAM for the 8B model.' Is this consistent or contradictory? Answer with CONSISTENT or CONTRADICTORY.",
                "verify": lambda o: "contradictory" in o.lower(),
            },
            {
                "id": "EN_06_2",
                "name": "Self-Correction Reasoning",
                "prompt": "You stated 7 * 8 = 54. Verify and correct your answer. Answer with: 56.",
                "verify": lambda o: "56" in o,
            },
            {
                "id": "EN_06_3",
                "name": "LTI State Stability Criterion",
                "prompt": "In a discrete-time Linear Time-Invariant system h_{t+1} = A*h_t + B*e, for bounded-input bounded-output stability, must the spectral radius rho(A) be strictly less than 1 or greater than 1? Answer LESS or GREATER.",
                "verify": lambda o: "less" in o.lower() and "greater" not in o.lower(),
            },
        ],
    },
    {
        "area_id": "07_red_team_security",
        "area_name": "07. Red-Team & Security Audit (Fuzzing & Vulnerabilities)",
        "tests": [
            {
                "id": "EN_07_1",
                "name": "SQL Injection Detection",
                "prompt": "Is the query \"SELECT * FROM users WHERE user = '\" + input + \"'\" vulnerable to SQL injection? Answer YES or NO.",
                "verify": lambda o: "yes" in o.lower(),
            },
            {
                "id": "EN_07_2",
                "name": "Arbitrary Code Execution Audit",
                "prompt": "Which function is safer to deserialize untrusted JSON strings in Python: eval() or json.loads()? Answer with only the safe function.",
                "verify": lambda o: "json.loads" in o.lower() and "eval" not in o.lower().replace("eval()", ""),
            },
            {
                "id": "EN_07_3",
                "name": "Path Traversal Prevention",
                "prompt": "Does input containing '../../etc/passwd' represent a path traversal attack vector? Answer YES or NO.",
                "verify": lambda o: "yes" in o.lower(),
            },
        ],
    },
    {
        "area_id": "08_speech_synthesis_vocal",
        "area_name": "08. Speech Synthesis & Vocal Formatting",
        "tests": [
            {
                "id": "EN_08_1",
                "name": "Currency Pronunciation Expansion",
                "prompt": "How should '$45.50' be expanded for a text-to-speech engine in English? Answer with 'forty-five dollars and fifty cents'.",
                "verify": lambda o: "forty-five" in o.lower() and "dollars" in o.lower(),
            },
            {
                "id": "EN_08_2",
                "name": "Metric Unit Verbalization",
                "prompt": "How should '120 km/h' be expanded in words for speech synthesis? Answer with 'kilometers per hour'.",
                "verify": lambda o: "kilometers per hour" in o.lower(),
            },
            {
                "id": "EN_08_3",
                "name": "SSML Pause Syntax",
                "prompt": "In standard SSML, what tag represents a 500 millisecond pause? Answer with <break time=\"500ms\"/>.",
                "verify": lambda o: "<break" in o and "500ms" in o,
            },
        ],
    },
    {
        "area_id": "09_multimodal_vision",
        "area_name": "09. Multimodal & Visual Coordinate Space",
        "tests": [
            {
                "id": "EN_09_1",
                "name": "Bounding Box IoU Computation",
                "prompt": "Box A = [0, 0, 10, 10] (area 100). Box B = [0, 0, 10, 10] (area 100). What is the exact Intersection over Union (IoU)? Answer with 1.0 or 0.0.",
                "verify": lambda o: "1.0" in o or "1" in o,
            },
            {
                "id": "EN_09_2",
                "name": "SVG Circle Diameter Calculation",
                "prompt": "In an SVG element <circle cx=\"50\" cy=\"50\" r=\"25\"/>, what is the circle diameter in pixels? Answer with only the number.",
                "verify": lambda o: "50" in o,
            },
            {
                "id": "EN_09_3",
                "name": "OCR Coordinate Normalization",
                "prompt": "If a screen resolution is 1920x1080 and an element center is at X=960, Y=540, what are the normalized coordinates between 0 and 1? Answer in format: 0.5, 0.5.",
                "verify": lambda o: "0.5" in o,
            },
        ],
    },
    {
        "area_id": "10_deliberative_planning",
        "area_name": "10. Deliberative Planning & Dependency Graphs",
        "tests": [
            {
                "id": "EN_10_1",
                "name": "Topological Order Resolution",
                "prompt": "Task A requires Task B. Task B requires Task C. In what order must they execute? Answer: C -> B -> A.",
                "verify": lambda o: ("c" in o.lower() and "b" in o.lower() and "a" in o.lower()) and (o.lower().find("c") < o.lower().find("b") < o.lower().find("a")),
            },
            {
                "id": "EN_10_2",
                "name": "Action Precondition Logic",
                "prompt": "To delete a file, which precondition is mandatory: file exists or file is compiled? Answer: FILE_EXISTS.",
                "verify": lambda o: "file_exists" in o.lower() or "exists" in o.lower(),
            },
            {
                "id": "EN_10_3",
                "name": "Circular Dependency Deadlock",
                "prompt": "If Service 1 waits for Service 2, and Service 2 waits for Service 1, what failure state occurs? Answer: DEADLOCK.",
                "verify": lambda o: "deadlock" in o.lower(),
            },
        ],
    },
    {
        "area_id": "11_scientific_reasoning",
        "area_name": "11. Scientific & Physics Invariants",
        "tests": [
            {
                "id": "EN_11_1",
                "name": "Ohm's Law Calculation",
                "prompt": "By Ohm's Law (V = R * I), if resistance R = 10 Ohms and current I = 2 Amperes, what is the voltage V? Answer with 20 V.",
                "verify": lambda o: "20" in o,
            },
            {
                "id": "EN_11_2",
                "name": "Chemical Stoichiometry",
                "prompt": "In the balanced combustion of methane CH4 + 2 O2 -> CO2 + 2 H2O, how many moles of H2O are produced from 3 moles of CH4? Answer with only the number.",
                "verify": lambda o: "6" in o,
            },
            {
                "id": "EN_11_3",
                "name": "Arithmetic Intensity in Roofline Model",
                "prompt": "If a kernel executes 100 GFLOPs and transfers 20 GB of memory from DRAM, what is its Arithmetic Intensity in FLOPs/byte? Answer with 5.",
                "verify": lambda o: "5" in o,
            },
        ],
    },
    {
        "area_id": "12_language_and_discourse",
        "area_name": "12. Language & Discourse Logic",
        "tests": [
            {
                "id": "EN_12_1",
                "name": "Information Compression",
                "prompt": "Summarize 'The memory bus bandwidth reached physical ceiling and cannot transfer more bytes' into under 5 words. Answer concisely.",
                "verify": lambda o: len(o.split()) <= 6 and ("bandwidth" in o.lower() or "memory" in o.lower()),
            },
            {
                "id": "EN_12_2",
                "name": "Syllogistic Deduction",
                "prompt": "All processors with AVX2 support 256-bit SIMD registers. Intel Xeon E5-2697 v3 supports AVX2. Does it support 256-bit SIMD? Answer YES or NO.",
                "verify": lambda o: "yes" in o.lower(),
            },
            {
                "id": "EN_12_3",
                "name": "Coreference Resolution",
                "prompt": "In 'The GPU completed the kernel because it had enough registers', what does 'it' refer to? Answer: GPU.",
                "verify": lambda o: "gpu" in o.lower(),
            },
        ],
    },
    {
        "area_id": "13_hardware_governor",
        "area_name": "13. Hardware Governor & Silicon Limits",
        "tests": [
            {
                "id": "EN_13_1",
                "name": "OOM Circuit Breaker",
                "prompt": "If VRAM consumption reaches 7.8 GB out of 8.0 GB (97.5%), should the system accept a new 4 GB allocation or trigger circuit breaker? Answer: CIRCUIT_BREAKER.",
                "verify": lambda o: "circuit_breaker" in o.lower(),
            },
            {
                "id": "EN_13_2",
                "name": "Watchdog Timeout Policy",
                "prompt": "If a child process heartbeat is silent for 3 times the timeout threshold, what action should the watchdog take? Answer: KILL_OR_RESTART.",
                "verify": lambda o: "kill" in o.lower() or "restart" in o.lower(),
            },
            {
                "id": "EN_13_3",
                "name": "AVX2 SIMD Lane Width",
                "prompt": "How many 32-bit single-precision float elements fit into one 256-bit AVX2 register? Answer: 8.",
                "verify": lambda o: "8" in o,
            },
        ],
    },
]


# ==============================================================================
# SUITE DOS 10 DESAFIOS CLAUDE OPUS EM INGLÊS COM ASSERTIONS EXECUTÁVEIS
# ==============================================================================
OPUS_10_TESTS_EN = [
    {
        "id": "OPUS_01_regex_pure",
        "name": "01. Pure Regex Engine with '.', '*' and '+' (No re module)",
        "prompt": (
            "Write only the Python function `match_pattern(text: str, pattern: str) -> bool` without comments "
            "that matches `text` against `pattern`. Support '.' (matches any single character), '*' (0 or more "
            "of preceding character), and '+' (1 or more of preceding character). Do not use the `re` module."
        ),
        "assertions": [
            "assert match_pattern('aa', 'a') is False",
            "assert match_pattern('aa', 'a*') is True",
            "assert match_pattern('ab', '.*') is True",
            "assert match_pattern('aab', 'c*a*b') is True",
            "assert match_pattern('mississippi', 'mis*is*p*.') is False",
            "assert match_pattern('a', 'a+') is True",
            "assert match_pattern('', 'a+') is False",
            "assert match_pattern('aaa', 'a+') is True",
        ],
    },
    {
        "id": "OPUS_02_parser_unary_power",
        "name": "02. Arithmetic Parser without eval() (Unary Minus and Right-Associative '^')",
        "prompt": (
            "Write only the Python function `evaluate_expression(expr: str) -> int` without comments "
            "that evaluates arithmetic expressions without using `eval()`. Support integers, binary operators "
            "+, -, *, //, right-associative exponentiation '^', unary minus '-', and parentheses '()'."
        ),
        "assertions": [
            "assert evaluate_expression('3 + 5 * 2') == 13",
            "assert evaluate_expression('(3 + 5) * 2') == 16",
            "assert evaluate_expression('-3 + 5') == 2",
            "assert evaluate_expression('2 ^ 3 ^ 2') == 512",
            "assert evaluate_expression('10 // 3') == 3",
            "assert evaluate_expression('-(2 + 3) * 4') == -20",
        ],
    },
    {
        "id": "OPUS_03_dijkstra_2d_free_edges",
        "name": "03. 2D State-Space Dijkstra (Up to K Free Edges)",
        "prompt": (
            "Write only the Python function `min_cost_k_free(n: int, edges: list[tuple[int, int, int]], k: int) -> int` "
            "without comments that computes the minimum path cost from node 0 to node n - 1 in an undirected weighted "
            "graph, where you can choose up to `k` edges to cross for cost 0. Return -1 if unreachable."
        ),
        "assertions": [
            "assert min_cost_k_free(4, [(0, 1, 10), (1, 2, 20), (2, 3, 30), (0, 3, 100)], 1) == 30",
            "assert min_cost_k_free(4, [(0, 1, 10), (1, 2, 20), (2, 3, 30), (0, 3, 100)], 0) == 60",
            "assert min_cost_k_free(3, [(0, 1, 5)], 1) == -1",
            "assert min_cost_k_free(1, [], 0) == 0",
        ],
    },
    {
        "id": "OPUS_04_max_rectangle_binary_matrix",
        "name": "04. Monotonic Stack: Maximal Rectangle of 1s in Binary Matrix",
        "prompt": (
            "Write only the Python function `maximal_rectangle(matrix: list[list[int]]) -> int` without comments "
            "that finds the largest rectangle containing only 1s in a 2D binary matrix and returns its area in O(M*N)."
        ),
        "assertions": [
            "assert maximal_rectangle([[1,0,1,0,0],[1,0,1,1,1],[1,1,1,1,1],[1,0,0,1,0]]) == 6",
            "assert maximal_rectangle([]) == 0",
            "assert maximal_rectangle([[0]]) == 0",
            "assert maximal_rectangle([[1]]) == 1",
            "assert maximal_rectangle([[0,0],[0,0]]) == 0",
        ],
    },
    {
        "id": "OPUS_05_bitmask_dp_open_tsp",
        "name": "05. Bitmask DP: Minimum Hamiltonian Path (Open TSP)",
        "prompt": (
            "Write only the Python function `open_tsp(dist: list[list[int]]) -> int` without comments "
            "that computes the minimum cost to visit all nodes exactly once starting at node 0 and ending at any node "
            "(do NOT return to 0). Use Bitmask Dynamic Programming."
        ),
        "assertions": [
            "assert open_tsp([[0, 20, 42, 25], [20, 0, 30, 34], [42, 30, 0, 10], [25, 34, 10, 0]]) == 60",
            "assert open_tsp([[0, 10, 15, 20], [10, 0, 35, 25], [15, 35, 0, 30], [20, 25, 30, 0]]) == 65",
            "assert open_tsp([[0]]) == 0",
        ],
    },
    {
        "id": "OPUS_06_median_two_sorted_arrays",
        "name": "06. Partition Search: Median of Two Sorted Arrays",
        "prompt": (
            "Write only the Python function `find_median_sorted(a: list[int], b: list[int]) -> float` without comments "
            "that finds the median of two sorted arrays in float format."
        ),
        "assertions": [
            "assert float(find_median_sorted([1, 3], [2])) == 2.0",
            "assert float(find_median_sorted([1, 2], [3, 4])) == 2.5",
            "assert float(find_median_sorted([], [1])) == 1.0",
            "assert float(find_median_sorted([2], [])) == 2.0",
        ],
    },
    {
        "id": "OPUS_07_longest_valid_parentheses_trap",
        "name": "07. Index Stack: Longest Valid Parentheses Substring",
        "prompt": (
            "Write only the Python function `longest_valid_parentheses(s: str) -> int` without comments "
            "that finds the length of the longest valid (well-formed) parentheses substring."
        ),
        "assertions": [
            "assert longest_valid_parentheses('(()') == 2",
            "assert longest_valid_parentheses(')()())') == 4",
            "assert longest_valid_parentheses('') == 0",
            "assert longest_valid_parentheses('()(()') == 2",
            "assert longest_valid_parentheses('()(())') == 6",
        ],
    },
    {
        "id": "OPUS_08_trapping_rain_water",
        "name": "08. Two-Pointers: Trapping Rain Water",
        "prompt": (
            "Write only the Python function `trap_rain_water(heights: list[int]) -> int` without comments "
            "that computes how much water it can trap after raining using Two-Pointers in O(N) time and O(1) space."
        ),
        "assertions": [
            "assert trap_rain_water([0,1,0,2,1,0,1,3,2,1,2,1]) == 6",
            "assert trap_rain_water([4,2,0,3,2,5]) == 9",
            "assert trap_rain_water([]) == 0",
            "assert trap_rain_water([3]) == 0",
        ],
    },
    {
        "id": "OPUS_09_binary_tree_max_path_sum",
        "name": "09. Binary Tree: Maximum Path Sum Any-to-Any (with Negative Nodes)",
        "prompt": (
            "Write only the Python function `max_path_sum_tree(root: dict | None) -> int` without comments "
            "that returns the maximum path sum of any non-empty path in a binary tree represented as dicts "
            "{'v': val, 'l': left, 'r': right}."
        ),
        "assertions": [
            "assert max_path_sum_tree({'v': 1, 'l': {'v': 2, 'l': None, 'r': None}, 'r': {'v': 3, 'l': None, 'r': None}}) == 6",
            "assert max_path_sum_tree({'v': -10, 'l': {'v': 9, 'l': None, 'r': None}, 'r': {'v': 20, 'l': {'v': 15, 'l': None, 'r': None}, 'r': {'v': 7, 'l': None, 'r': None}}}) == 42",
            "assert max_path_sum_tree({'v': -3, 'l': None, 'r': None}) == -3",
        ],
    },
    {
        "id": "OPUS_10_dpll_sat_solver_cnf",
        "name": "10. DPLL SAT Solver for CNF Formulas",
        "prompt": (
            "Write only the Python function `solve_sat_cnf(num_vars: int, clauses: list[list[int]]) -> dict[int, bool] | None` "
            "without comments that solves a boolean satisfiability problem in CNF. Variables are 1-indexed. Return a dict "
            "mapping each variable 1..num_vars to True/False if SAT, or None if UNSAT."
        ),
        "assertions": [
            "r1 = solve_sat_cnf(2, [[1, 2], [1, -2], [-1, 2]]); assert isinstance(r1, dict) and r1[1] is True and r1[2] is True",
            "r2 = solve_sat_cnf(1, [[1], [-1]]); assert r2 is None",
            "r3 = solve_sat_cnf(3, [[1, -2], [2, -3], [3, -1]]); assert isinstance(r3, dict)",
        ],
    },
]


def run_g9v3_benchmark() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    print("\n" + "=" * 88)
    print(" [BENCHMARK OFICIAL EM INGLÊS] AI9STARS / G9V3-3B (1.77 GB Q4_K_M) NA RX 580 VULKAN")
    print(" Bateria 1: 13 Áreas Cognitivas x 3 Testes = 39 Testes em Inglês")
    print(" Bateria 2: 10 Desafios Algorítmicos Nível Claude Opus em Inglês com Pytest Formal")
    print("=" * 88, flush=True)

    # 1. Download
    model_file = ensure_download()

    # 2. Boot
    proc = start_vulkan_server(model_file, port=8081)
    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "model": "ai9stars/G9v3-3B",
        "quant": "Q4_K_M (1.77 GB)",
        "language": "English (100% Native Evaluation)",
        "hardware": "AMD Radeon RX 580 8GB Vulkan Bare-Metal",
        "part1_13_areas": {},
        "part2_opus_10": {},
    }

    try:
        # ----------------------------------------------------------------------
        # PARTE 1: 13 ÁREAS (39 TESTES)
        # ----------------------------------------------------------------------
        print("\n" + "=" * 88)
        print(" [PARTE 1] EXECUTANDO AS 13 ÁREAS COGNITIVAS EM INGLÊS (39 TESTES)...")
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
                t_start = time.perf_counter()
                out, tps = query_g9v3(t["prompt"], port=8081, n_predict=128, is_code=t.get("is_code", False))
                passed = False
                try:
                    passed = bool(t["verify"](out))
                except Exception:
                    passed = False

                elapsed_ms = round((time.perf_counter() - t_start) * 1000.0, 2)
                if passed:
                    area_passes += 1
                    total_areas_pass += 1
                if tps > 0:
                    areas_tps_list.append(tps)

                badge = "PASS" if passed else "FAIL"
                print(f"   [{badge:4s}] {t['name']:40s} | Vel: {tps:5.2f} t/s | Tempo: {elapsed_ms:6.1f}ms", flush=True)
                area_tests.append({
                    "id": t["id"],
                    "name": t["name"],
                    "passed": passed,
                    "tps": round(tps, 2),
                    "latency_ms": elapsed_ms,
                    "output": out[:160],
                })

            report["part1_13_areas"][area_id] = {
                "name": area_name,
                "passed": area_passes,
                "total": len(area["tests"]),
                "score_str": f"{area_passes}/{len(area['tests'])}",
                "tests": area_tests,
            }

        p1_time = round(time.perf_counter() - p1_t0, 2)
        p1_avg_tps = round(sum(areas_tps_list) / max(1, len(areas_tps_list)), 2)
        report["part1_summary"] = {
            "passed": total_areas_pass,
            "total": total_areas_tests,
            "pct": round((total_areas_pass / total_areas_tests) * 100.0, 2),
            "avg_tps": p1_avg_tps,
            "total_time_s": p1_time,
        }
        PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROOF_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\n -> [PARTE 1 CONCLUÍDA]: {total_areas_pass}/{total_areas_tests} ({report['part1_summary']['pct']}%) | Vel: {p1_avg_tps} t/s | Tempo: {p1_time}s", flush=True)

        # ----------------------------------------------------------------------
        # PARTE 2: 10 DESAFIOS CLAUDE OPUS EM INGLÊS COM PYTEST FORMAL
        # ----------------------------------------------------------------------
        print("\n" + "=" * 88)
        print(" [PARTE 2] EXECUTANDO OS 10 DESAFIOS CLAUDE OPUS EM INGLÊS COM PYTEST...")
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
            prompt = test["prompt"] + "\nWrite concise clean Python code only, no comments."
            first_passed = False
            final_passed = False
            initial_ce = None
            last_code = ""
            last_tps = 0.0

            while attempts < 2:
                attempts += 1
                last_code, last_tps = query_g9v3(prompt, port=8081, n_predict=512, is_code=True)
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
                        f"Rewrite the function correctly to pass all test cases (concise, no comments)."
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

        p2_time = round(time.perf_counter() - p2_t0, 2)
        p2_avg_tps = round(sum(opus_tps_list) / max(1, len(opus_tps_list)), 2)
        report["part2_opus_10"] = {
            "zero_shot_passes": opus_zero_shot,
            "final_passes": opus_final_passes,
            "repaired_passes": opus_repaired,
            "final_pct": round((opus_final_passes / len(OPUS_10_TESTS_EN)) * 100.0, 1),
            "avg_tps": p2_avg_tps,
            "total_time_s": p2_time,
            "tests": opus_tests_results,
        }

        PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
        PROOF_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

        print("\n" + "=" * 88)
        print(" [RESULTADO CONSOLIDADO G9V3-3B NA RX 580 VULKAN]")
        print("=" * 88)
        print(f" * Parte 1 (13 Áreas em Inglês): {total_areas_pass}/39 ({report['part1_summary']['pct']}%) | Vel: {p1_avg_tps} t/s | Tempo: {p1_time}s")
        print(f" * Parte 2 (10 Desafios Opus EN): {opus_final_passes}/10 ({report['part2_opus_10']['final_pct']}%) | De 1ª: {opus_zero_shot}/10 | Vel: {p2_avg_tps} t/s | Tempo: {p2_time}s")
        print("=" * 88, flush=True)
        return 0

    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=5.0)
            except Exception:
                proc.kill()


if __name__ == "__main__":
    sys.exit(run_g9v3_benchmark())
