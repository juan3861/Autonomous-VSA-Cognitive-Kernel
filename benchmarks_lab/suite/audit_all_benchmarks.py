import os
import glob
import json
import re

DATA_DIR = "F:/data"
OUTPUT_MD = "F:/data/CATALOGO_MESTRE_BENCHMARKS_HISTORICOS.md"
OUTPUT_JSON = "F:/data/catalogo_mestre_benchmarks_historicos.json"

proof_files = glob.glob(os.path.join(DATA_DIR, "proof_*.json"))
print(f"Total de arquivos proof encontrados em {DATA_DIR}: {len(proof_files)}")

master_catalog = {}

for pf in sorted(proof_files):
    fname = os.path.basename(pf)
    try:
        with open(pf, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read().strip()
            if not content:
                continue
            data = json.loads(content)

        extracted = []

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    m = item.get("model") or item.get("model_name") or item.get("name") or item.get("modelo")
                    if m:
                        extracted.append((m, item))
        elif isinstance(data, dict):
            # Check nested keys
            for key in ["results", "models", "ranking", "rankings", "leaderboard", "data", "contenders", "evaluations"]:
                if key in data:
                    val = data[key]
                    if isinstance(val, dict):
                        for m, sub in val.items():
                            extracted.append((m, sub))
                    elif isinstance(val, list):
                        for item in val:
                            if isinstance(item, dict):
                                m = item.get("model") or item.get("model_name") or item.get("name") or item.get("modelo")
                                if m:
                                    extracted.append((m, item))
            # Also top-level keys if they look like model names (.gguf or known patterns)
            if not extracted:
                for k, v in data.items():
                    if isinstance(v, dict) and any(x in str(v).lower() for x in ["score", "pass", "tps", "areas", "opus", "tests", "accuracy", "bench"]):
                        extracted.append((k, v))
                    elif isinstance(v, (int, float, str)) and any(x in k.lower() for x in ["qwen", "gemma", "deepseek", "opus", "llama", "grok", "fable"]):
                        extracted.append((k, {"score": v}))

        print(f"[{fname}]: {len(extracted)} modelos extraídos.")

        for m_name, meta in extracted:
            # Clean model name
            m_clean = str(m_name).strip()
            # Normalize extension if present
            m_norm = re.sub(r"\.gguf$", "", m_clean, flags=re.IGNORECASE)
            
            if m_norm not in master_catalog:
                master_catalog[m_norm] = {
                    "canonical_name": m_norm,
                    "benchmarks": []
                }
            
            # Extract metrics summary
            summary = {}
            if isinstance(meta, dict):
                for k in ["score", "total_score", "pass_rate", "pass_count", "total_tests", "13_areas", "opus", "opus_score", "tps", "speed_tps", "prompt_tps", "eval_tps", "status", "baseline_score", "lambda_score", "gain_pct"]:
                    if k in meta:
                        summary[k] = meta[k]
                if not summary:
                    # capture small representation
                    summary = {k: v for k, v in meta.items() if isinstance(v, (int, float, str, bool)) and len(str(v)) < 100}
            else:
                summary["value"] = meta

            master_catalog[m_norm]["benchmarks"].append({
                "proof_file": fname,
                "summary": summary
            })

    except Exception as e:
        print(f"Erro ao processar {fname}: {e}")

# Check also markdown reports in F:/data/ to capture any that didn't have JSON or had special summaries
md_files = glob.glob(os.path.join(DATA_DIR, "RELATORIO_*.md"))
print(f"Total de relatórios Markdown encontrados: {len(md_files)}")

# Save JSON
with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
    json.dump(master_catalog, f, indent=2, ensure_ascii=False)

print(f"\n==========================================")
print(f"TOTAL DE MODELOS ÚNICOS NO CATÁLOGO: {len(master_catalog)}")
print(f"Catálogo salvo em {OUTPUT_JSON}")
