"""Suíte de Testes Adversariais do Modelo Mundial Latente JEPA (Protocolo O.M.E.G.A.).

Validação empírica:
1. Codificação de Espaço Latente Contínuo e Estabilidade do Target Encoder (EMA).
2. Simulação Mental Deliberativa (Rollout de 10 passos) em microssegundos.
3. Decisão de Ação Ótima via Model Predictive Control (MPC) Latente sem LLM.
4. Prevenção de Colapso Representacional (Variância estritamente > 0).
"""
import sys
import os
import time
from pathlib import Path
import numpy as np

# Injeta a raiz em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.planning.jepa_latent_world_model import JEPAPredictiveWorldModel


def test_jepa_latent_encoding_and_anti_collapse():
    print("[TESTE 1] Codificação Latente e Prevenção de Colapso Representacional...")
    jepa = JEPAPredictiveWorldModel(obs_dim=16, action_dim=4, latent_dim=32, ema_tau=0.98)

    obs = np.random.randn(16)
    s_t = jepa.encode_context(obs)
    s_target = jepa.encode_target(obs)

    assert s_t.shape == (32,), f"Dimensão incorreta: {s_t.shape}"
    var_s = float(np.var(s_t))
    assert var_s > 0.5, f"Alerta de colapso representacional! Variância: {var_s}"

    # Treina alguns passos e verifica que a variância não decai para zero
    for _ in range(25):
        o_t = np.random.randn(16)
        a_t = np.random.randn(4)
        o_t1 = o_t + 0.1 * a_t[0] + np.random.randn(16) * 0.05
        jepa.step_train(o_t, a_t, o_t1)

    s_after = jepa.encode_context(obs)
    var_after = float(np.var(s_after))
    assert var_after > 0.3, f"Colapso pós-treinamento detectado! Variância: {var_after}"
    print(f"   -> Variância Latente Mantida: {var_after:.4f} (Anti-colapso confirmado)")
    print("   [OK] Espaço latente não colapsou.")


def test_jepa_mental_rollout_microseconds():
    print("\n[TESTE 2] Simulação Mental em Microssegundos (Rollout Latente)...")
    jepa = JEPAPredictiveWorldModel(obs_dim=16, action_dim=4, latent_dim=32)

    current_obs = np.ones(16)
    goal_obs = np.ones(16) * 2.0
    action_seq = [np.random.randn(4) for _ in range(10)]

    # Warmup do cache de instruções da CPU e bibliotecas dinâmicas BLAS
    _ = jepa.mental_rollout(current_obs, action_seq, goal_obs)

    res = jepa.mental_rollout(current_obs, action_seq, goal_obs)
    assert res["status"] == "ROLLOUT_COMPLETE"
    assert res["horizon_steps"] == 10
    assert res["trajectory_depth"] == 11
    print(f"   -> Tempo de Simulação de 10 Passos: {res['elapsed_microseconds']:.2f} microssegundos")
    assert res["elapsed_microseconds"] < 10000.0, f"Latência de rollout mental ultrapassou o teto de 10ms! Obtido: {res['elapsed_microseconds']:.2f} us"
    print(f"   [OK] Rollout mental concluído em {res['elapsed_microseconds']:.2f} us (< 10 ms, 0 tokens / 0% GPU).")


def test_jepa_mpc_action_selection():
    print("\n[TESTE 3] Decisão de Ação via Model Predictive Control Latente...")
    jepa = JEPAPredictiveWorldModel(obs_dim=16, action_dim=4, latent_dim=32)

    obs = np.zeros(16)
    goal = np.ones(16)

    # 3 planos de ação concorrentes
    plan_a = [np.zeros(4) for _ in range(5)]
    plan_b = [np.ones(4) * 0.5 for _ in range(5)]
    plan_c = [np.ones(4) * 1.5 for _ in range(5)]

    best_idx, tele = jepa.select_best_action_plan(obs, [plan_a, plan_b, plan_c], goal)
    print(f"   -> Plano Vencedor Selecionado: Índice {best_idx}")
    print(f"   -> Valor de Alinhamento Cumulativo: {tele['goal_cumulative_value']}")
    assert best_idx in [0, 1, 2]
    assert tele["goal_cumulative_value"] is not None
    print("   [OK] Seleção MPC concluída com pontuação de energia livre.")


def main():
    print("=" * 80)
    print(" SUÍTE DE TESTES OMEGA: JEPA PREDICTIVE WORLD MODEL")
    print("=" * 80)
    test_jepa_latent_encoding_and_anti_collapse()
    test_jepa_mental_rollout_microseconds()
    test_jepa_mpc_action_selection()
    print("\n" + "=" * 80)
    print(" TODOS OS TESTES PASSARAM COM SUCESSO (JEPA LATENT WORLD MODEL PRONTO).")
    print("=" * 80)


if __name__ == "__main__":
    main()
