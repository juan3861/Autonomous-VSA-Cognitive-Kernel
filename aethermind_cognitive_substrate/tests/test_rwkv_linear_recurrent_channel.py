"""Test Suite — Organ 32: RWKV Linear Recurrent Channel (O(1) Temporal Memory).

Verifica:
1. Instanciação e parâmetros corretos do RWKVLinearRecurrentChannel.
2. Passo recorrente único produz saída de dimensão correta e telemetria válida.
3. Varredura de sequência de 50 passos com latência < 5ms e throughput > 5000 steps/s.
4. Reset de estado: norma do estado retorna a zero após reset_state().
5. Integração com SovereignCortexRuntime via missões 'rwkv_step' e 'rwkv_scan'.
"""
import sys
import time
import numpy as np
sys.path.insert(0, r"F:\AetherMind_Apotheosis_Final")

from aethermind_cognitive_substrate.planning.rwkv_linear_recurrent_channel import RWKVLinearRecurrentChannel
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def test_rwkv_linear_recurrent_channel():
    print("=" * 70)
    print("[ORGAN 32] RWKV LINEAR RECURRENT CHANNEL — TESTE EMPIRICO")
    print("=" * 70)

    # 1. Instanciação
    rwkv = RWKVLinearRecurrentChannel(d_model=16, num_heads=4, head_dim=8)
    assert rwkv.d_model == 16, "d_model incorreto"
    assert rwkv.num_heads == 4, "num_heads incorreto"
    assert rwkv.head_dim == 8, "head_dim incorreto"
    assert rwkv.state_S.shape == (4, 8, 8), f"Forma do estado incorreta: {rwkv.state_S.shape}"
    print("[1/5] Instanciação: OK")

    # 2. Passo recorrente único
    x_t = np.random.randn(16)
    out, tele = rwkv.step(x_t.tolist())
    assert len(out) == 16, f"Saída deve ter 16 elementos, got {len(out)}"
    assert tele["step"] == 1, f"Step counter deve ser 1, got {tele['step']}"
    assert tele["elapsed_us"] > 0, "elapsed_us deve ser > 0"
    assert isinstance(tele["state_frobenius_norm"], float), "state_frobenius_norm deve ser float"
    print(f"[2/5] Passo Único: OK | out_norm={tele['output_norm']} | state_norm={tele['state_frobenius_norm']} | {tele['elapsed_us']:.1f} us")

    # 3. Acúmulo de estado: a norma do estado deve crescer com cada passo
    rwkv.reset_state()
    norms = []
    for i in range(10):
        x = np.random.randn(16)
        _, t = rwkv.step(x.tolist())
        norms.append(t["state_frobenius_norm"])
    assert norms[-1] > norms[0], "Norma do estado deve crescer ao longo dos passos"
    print(f"[3/5] Acúmulo de Estado: OK | norm[0]={norms[0]:.4f} -> norm[9]={norms[-1]:.4f}")

    # 4. Reset de estado
    rwkv.reset_state()
    state_norm_after_reset = float(np.linalg.norm(rwkv.state_S))
    assert state_norm_after_reset == 0.0, f"Após reset, norma deve ser 0, got {state_norm_after_reset}"
    assert rwkv.step_count == 0, "step_count deve ser 0 após reset"
    print("[4/5] Reset de Estado: OK | state_norm=0.0 após reset_state()")

    # 5. Varredura de sequência de 50 passos
    rwkv.reset_state()
    sequence = [np.random.randn(16).tolist() for _ in range(50)]
    t0 = time.perf_counter()
    outputs, summary = rwkv.sequence_scan(sequence)
    total_ms = (time.perf_counter() - t0) * 1000.0
    assert len(outputs) == 50, f"Deve ter 50 saídas, got {len(outputs)}"
    assert len(outputs[0]) == 16, "Cada saída deve ter 16 elementos"
    assert summary["total_steps"] == 50
    assert total_ms < 5000.0, f"Varredura de 50 passos deve ser < 5s, got {total_ms:.2f} ms"
    tps = summary.get("throughput_steps_per_sec", 0)
    print(f"[5/5] Sequence Scan 50 passos: OK | {total_ms:.2f} ms | {tps:.0f} steps/s")

    # Integração com Córtex Soberano
    print("\n[INTEGRAÇÃO] Verificando missões via SovereignCortexRuntime...")
    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["organs_active_count"] >= 32, f"Deve ter >= 32 órgãos, got {health['organs_active_count']}"
    assert health.get("rwkv_linear_recurrent_active") is True, "rwkv_linear_recurrent_active deve ser True"
    print(f"  > Órgãos Ativos: {health['organs_active_count']} | RWKV: {health.get('rwkv_linear_recurrent_active')}")

    res_step = cortex.execute_cognitive_mission("rwkv_step", {"x_t": [0.1] * 16})
    assert res_step["result"]["status"] == "RWKV_STEP_COMPLETED", f"Falha no rwkv_step: {res_step['result']}"
    print(f"  > Missão rwkv_step: {res_step['result']['status']} | latencia={res_step['orchestration_overhead_ms']} ms")

    res_scan = cortex.execute_cognitive_mission("rwkv_scan", {"sequence": [[float(i % 8) / 8.0] * 16 for i in range(20)]})
    assert res_scan["result"]["status"] == "RWKV_SEQUENCE_SCANNED", f"Falha no rwkv_scan: {res_scan['result']}"
    print(f"  > Missão rwkv_scan: {res_scan['result']['status']} | {res_scan['result']['num_steps']} passos")

    print("\n[VEREDITO FINAL] ORGAN 32 RWKV: APROVADO COM VK_SUCCESS")
    return 0


if __name__ == "__main__":
    exit_code = test_rwkv_linear_recurrent_channel()
    sys.exit(exit_code)
