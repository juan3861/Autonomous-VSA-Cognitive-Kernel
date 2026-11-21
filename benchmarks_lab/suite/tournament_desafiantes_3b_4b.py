# -*- coding: utf-8 -*-
"""
AETHERMIND — TORNEIO DOS NOVOS DESAFIANTES 3B-4B VS CAMPEOES CONSAGRADOS
Comandante Primário: Mestre Ruan

Novos Desafiantes:
1. Vortecks/G9v3-3B-Heretic-Abliterated-GGUF (Q4_K_M)
2. Edge-Quant/Nanbeige4.1-3B-Q4_K_M-GGUF (Q4_K_M)
3. bartowski/Nanbeige_Nanbeige4.2-3B-GGUF (Q4_K_M)
4. IFM/K2-Horizon-3.7B-GGUF (Q4_K_M)

Nota: bartowski/ai9stars_G9v3-3B-GGUF (Q4_K_M a BF16) já foi 100% auditado no torneio anterior.
"""

import os
import sys
import time
import json
import urllib.request
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROTOR_ROOT = Path(r"F:\rotor-llm")
if str(ROTOR_ROOT) not in sys.path:
    sys.path.insert(0, str(ROTOR_ROOT))

import tournament_finalistas_3b_4b_quants as tq
from rlm import LambdaRLM

MODELS_DIR = Path(r"F:\models\desafiantes_3b_4b")
PROOF_FILE = Path(r"F:\data\proof_desafiantes_3b_4b.json")
LOG_FILE = Path(r"F:\data\tournament_desafiantes_3b_4b.log")
SERVER_LOG_FILE = Path(r"F:\data\llama_server_desafiantes_3b_4b.log")

# Redireciona globals do módulo reutilizado
tq.MODELS_DIR = MODELS_DIR
tq.PROOF_FILE = PROOF_FILE
tq.LOG_FILE = LOG_FILE
tq.SERVER_LOG_FILE = SERVER_LOG_FILE

CHALLENGERS = [
    {
        "id": "vortecks_g9v3_heretic__q4_k_m",
        "champ": "Vortecks/G9v3-3B-Heretic-Abliterated",
        "champ_short": "G9v3-3B-Heretic",
        "params": "3B",
        "teacher": "Heretic Abliterated (KL 0.0843)",
        "quant": "Q4_K_M",
        "filename": "G9v3-3B-Heretic-Abliterated-Q4_K_M.gguf",
        "url": "https://huggingface.co/Vortecks/G9v3-3B-Heretic-Abliterated-GGUF/resolve/main/G9v3-3B-Heretic-Abliterated-Q4_K_M.gguf",
    },
    {
        "id": "nanbeige4_1_3b__q4_k_m",
        "champ": "Nanbeige/Nanbeige4.1-3B",
        "champ_short": "Nanbeige4.1-3B",
        "params": "3B",
        "teacher": "Nanbeige 4.1 Native",
        "quant": "Q4_K_M",
        "filename": "nanbeige4.1-3b-q4_k_m.gguf",
        "url": "https://huggingface.co/Edge-Quant/Nanbeige4.1-3B-Q4_K_M-GGUF/resolve/main/nanbeige4.1-3b-q4_k_m.gguf",
    },
    {
        "id": "nanbeige4_2_3b__q4_k_m",
        "champ": "Nanbeige/Nanbeige4.2-3B",
        "champ_short": "Nanbeige4.2-3B",
        "params": "3B",
        "teacher": "Nanbeige 4.2 Native (imatrix)",
        "quant": "Q4_K_M",
        "filename": "Nanbeige_Nanbeige4.2-3B-Q4_K_M.gguf",
        "url": "https://huggingface.co/bartowski/Nanbeige_Nanbeige4.2-3B-GGUF/resolve/main/Nanbeige_Nanbeige4.2-3B-Q4_K_M.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q4_k_m",
        "champ": "IFM/K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "params": "3.7B",
        "teacher": "IFM K2-Horizon Native",
        "quant": "Q4_K_M",
        "filename": "K2-Horizon-4B-Q4_K_M.gguf",
        "url": "https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q4_K_M.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q5_k_m",
        "champ": "IFM/K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "params": "3.7B",
        "teacher": "IFM K2-Horizon Native",
        "quant": "Q5_K_M",
        "filename": "K2-Horizon-4B-Q5_K_M.gguf",
        "url": "https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q5_K_M.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q6_k",
        "champ": "IFM/K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "params": "3.7B",
        "teacher": "IFM K2-Horizon Native",
        "quant": "Q6_K",
        "filename": "K2-Horizon-4B-Q6_K.gguf",
        "url": "https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q6_K.gguf",
    },
    {
        "id": "k2_horizon_3_7b__q8_0",
        "champ": "IFM/K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "params": "3.7B",
        "teacher": "IFM K2-Horizon Native",
        "quant": "Q8_0",
        "filename": "K2-Horizon-4B-Q8_0.gguf",
        "url": "https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-Q8_0.gguf",
    },
    {
        "id": "k2_horizon_3_7b__bf16",
        "champ": "IFM/K2-Horizon-3.7B",
        "champ_short": "K2-Horizon-3.7B",
        "params": "3.7B",
        "teacher": "IFM K2-Horizon Native",
        "quant": "BF16",
        "filename": "K2-Horizon-4B-BF16.gguf",
        "url": "https://huggingface.co/IFM/K2-Horizon-3.7B-GGUF/resolve/main/K2-Horizon-4B-BF16.gguf",
    },
]


def download_if_needed(url: str, dest: Path):
    """Baixa o GGUF via streaming direto para o disco F: sem passar pelo cache do disco C:."""
    if dest.exists() and dest.stat().st_size > 100 * 1024 * 1024:
        tq.log(f"[+] Arquivo já presente em disco: {dest.name} ({dest.stat().st_size / 1024**3:.2f} GB)")
        return

    dest.parent.mkdir(parents=True, exist_ok=True)
    part_path = dest.with_suffix(".gguf.part")
    tq.log(f"[*] Baixando {dest.name} de {url} ...")
    t0 = time.time()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        last_pct = -1
        with open(part_path, "wb") as out:
            while True:
                chunk = resp.read(1024 * 1024 * 4)  # 4 MB chunks
                if not chunk:
                    break
                out.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    pct = int((downloaded / total) * 100)
                    if pct >= last_pct + 10:
                        last_pct = pct
                        elapsed = max(0.1, time.time() - t0)
                        mb_s = (downloaded / (1024**2)) / elapsed
                        tq.log(f"    -> Download {dest.name}: {pct}% ({downloaded/1024**3:.2f}/{total/1024**3:.2f} GB) @ {mb_s:.1f} MB/s")
    if dest.exists():
        dest.unlink()
    part_path.rename(dest)
    tq.log(f"[+] Download concluído: {dest.name} em {time.time() - t0:.1f}s")


def main():
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tq.log("=" * 80)
    tq.log("AETHERMIND — TORNEIO DOS NOVOS DESAFIANTES 3B-4B VS CAMPEOES")
    tq.log("=" * 80)

    results = {}
    if PROOF_FILE.exists():
        try:
            results = json.loads(PROOF_FILE.read_text(encoding="utf-8"))
            tq.log(f"[*] Carregado histórico com {len(results)} desafiantes concluídos.")
        except Exception:
            results = {}

    for idx, c in enumerate(CHALLENGERS, 1):
        c_id = c["id"]
        c_name = f"{c['champ_short']} [{c['quant']}]"
        model_path = MODELS_DIR / c["filename"]

        tq.log("\n" + "#" * 80)
        tq.log(f"[{idx}/{len(CHALLENGERS)}] PROCESSANDO: {c_name} ({c['params']})")
        tq.log(f"   Modelo: {c['champ']} | Quant: {c['quant']} | Origem: {c['teacher']}")
        tq.log(f"   Arquivo: {model_path}")
        tq.log("#" * 80)

        if results.get(c_id, {}).get("completed"):
            prev = results[c_id]
            tq.log(f"[+] {c_name} já avaliado ({prev['score_13_areas']}/39 | Opus: {prev['score_opus']}/10 | TG: {prev['tg_tok_s']:.2f} t/s). Pulando...")
            continue

        download_if_needed(c["url"], model_path)

        proc = None
        try:
            cpu_speed_info = tq.benchmark_cpu_speed(model_path)
            proc, boot_s, active_ngl = tq.start_llama_server(model_path)
            speed_info = tq.benchmark_speed(boot_s)

            lambda_engine = LambdaRLM(
                backend="openai",
                backend_kwargs={
                    "model_name": model_path.name,
                    "base_url": f"{tq.BASE_URL}/v1",
                    "api_key": "none",
                    "max_tokens": 768,
                    "temperature": 0.0,
                    "timeout": 480.0,
                },
                context_window_chars=4096,
                verbose=False
            )

            res_13 = tq.run_13_areas(lambda_engine)
            res_opus = tq.run_opus(lambda_engine)

            results[c_id] = {
                "champ": c["champ"],
                "champ_short": c["champ_short"],
                "params": c["params"],
                "teacher": c["teacher"],
                "quant": c["quant"],
                "size_mb": round(model_path.stat().st_size / (1024**2), 2),
                "active_ngl": active_ngl,
                "speed": speed_info,
                "boot_seconds": speed_info["boot_seconds"],
                "pp_tok_s": speed_info["prompt_per_second"],
                "tg_tok_s": speed_info["predicted_per_second"],
                "cpu_pp_tok_s": cpu_speed_info["cpu_pp_tok_s"],
                "cpu_tg_tok_s": cpu_speed_info["cpu_tg_tok_s"],
                "score_13_areas": res_13["passed"],
                "baseline_13_areas": res_13["baseline_passed"],
                "pct_13_areas": res_13["pct"],
                "perfect_areas_count": res_13["perfect_areas_count"],
                "score_opus": res_opus["passed"],
                "baseline_opus": res_opus["baseline_passed"],
                "pct_opus": res_opus["pct"],
                "details_13_areas": res_13,
                "details_opus": res_opus,
                "completed": True,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            PROOF_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            tq.log(f"[+] Prova gravada em {PROOF_FILE.name}!")

        except Exception as e:
            tq.log(f"[!] Erro ao testar {c_name}: {e}")
        finally:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except Exception:
                    pass
            tq.kill_port_8089()
            time.sleep(1.0)

    tq.log("\n" + "=" * 80)
    tq.log("[+] TORNEIO DOS NOVOS DESAFIANTES 3B-4B FINALIZADO!")
    tq.log("=" * 80)


if __name__ == "__main__":
    main()

