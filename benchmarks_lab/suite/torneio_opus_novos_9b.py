# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 rotor-llm contributors

"""Torneio Extremo Nível Claude Opus: 4 Novos Modelos Destilados 9B na RX 580 Vulkan.
Contenders:
1. XiaomiMiMo/MiMo-V2.6-Distill-Qwen-9B (Q4_K_M, 5.44 GB)
2. ornith-ai/Ornith-1.5-9B (Q4_K_M, 5.50 GB)
3. Jackrong/Qwopus3.5-9B-v3 (Q4_K_M, 5.24 GB)
4. Qwen3.5-9B Puro (Q4_K_M, 5.75 GB)

Baseline Champion a ser batido:
- rlm-qwen3-8b-v0.1-Q4_K_M (3/10 Opus, 6.00 t/s, 675.75s)
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from duelo_nivel_opus_8b_vs_9b import OPUS_10_TESTS
from huggingface_hub import hf_hub_download
from router.formal_verifier import formal_verifier
from router.grammar_fastforward import grammar_ff_engine

MODELS_DIR = Path(r"C:\AetherMind_Contenders")
PROOF_TOURNAMENT_PATH = Path(r"F:\data\proof_torneio_opus_9b_distills.json")
VULKAN_SERVER_BIN = r"F:\tools\lc_vulkan\llama-server.exe"

CONTENDERS = [
    {
        "key": "mimo-9b",
        "name": "MiMo-V2.6-Distill-Qwen-9B",
        "repo": "bartowski/MiMo-V2.6-Distill-Qwen-9B-GGUF",
        "filename": "MiMo-V2.6-Distill-Qwen-9B-Q4_K_M.gguf",
        "vram_gb": 5.44,
        "gpu_layers": 31,
    },
    {
        "key": "ornith-9b",
        "name": "Ornith-1.5-9B",
        "repo": "bartowski/Ornith-1.5-9B-GGUF",
        "filename": "Ornith-1.5-9B-Q4_K_M.gguf",
        "vram_gb": 5.50,
        "gpu_layers": 31,
    },
    {
        "key": "qwopus-9b",
        "name": "Qwopus3.5-9B-v3",
        "repo": "mradermacher/Qwopus3.5-9B-v3-GGUF",
        "filename": "Qwopus3.5-9B-v3.Q4_K_M.gguf",
        "vram_gb": 5.24,
        "gpu_layers": 32,
    },
    {
        "key": "qwen35-pure-9b",
        "name": "Qwen3.5-9B-Pure",
        "repo": "bartowski/Qwen_Qwen3.5-9B-GGUF",
        "filename": "Qwen_Qwen3.5-9B-Q4_K_M.gguf",
        "vram_gb": 5.75,
        "gpu_layers": 30,
    },
]


def ensure_download(target: dict[str, Any]) -> Path:
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = MODELS_DIR / target["filename"]
    if dest_path.exists() and dest_path.stat().st_size > 4_000_000_000:
        print(f" -> [CACHE HIT] {target['filename']} já existe ({dest_path.stat().st_size / (1024**3):.2f} GB).", flush=True)
        return dest_path

    print(f"\n[*] Baixando {target['name']} de {target['repo']}...", flush=True)
    t0 = time.perf_counter()
    downloaded_path = hf_hub_download(
        repo_id=target["repo"],
        filename=target["filename"],
        local_dir=str(MODELS_DIR),
    )
    elapsed = round(time.perf_counter() - t0, 1)
    sz = Path(downloaded_path).stat().st_size / (1024**3)
    print(f" -> [DOWNLOAD CONCLUÍDO] {sz:.2f} GB baixados em {elapsed}s (Média: {sz*1024/max(1, elapsed):.2f} MB/s).", flush=True)
    return Path(downloaded_path)


def start_vulkan_server(model_path: Path, gpu_layers: int, port: int = 8081, timeout_s: float = 75.0) -> subprocess.Popen[str]:
    subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"], capture_output=True)
    time.sleep(1.5)

    env = os.environ.copy()
    env["VK_LOADER_LAYERS_DISABLE"] = "~all~"
    env["DISABLE_LAYER_AMD_SWITCHABLE_GRAPHICS_1"] = "1"
    env["AMD_VULKAN_FORCE_GPU_MEMORY_PRIORITY"] = "1"

    cmd = [
        VULKAN_SERVER_BIN,
        "-m", str(model_path),
        "-ngl", str(gpu_layers),
        "-fa", "1",
        "-ctk", "q8_0",
        "-ctv", "q8_0",
        "-t", "8",
        "-c", "2048",
        "-b", "512",
        "-ub", "128",
        "-np", "1",
        "--cache-reuse", "256",
        "--no-mmap",
        "--prio", "2",
        "-C", "0x5555554",
        "--dynatemp-range", "0.4",
        "--min-p", "0.05",
        "--dry-multiplier", "0.8",
        "--host", "127.0.0.1",
        "--port", str(port),
    ]

    log_file = open(r"F:\data\llama_tournament_gpu.log", "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, env=env, stdout=log_file, stderr=subprocess.STDOUT, text=True)

    t0 = time.perf_counter()
    health_url = f"http://127.0.0.1:{port}/health"
    while time.perf_counter() - t0 < timeout_s:
        if proc.poll() is not None:
            raise RuntimeError(f"Servidor Vulkan encerrou prematuramente (código: {proc.poll()}).")
        try:
            req = urllib.request.Request(health_url)
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    print(f" -> [GPU ONLINE] Carregado em {time.perf_counter() - t0:.2f}s na RX 580 Vulkan.", flush=True)
                    return proc
        except Exception:
            time.sleep(1.0)

    proc.terminate()
    raise TimeoutError(f"Timeout ({timeout_s}s) ao subir servidor GPU Vulkan.")


def query_model(prompt: str, port: int = 8081, n_predict: int = 512) -> tuple[str, float]:
    plan = grammar_ff_engine.build_plan("python_func")
    clean_user = prompt.replace("/no_think", "").strip()
    effective_prompt = (
        f"<|im_start|>user\n{clean_user}<|im_end|>\n"
        f"<|im_start|>assistant\n<think>\n\n</think>\n"
        + plan.injected_prefix
    )
    stop_list = ["<|im_end|>", "<|endoftext|>", "```"]
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
    with urllib.request.urlopen(req, timeout=180.0) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    elapsed = max(0.001, time.perf_counter() - t0)
    raw_content = data.get("content", "")
    timings = data.get("timings", {})
    predicted_n = int(timings.get("predicted_n", max(1, len(raw_content) // 4)))
    tps = predicted_n / elapsed
    reconstructed = grammar_ff_engine.reconstruct_output(plan, raw_content)
    return reconstructed, tps


def run_tournament() -> int:
    try:
        sys.stdout.reconfigure(line_buffering=True)
    except Exception:
        pass

    print("\n" + "=" * 88)
    print(" [GRANDE TORNEIO NÍVEL CLAUDE OPUS] 4 NOVOS 9B DESTILADOS VS BASELINE 8B-RLM")
    print(" Silício: AMD Radeon RX 580 8GB GDDR5 (Vulkan Bare-Metal)")
    print(" Provas: 10 Desafios Algorítmicos Hardcore de Nível Claude Opus com Pytest Formal")
    print("=" * 88, flush=True)

    report: dict[str, Any] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "tournament": "Torneio 9B Distill Nível Claude Opus na RX 580 Vulkan",
        "baseline_champion": {
            "key": "8b-rlm",
            "name": "rlm-qwen3-8b-v0.1-Q4_K_M",
            "zero_shot_passes": 2,
            "final_passes": 3,
            "final_pct": 30.0,
            "avg_tps": 6.00,
            "total_wall_s": 675.75,
        },
        "contenders": {},
    }

    if PROOF_TOURNAMENT_PATH.exists():
        try:
            existing = json.loads(PROOF_TOURNAMENT_PATH.read_text(encoding="utf-8"))
            if "contenders" in existing:
                report["contenders"] = existing["contenders"]
        except Exception:
            pass

    for target in CONTENDERS:
        key = target["key"]
        print(f"\n{'='*88}\n [CONTENDER] {target['name']} ({target['filename']})\n{'='*88}", flush=True)

        # 1. Download
        model_file = ensure_download(target)

        # 2. Boot
        proc = start_vulkan_server(model_file, gpu_layers=target["gpu_layers"], port=8081)
        try:
            zero_shot = 0
            final_passes = 0
            repaired_count = 0
            tps_list: list[float] = []
            test_results: list[dict[str, Any]] = []
            total_wall_ms = 0.0

            for test in OPUS_10_TESTS:
                t_test = time.perf_counter()
                attempts = 0
                prompt = test["prompt"] + "\nSeja extremamente conciso no código Python, sem comentários."
                first_passed = False
                final_passed = False
                initial_ce = None
                last_code = ""
                last_tps = 0.0

                while attempts < 2:
                    attempts += 1
                    last_code, last_tps = query_model(prompt, port=8081, n_predict=512)
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
                            f"Sua tentativa anterior falhou no verificador formal:\n{ver.counterexample}\n"
                            f"Reescreva a função de forma correta e enxuta (sem comentários)."
                        )

                elapsed_ms = round((time.perf_counter() - t_test) * 1000.0, 2)
                total_wall_ms += elapsed_ms
                if first_passed:
                    zero_shot += 1
                if final_passed:
                    final_passes += 1
                if final_passed and attempts > 1:
                    repaired_count += 1
                if last_tps > 0:
                    tps_list.append(last_tps)

                badge = "PASS (1ª)" if first_passed else ("PASS (Reparado 2ª)" if final_passed else "FAIL")
                print(f"   [{key:14s}] {test['name']:60s} | {badge:16s} | Vel: {last_tps:5.2f} t/s | Tempo: {elapsed_ms:7.1f}ms", flush=True)

                test_results.append({
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

            avg_tps = round(sum(tps_list) / max(1, len(tps_list)), 2)
            cdata = {
                "name": target["name"],
                "file": target["filename"],
                "zero_shot_passes": zero_shot,
                "final_passes": final_passes,
                "repaired_passes": repaired_count,
                "final_pct": round(final_passes * 10.0, 1),
                "avg_tps": avg_tps,
                "total_wall_s": round(total_wall_ms / 1000.0, 2),
                "tests": test_results,
            }
            report["contenders"][key] = cdata
            PROOF_TOURNAMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
            PROOF_TOURNAMENT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f" -> [{key} FINALIZADO]: De 1ª={zero_shot}/10 | Final(c/ Reparo)={final_passes}/10 ({final_passes*10}%) | Vel={avg_tps} t/s", flush=True)

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5.0)
            except Exception:
                proc.kill()
            subprocess.run(["powershell", "-NoProfile", "-Command", "Get-Process -Name llama-server -ErrorAction SilentlyContinue | Stop-Process -Force"], capture_output=True)

    print("\n" + "=" * 88)
    print(" [LEADERBOARD FINAL DO TORNEIO CLAUDE OPUS NA RX 580 VULKAN]")
    print("=" * 88)
    print(f" * Baseline [8b-rlm        ]: Final: 3/10 (30.0%) | Vel: 6.00 t/s | Tempo: 675.75s")
    for k, cd in report["contenders"].items():
        print(f" * Novo     [{k:14s}]: Final: {cd['final_passes']}/10 ({cd['final_pct']}%) | Vel: {cd['avg_tps']} t/s | Tempo: {cd['total_wall_s']}s")
    print("=" * 88, flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(run_tournament())
