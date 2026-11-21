import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

repos = [
    "ProCreations/Dory-Beam-4B-GGUF",
    "yuxinlu1/gemma-4-12B-agentic-fable5-composer2.5-v2-3.5x-tau2-GGUF",
    "yuxinlu1/gemma-4-12B-coder-fable5-composer2.5-v1-GGUF",
    "Mia-AiLab/Gemmable-4-12B-MTP-GGUF",
    "deadbydawn101/gemma-4-E4B-Agentic-Opus-Reasoning-GeminiCLI-GGUF",
    "mradermacher/IBM-Grok4-UltraFast-Coder-1B-GGUF",
    "IntelligentEstate/Baby_Grok3-1.5b-iQ4_K_M-GGUF"
]

print("=== LISTAGEM DE ARQUIVOS GGUF DISPONÍVEIS ===")
for r in repos:
    url = f"https://huggingface.co/api/models/{r}/tree/main"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            files = json.loads(resp.read().decode("utf-8"))
            ggufs = [f for f in files if f.get("path", "").endswith(".gguf")]
            print(f"\n--- {r} ---")
            for g in ggufs:
                size_gb = g.get("size", 0) / (1024**3)
                print(f"  * {g.get('path')} ({size_gb:.2f} GB)")
    except Exception as e:
        print(f"\n--- {r} --- Erro: {e}")
