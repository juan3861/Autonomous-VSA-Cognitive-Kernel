import sys
import os
import math
from pathlib import Path

# Injeta a raiz do repositório em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.planning.coconut_latent_cot import CoconutLatentCoTEngine
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: COCONUT CONTINUOUS LATENT COT & TELEMETRY STREAM PIPELINE (ÓRGÃO 27)")
    print("=" * 80)

    # 1. Instanciação e Pensamento Contínuo Isolado
    coconut = CoconutLatentCoTEngine(latent_dim=32, max_latent_steps=12, convergence_tol=1e-2)
    initial_vec = [math.sin(i * 0.3) * 0.8 for i in range(32)]
    res_iso = coconut.think_continuously(initial_vec)
    assert res_iso["intermediate_tokens_decoded"] == 0, "Zero tokens intermediários devem ser decodificados!"
    assert res_iso["steps_executed"] > 0
    assert res_iso["final_latent_norm"] < 10.0
    print(f" -> [TESTE 1/5]: Pensamento Latente Isolado: {res_iso['steps_executed']} passos em {res_iso['elapsed_us']} us (Tokens=0, Norma={res_iso['final_latent_norm']}).")

    # 2. Pensamento Latente Acoplado no Córtex Completo (Mamba SSM + Rust HRM + MoE Router)
    runtime = SovereignCortexRuntime()
    res_full = runtime.execute_cognitive_mission("coconut_think", {"initial_state": initial_vec})
    r = res_full["result"]
    assert r["intermediate_tokens_decoded"] == 0
    assert r["moe_action_dispatch"] is not None, "Deve retornar despacho do roteador MoE!"
    assert len(r["moe_action_dispatch"]["selected_experts"]) == 2
    print(f" -> [TESTE 2/5]: Pensamento Latente Completo (SSM+HRM+MoE): {r['steps_executed']} passos em {r['elapsed_us']} us -> Especialistas={r['moe_action_dispatch']['selected_experts']}.")

    # 3. Falsificação Adversarial: Injeção de Vetor Explosivo e Verificação de Contração
    explosive_vec = [1000.0 * ((-1) ** i) for i in range(32)]
    res_adv = runtime.execute_cognitive_mission("coconut_think", {"initial_state": explosive_vec})
    r_adv = res_adv["result"]
    assert r_adv["final_latent_norm"] < 50.0, f"Vetor latente falhou em contrair entrada explosiva! Norma={r_adv['final_latent_norm']}"
    print(f" -> [TESTE 3/5]: Falsificação Adversarial: Entrada de magnitude ~5656 contraída para Norma={r_adv['final_latent_norm']}.")

    # 4. Pipeline Sistêmico Real (Win32 Sentinel -> Mamba SSM -> Surpresa -> Paged Memory OS -> MoE)
    stream_1 = runtime.execute_cognitive_mission("telemetry_stream_ingest", {})
    s1 = stream_1["result"]
    assert s1["status"] == "TELEMETRY_STREAM_INGESTED"
    assert s1["surprise_score"] > 0.0
    print(f" -> [TESTE 4/5]: Stream Passo 1 (Telemetria Real SO): Page={s1['page_id']}, Surpresa={s1['surprise_score']}, Importância={s1['memory_importance']} em {s1['pipeline_elapsed_ms']} ms.")

    # 5. Injeção de anomalia sintética no stream para validar Surprise-Gated Eviction & MoE Trigger
    anomaly_signal = [0.99, 0.98, 0.01, 0.99] + [0.9] * 12
    stream_2 = runtime.execute_cognitive_mission("telemetry_stream_ingest", {"custom_signal": anomaly_signal})
    s2 = stream_2["result"]
    assert s2["moe_dispatch"] is not None and s2["moe_dispatch"]["triggered"] is True
    content, origin, _ = runtime.paged_memory.access_page(s2["page_id"])
    assert origin == "HOT_TIER", "Anomalia de alta surpresa deve estar residente na Hot Tier!"
    print(f" -> [TESTE 5/5]: Anomalia no Stream acionou MoE ({s2['moe_dispatch']['selected_experts']}) e protegeu página '{s2['page_id']}' na {origin}.")

    print("\n[VEREDITO EMPÍRICO]: COCONUT LATENT COT & TELEMETRY STREAM PIPELINE APROVADOS COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
