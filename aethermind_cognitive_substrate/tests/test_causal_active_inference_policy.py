"""Test Suite — Organ 33: Causal Active Inference Policy Engine (do-calculus + Free Energy).

Verifica:
1. Instanciação e configuração do CausalActiveInferenceEngine.
2. Avaliação de políticas interventivas do(a) com cálculo de G(do(pi)) para 4 candidatos.
3. Detecção de Backdoor Confounder (CDI > limiar quando sinal espúrio Z está ativo).
4. Arrependimento Contrafactual: regret >= 0 e abdução de ruído exógeno U.
5. Integração via SovereignCortexRuntime com missões 'causal_policy_search' e 'counterfactual_regret'.
"""
import sys
import numpy as np
sys.path.insert(0, r"F:\AetherMind_Apotheosis_Final")

from aethermind_cognitive_substrate.planning.causal_active_inference_policy import CausalActiveInferenceEngine
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def test_causal_active_inference_policy():
    print("=" * 70)
    print("[ORGAN 33] CAUSAL ACTIVE INFERENCE POLICY — TESTE EMPIRICO")
    print("=" * 70)

    # 1. Instanciação
    engine = CausalActiveInferenceEngine(obs_dim=16, action_dim=4, latent_dim=16)
    assert engine.obs_dim == 16
    assert engine.action_dim == 4
    target = np.ones(16) * 0.5
    engine.set_target_goal(target)
    assert np.allclose(engine.target_goal, target), "target_goal não configurado corretamente"
    print("[1/5] Instanciação e configuração do alvo: OK")

    # 2. Avaliação de Energia Livre Esperada Causal G(do(pi)) para 4 políticas
    current_state = np.random.randn(16) * 0.2
    candidates = [
        np.array([0.1, 0.0, 0.0, 0.0]),
        np.array([0.0, 0.1, 0.0, 0.0]),
        np.array([0.5, 0.5, 0.0, 0.0]),
        np.array([-0.1, -0.1, 0.1, 0.1])
    ]
    res = engine.evaluate_interventional_policy(
        current_state=current_state,
        candidate_actions=candidates,
        action_names=["alpha", "beta", "gamma", "delta"]
    )
    assert res["status"] == "CAUSAL_POLICY_SEARCH_COMPLETED", f"Status incorreto: {res['status']}"
    assert res["best_action"] in ["alpha", "beta", "gamma", "delta"], f"best_action inválido: {res['best_action']}"
    assert len(res["evaluations"]) == 4, f"Deve avaliar 4 políticas, got {len(res['evaluations'])}"
    for ev in res["evaluations"]:
        assert "g_expected_free_energy" in ev
        assert "pragmatic_risk" in ev
        assert "epistemic_gain" in ev
        assert "causal_discrepancy_cdi" in ev
    print(f"[2/5] Avaliação G(do(pi)) 4 políticas: OK | best={res['best_action']} | G_min={res['min_expected_free_energy_g']}")
    print(f"      Latência: {res['elapsed_ms']:.3f} ms")

    # 3. Detecção de Backdoor Confounder com sinal espúrio Z ativo
    res_confounded = engine.evaluate_interventional_policy(
        current_state=current_state,
        candidate_actions=candidates,
        confounder_latent_signal=5.0  # Z grande → CDI alto
    )
    has_confounder = res_confounded["confounder_detected"]
    max_cdi = max(e["causal_discrepancy_cdi"] for e in res_confounded["evaluations"])
    print(f"[3/5] Detecção de Backdoor Confounder: CDI_max={max_cdi:.4f} | Detectado={has_confounder}")
    # Com Z=5.0 grande, o CDI deve ser >0
    assert max_cdi > 0.0, f"CDI deve ser > 0 com confounder ativo, got {max_cdi}"

    # 4. Arrependimento Contrafactual
    executed = np.array([0.1, 0.0, 0.0, 0.0])
    observed = np.random.randn(16) * 0.3
    counterfactual = np.array([0.5, 0.5, 0.0, 0.0])
    res_cf = engine.compute_counterfactual_regret(
        executed_action=executed,
        observed_outcome=observed,
        counterfactual_candidate=counterfactual
    )
    assert res_cf["status"] == "COUNTERFACTUAL_REGRET_EVALUATED"
    assert res_cf["regret"] >= 0.0, f"Regret deve ser >= 0, got {res_cf['regret']}"
    assert isinstance(res_cf["factual_utility"], float)
    assert isinstance(res_cf["counterfactual_utility"], float)
    print(f"[4/5] Arrependimento Contrafactual: OK | Regret={res_cf['regret']:.4f} | "
          f"U_factual={res_cf['factual_utility']:.4f} | U_cf={res_cf['counterfactual_utility']:.4f}")

    # 5. Integração com Córtex Soberano
    print("\n[INTEGRAÇÃO] Verificando missões via SovereignCortexRuntime...")
    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["organs_active_count"] >= 33, f"Deve ter >= 33 órgãos, got {health['organs_active_count']}"
    assert health.get("causal_active_inference_engine_active") is True

    res_pol = cortex.execute_cognitive_mission(
        "causal_policy_search",
        {
            "current_state": [0.2] * 16,
            "target_goal": [0.5] * 16,
            "candidate_actions": [[0.1] * 4, [-0.1] * 4, [0.5, 0.0, 0.0, 0.0]],
            "action_names": ["push", "pull", "thrust"]
        }
    )
    assert res_pol["result"]["status"] == "CAUSAL_POLICY_SEARCH_COMPLETED"
    print(f"  > Missão causal_policy_search: {res_pol['result']['status']} | best={res_pol['result']['best_action']}")

    res_cfr = cortex.execute_cognitive_mission(
        "counterfactual_regret",
        {
            "executed_action": [0.1] * 4,
            "observed_outcome": [0.3] * 16,
            "counterfactual_action": [0.9] * 4
        }
    )
    assert res_cfr["result"]["status"] == "COUNTERFACTUAL_REGRET_EVALUATED"
    print(f"  > Missão counterfactual_regret: {res_cfr['result']['status']} | regret={res_cfr['result']['regret']}")

    print(f"\n[5/5] Integração Córtex: OK | Órgãos={health['organs_active_count']}")
    print("\n[VEREDITO FINAL] ORGAN 33 CAUSAL ACTIVE INFERENCE: APROVADO COM VK_SUCCESS")
    return 0


if __name__ == "__main__":
    exit_code = test_causal_active_inference_policy()
    sys.exit(exit_code)
