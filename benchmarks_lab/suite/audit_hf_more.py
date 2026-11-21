import urllib.request
import json
import ssl

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

repos = [
    "TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill-GGUF",
    "yuxinlu1/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF",
    "mradermacher/Grok-3-reasoning-gemma3-4B-distilled-HF-GGUF"
]

for r in repos:
    url = f"https://huggingface.co/api/models/{r}/tree/main"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
            files = json.loads(resp.read().decode("utf-8"))
            ggufs = [f for f in files if f.get("path", "").endswith(".gguf")]
            print(f"\n--- {r} ---")
            for g in ggufs:
                sz = g.get("size", 0) / (1024**3)
                print(f"  * {g.get('path')} ({sz:.2f} GB)")
    except Exception as e:
        print(f"{r} error: {e}")
