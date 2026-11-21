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
    "yuxinlu1/gemma-4-12B-it-Claude-4.6-4.8-Opus-GGUF",
    "Mia-AiLab/Gemmable-4-12B-MTP-GGUF",
    "deadbydawn101/gemma-4-E4B-Agentic-Opus-Reasoning-GeminiCLI-GGUF",
    "TeichAI/gemma-4-26B-A4B-it-Claude-Opus-Distill-GGUF",
    "mradermacher/IBM-Grok4-UltraFast-Coder-1B-GGUF",
    "IntelligentEstate/Baby_Grok3-1.5b-iQ4_K_M-GGUF",
    "TeichAI/Qwen3-4B-Instruct-grok-4-fast-brainstorming-distill",
    "mradermacher/Grok-3-reasoning-gemma3-4B-distilled-HF-GGUF",
    "mradermacher/Grok-3-reasoning-gemma3-12B-distilled-HF-GGUF",
    "NVIDIA-Nemotron-Labs-Dory1.0-4B",
    "google/gemma-4-12B-it",
    "google/gemma-3-4b-it",
    "google/gemma-3-12b-it",
    "unsloth/gemma-3-4b-it-GGUF",
    "mradermacher/Qwen3.5-9B-Kimi-k3-Distilled-GGUF",
    "CreitinGameplays/Llama-3.2-3B-Fable-5-Distill"
]

print(f"Auditando {len(repos)} repositórios no Hugging Face API...")
for r in repos:
    url = f"https://huggingface.co/api/models/{r}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=5, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            m_id = data.get("id", r)
            dl = data.get("downloads", 0)
            likes = data.get("likes", 0)
            print(f"[FOUND] {m_id} | Downloads: {dl} | Likes: {likes}")
    except urllib.error.HTTPError as e:
        print(f"[NOT FOUND HTTP {e.code}] {r}")
    except Exception as e:
        print(f"[ERROR] {r}: {e}")
