import sys
import os
from pathlib import Path
import numpy as np

# Injeta a raiz do repositório em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: CAUSAL MPC-CBF CONTROLLER & GATED TELEMETRY STREAM (ÓRGÃO 31)")
    print("=" * 80)

    runtime = SovereignCortexRuntime()

    # 1. Verificação de Saúde do Córtex v4.1.0 (31 Órgãos)
    health = runtime.get_system_health()
    assert health["organs_active_count"] >= 31, f"Esperado >= 31 órgãos, obtido {health['organs_active_count']}"
    assert health["causal_mpc_cbf_active"] is True
    print(f" -> [TESTE 1/4]: Córtex v4.1.0 ({health['organs_active_count']} Órgãos) inicializado.")

    # 2. Gatekeeper Obrigatório CBF-QP no Pipeline Streaming
    stream_res = runtime.execute_cognitive_mission("telemetry_stream_ingest", {})
    s_data = stream_res["result"]
    assert "cbf_safety_certification" in s_data, "Stream deve conter certificação CBF-QP obrigatória!"
    assert s_data["cbf_safety_certification"]["is_formally_safe"] is True
    print(f" -> [TESTE 2/4]: Gatekeeper CBF-QP no Stream validado (Safe={s_data['cbf_safety_certification']['is_formally_safe']}, Elapsed={s_data['pipeline_elapsed_ms']} ms).")

    # 3. Planejamento Causal MPC-CBF no Espaço Latente JEPA (Ações Seguras)
    obs = np.zeros(16)
    goal = np.ones(16) * 0.5
    safe_plans = [
        [np.array([0.05, 0.05, 0.05, 0.05]), np.array([0.02, 0.02, 0.02, 0.02])],
        [np.array([-0.1, -0.1, -0.1, -0.1]), np.array([-0.05, -0.05, -0.05, -0.05])]
    ]
    mpc_res = runtime.execute_cognitive_mission("causal_mpc_cbf", {
        "current_obs": obs.tolist(),
        "goal_obs": goal.tolist(),
        "candidate_plans": [[a.tolist() for a in p] for p in safe_plans],
        "system_state_4d": [0.40, 0.40, 0.40, 0.70]
    })
    r_mpc = mpc_res["result"]
    assert r_mpc["status"] == "CAUSAL_MPC_PLAN_CERTIFIED"
    assert r_mpc["all_steps_formally_safe"] is True
    print(f" -> [TESTE 3/4]: Causal MPC-CBF selecionou plano #{r_mpc['best_plan_index']} em {r_mpc['elapsed_ms']} ms (Todos os passos seguros={r_mpc['all_steps_formally_safe']}).")

    # 4. Falsificação Adversarial: Plano Vencedor com Ação Agressiva perto da Barreira
    aggressive_plans = [
        [np.array([1.80, 1.50, 1.20, 0.80]), np.array([1.20, 1.20, 1.00, 0.50])]
    ]
    adv_res = runtime.execute_cognitive_mission("causal_mpc_cbf", {
        "current_obs": obs.tolist(),
        "goal_obs": goal.tolist(),
        "candidate_plans": [[a.tolist() for a in p] for p in aggressive_plans],
        "system_state_4d": [0.89, 0.86, 0.81, 0.91]
    })
    r_adv = adv_res["result"]
    assert r_adv["cbf_intervened"] is True, "CBF deve intervir em plano agressivo próximo à barreira!"
    assert r_adv["all_steps_formally_safe"] is True, "Mesmo sob ataque, trajetória certificada deve ser segura!"
    print(f" -> [TESTE 4/4]: Falsificação Adversarial: Plano agressivo interceptado (Intervenção={r_adv['cbf_intervened']}, Seguro={r_adv['all_steps_formally_safe']}).")

    print("\n[VEREDITO EMPÍRICO]: CAUSAL MPC-CBF & GATED STREAM PIPELINE APROVADOS COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
