import os, sys
from pathlib import Path

# Search directories
SEARCH_DIRS = [
    Path(r"F:\AetherMind_Contenders"),
    Path(r"E:\models"),
    Path(r"F:\data\models"),
    Path(r"I:\AetherMind_High_Titans"),
    Path(r"I:\AetherMind_Contenders"),
    Path(r"I:\AetherMind_Archive"),
    Path(r"J:\AetherMind_Contenders"),
]

# The 23 items requested by Mestre Ruan
REQUESTED_ITEMS = [
    ("Jackrong/Gemopus-4-26B-A4B-it-GGUF", ["Gemopus-4-26B", "gemopus"]),
    ("glyphsoftware/gemma-4-26b-a4b-opus-4.7-distilled-gguf", ["gemma-4-26b-a4b-opus-4.7", "opus-4.7"]),
    ("mudler/Gemopus-4-26B-A4B-it-Preview-APEX-GGUF", ["APEX", "gemopus-4-26B-A4B-APEX"]),
    ("gemma-4-26b-a4b-opus-4.7-distilled.BF16-mmproj.gguf", ["mmproj"]),
    ("yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF", ["gemma4-v2", "gemma-4-12B"]),
    ("AtomicChat/gemma-4-26B-A4B-it-assistant-GGUF", ["gemma-4-26B-A4B-it-assistant", "assistant"]),
    ("TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill-v2-GGUF", ["gemma-4-26B-A4B-it-Claude-Opus", "TeichAI"]),
    ("Qwen3.5-30B-A3B Q4_K_M (bartowski)", ["Qwen_Qwen3-30B-A3B-Q4_K_M", "Qwen3-30B-A3B-Q4"]),
    ("Qwen3.5-30B-A3B IQ3_M (bartowski)", ["Qwen_Qwen3-30B-A3B-IQ3_M", "Qwen3-30B-A3B-IQ3"]),
    ("ibm-granite/granite-4.0-small-moe-GGUF", ["granite-4.0", "granite"]),
    ("TeichAI/Qwen3-30B-A3B-Claude-Opus-Distill-GGU", ["Qwen3-30B-A3B-Claude-Opus"]),
    ("unsloth/Qwen3.5-30B-A3B-GGUF", ["Qwen3.5-30B-A3B"]),
    ("Jackrong/Qwen3.5-30B-A3B-DeepSeek-V4-Pro-GGUF", ["Qwen3.5-30B-A3B-DeepSeek"]),
    ("unsloth/Qwen3-30B-A3B-Thinking-2507-GGUF", ["Qwen3-30B-A3B-Thinking"]),
    ("Achilles1089/fable-coder-35B-A3B-GGUF", ["fable-coder-35B", "fable-coder"]),
    ("lordx64/Qwen3.6-35B-A3B-Claude-4.7-Opus-Reasoning-Distilled", ["Qwen3.6-35B"]),
    ("MoreThought/Fable-5.1-Max-Reasoning-Filtered-10000x", ["Fable-5.1-Max"]),
    ("mondk/Fable-5.1-Max-CLEANED", ["Fable-5.1-Max-CLEANED"]),
    ("aemmeath/NasledieLab-Qwen3.5-0.8B-GPT-6-Astra-Luna-Fable-5.1-Opus-5.5-distill-Karpy-GGUF", ["Astra-Luna", "Karpy"]),
    ("xoykor/Ornith-1.5-9B-DSH-Agentic-GPT-5.6-Sol-Distill", ["Ornith", "Ornith-1.5-9B"]),
    ("oroboros-labs/gpt-5.6-sol", ["gpt-5.6-sol"]),
    ("Achilles1089/fable-coder-35B-A3B-GGUF (duplicado)", ["fable-coder"]),
    ("mondk/GGUF.Claude-Qwen3.5-V2", ["Claude-Qwen3.5-V2", "GGUF.Claude-Qwen3.5"])
]

# Scan files in dirs
found_files = []
for d in SEARCH_DIRS:
    if d.exists():
        try:
            for item in d.glob("*"):
                if item.is_file():
                    found_files.append((item.name, item.stat().st_size, item))
        except Exception as e:
            pass

print("=" * 80)
print("   RELATORIO MINUCIOSO DE AUDITORIA: 23 MODELOS SOLICITADOS")
print("=" * 80)

for idx, (label, patterns) in enumerate(REQUESTED_ITEMS, 1):
    matches = []
    for fn, sz, path in found_files:
        if any(p.lower() in fn.lower() for p in patterns):
            matches.append((fn, sz, path))
    
    print(f"\n[{idx:02d}] {label}")
    if matches:
        for fn, sz, p in matches:
            sz_gb = round(sz / (1024**3), 2)
            status = "PRONTO (COMPLETO)" if sz > 100_000_000 else "PARCIAL / INCOMPLETO"
            print(f"     -> {status}: {fn} ({sz_gb} GB) em {p.parent}")
    else:
        print("     -> NAO ENCONTRADO / PENDENTE DE DOWNLOAD")
