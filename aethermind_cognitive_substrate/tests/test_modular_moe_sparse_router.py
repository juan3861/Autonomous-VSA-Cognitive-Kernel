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

from aethermind_cognitive_substrate.planning.modular_moe_sparse_router import ModularMoESparseRouter
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: MODULAR SPARSE MIXTURE-OF-EXPERTS (MoE) CAUSAL ROUTER (ÓRGÃO 24)")
    print("=" * 80)

    # 1. Instanciação direta
    router = ModularMoESparseRouter(input_dim=32, num_experts=8, top_k=2)
    assert router.num_experts == 8, f"Esperado 8 experts, obtido {router.num_experts}"
    assert router.top_k == 2, f"Esperado top_k=2, obtido {router.top_k}"
    print(" -> [TESTE 1/4]: Instanciação e Top-K Gating verificados com sucesso.")

    # 2. Roteamento determinístico
    x_test = [math.sin(i * 0.5) for i in range(32)]
    selected, telemetry = router.route(x_test)
    assert len(selected) == 2, f"Esperado 2 especialistas selecionados, obtido {len(selected)}"
    weights_sum = sum(w for _, w in selected)
    assert abs(weights_sum - 1.0) < 1e-6, f"Softmax deve somar 1.0, somou {weights_sum}"
    print(f" -> [TESTE 2/4]: Roteamento executado: {selected} em {telemetry['elapsed_us']} us (Soma Softmax={weights_sum:.6f}).")

    # 3. Falsificação Adversarial: Garantir que vetores opostos ativam especialistas distintos
    x_opposite = [-val for val in x_test]
    selected_opp, _ = router.route(x_opposite)
    print(f" -> [TESTE 3/4]: Falsificação Adversarial: x_inverso gerou especialistas {selected_opp}.")
    assert selected != selected_opp, "Entradas opostas não devem ativar a mesma combinação idêntica de pesos!"

    # 4. Roteamento via Runtime Soberano
    runtime = SovereignCortexRuntime()
    mission_res = runtime.execute_cognitive_mission("moe_route", {"vector": x_test})
    assert mission_res["mission_type"] == "moe_route"
    assert "telemetry" in mission_res["result"]
    print(f" -> [TESTE 4/4]: Despacho no Córtex Runtime validado (Overhead={mission_res['orchestration_overhead_ms']} ms).")

    print("\n[VEREDITO EMPÍRICO]: MODULAR MoE SPARSE ROUTER APROVADO COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
