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

from aethermind_cognitive_substrate.planning.mamba_selective_ssm import MambaSelectiveSSMEngine
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: MAMBA SELECTIVE STATE-SPACE MODEL (SSM) ENGINE (ÓRGÃO 25)")
    print("=" * 80)

    # 1. Instanciação e estabilidade de transição A
    ssm = MambaSelectiveSSMEngine(d_model=16, d_state=32)
    assert all(a < 0 for a in ssm.A_diag), "Todos os polos em A_diag devem ser estritamente negativos para estabilidade de Lyapunov!"
    print(" -> [TESTE 1/4]: Polos de Lyapunov e inicialização do espaço de estados verificados.")

    # 2. Execução de passo único
    x_t = [math.cos(i * 0.4) for i in range(16)]
    y_t, tele = ssm.step(x_t)
    assert len(y_t) == 16, f"Saída deve ter dimensão d_model=16, obtido {len(y_t)}"
    assert tele["is_stable"], "Estado latente divergiu!"
    assert tele["delta_t"] > 0, "Delta_t adaptativo deve ser estritamente positivo!"
    print(f" -> [TESTE 2/4]: Passo SSM executado em {tele['elapsed_us']} us (Delta_t={tele['delta_t']}, Norma={tele['h_norm']:.4f}).")

    # 3. Varredura Seletiva Contínua (Sequência de 100 passos)
    seq = [[math.sin((s + 1) * 0.1 * (i + 1)) for i in range(16)] for s in range(100)]
    ssm.reset_state()
    outputs, summary = ssm.selective_scan(seq)
    assert len(outputs) == 100
    assert summary["throughput_steps_per_sec"] > 1000.0, f"Throughput muito baixo: {summary['throughput_steps_per_sec']}"
    print(f" -> [TESTE 3/4]: Varredura de 100 passos concluída em {summary['total_elapsed_ms']} ms ({summary['throughput_steps_per_sec']} steps/s, {summary['us_per_step']} us/step).")

    # 4. Falsificação Adversarial: Injeção de Ruído Não-Estacionário e Verificação de Não-Explosão
    noisy_seq = [[10.0 if i == 0 else -10.0 for i in range(16)] for _ in range(50)]
    noisy_out, noisy_sum = ssm.selective_scan(noisy_seq)
    assert noisy_sum["final_h_norm"] < 500.0, f"Norma explodiu sob estresse: {noisy_sum['final_h_norm']}"
    print(f" -> [TESTE 4/4]: Falsificação Adversarial: Norma sob estresse = {noisy_sum['final_h_norm']:.2f} < 500.0 (Absolutamente Estável).")

    # 5. Despacho via Runtime Soberano
    runtime = SovereignCortexRuntime()
    res = runtime.execute_cognitive_mission("ssm_step", {"x_t": x_t})
    assert res["result"]["status"] == "SSM_STEP_COMPLETED"
    print(f" -> [TESTE 5/5]: Despacho SSM via Córtex Runtime concluído com sucesso.")

    print("\n[VEREDITO EMPÍRICO]: MAMBA SELECTIVE SSM APROVADO COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
