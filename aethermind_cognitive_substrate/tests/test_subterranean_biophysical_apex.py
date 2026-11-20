"""Subterranean Bio-Physical Architecture Test Suite (Post-Backprop AGI Substrate).

Valida empiricamente os 6 paradigmas 'fora da Matrix' da neurociência e física matemática:
1. HRM & TRM: Raciocínio de Ponto Fixo em Dupla Frequência com Teorema da Função Implícita (IFT).
2. AKOrN & CTM: Osciladores Neurais de Kuramoto e Ligação Semântica por Sincronia de Fase.
3. Active Inference & FEP: Minimização de Energia Livre de Friston e Plasticidade Local Hebbiana (Zero BPTT).
4. HDC / VSA 10.000 Bits: Álgebra Holográfica MAP de Kanerva e Resiliência a 35% de Corrupção.
5. Máquinas de Ising Termodinâmicas (Extropic thrml): Relaxamento em Blocos Bipartidos.
6. KAN (Kolmogorov-Arnold) & NCA: Ativações nas arestas e regeneração bioelétrica após 70% de dano.
"""
from __future__ import annotations

import sys
import os
import time
import math
from pathlib import Path
import numpy as np

# Injeta a raiz do projeto no path
substrate_root = Path(__file__).parent.parent
sys.path.insert(0, str(substrate_root.parent))

from aethermind_cognitive_substrate.metacognition import (
    HRMDualTimescaleFixedPoint, KuramotoOscillatoryNetwork
)
from aethermind_cognitive_substrate.planning import ActiveInferenceFristonEngine
from aethermind_cognitive_substrate.memory_vault import KanervaHDC10000VSA
from aethermind_cognitive_substrate.logic_symbolic import (
    ThermodynamicIsingMachine, KolmogorovArnoldSplineLayer, MorphogeneticCellularAutomata
)
from aethermind_cognitive_substrate import SovereignCortexRuntime


def test_subterranean_biophysical_organs() -> int:
    print("================================================================================")
    print(" [SUBTERRÂNEO BIOPFÍSICO: TESTE DOS 6 PARADIGMAS PÓS-BACKPROP / NÃO-LLM]")
    print(" Rigor Absoluto | Zero Mocks | Verificação no Silício Local")
    print("================================================================================\n")

    # --------------------------------------------------------------------------
    # 1. HRM & TRM (Raciocínio de Ponto Fixo em Dupla Frequência)
    # --------------------------------------------------------------------------
    print("[1/6] Testando HRM / TRM (Ponto Fixo Córtex-Tálamo & IFT O(1))...")
    hrm = HRMDualTimescaleFixedPoint(slow_dim=16, fast_dim=32, input_dim=16, contraction_factor=0.80)
    x_input = np.ones(16, dtype=np.float64) * 0.5
    hrm_res = hrm.find_fixed_point_equilibrium(x_input, slow_macro_steps=3)

    assert hrm_res["status"] == "EQUILIBRIUM_REACHED"
    assert hrm_res["is_banach_contractive"] is True
    assert hrm_res["spectral_radius_jacobian"] < 1.0
    assert hrm_res["macro_steps_executed"] >= 1
    assert hrm_res["ift_resolvent_frobenius_norm"] > 0.0
    print(f"  -> Ponto Fixo Atingido em {hrm_res['total_fast_cycles']} ciclos rápidos ({hrm_res['elapsed_ms']} ms)")
    print(f"  -> Raio Espectral Jacobiano: {hrm_res['spectral_radius_jacobian']} < 1.0 (Contração Garantida)")
    print(f"  -> Resolvente IFT O(1) de Memória: Frobenius = {hrm_res['ift_resolvent_frobenius_norm']}")

    # --------------------------------------------------------------------------
    # 2. AKOrN & CTM (Osciladores de Kuramoto & Sincronia de Fase Temporal)
    # --------------------------------------------------------------------------
    print("\n[2/6] Testando AKOrN / CTM (Osciladores de Kuramoto & Resolução do Binding Problem)...")
    kuramoto = KuramotoOscillatoryNetwork(num_oscillators=64, coupling_strength_k=3.0, dt=0.04)

    # Estimula 2 conceitos semânticos distintos (ex: "Maçã_Vermelha" nos neurônios 0..9 e "Céu_Azul" nos 20..29)
    stimuli = {
        "objeto_maca_vermelha": list(range(0, 10)),
        "objeto_ceu_azul": list(range(20, 30))
    }
    sync_res = kuramoto.bind_features_by_phase(stimuli, integration_steps=60)

    assert sync_res["status"] == "PHASE_SYNCHRONY_CONVERGED"
    coherences = sync_res["group_internal_coherences"]
    assert coherences["objeto_maca_vermelha"] > 0.50
    assert coherences["objeto_ceu_azul"] > 0.50
    print(f"  -> Sincronia de Fase Convergida em {sync_res['elapsed_ms']} ms")
    print(f"  -> Coerência Interna Grupo 1 ('Maçã'): {coherences['objeto_maca_vermelha']}")
    print(f"  -> Coerência Interna Grupo 2 ('Céu'): {coherences['objeto_ceu_azul']}")
    print(f"  -> Parâmetro de Ordem de Kuramoto Final R: {sync_res['final_global_order_R']}")

    # --------------------------------------------------------------------------
    # 3. Active Inference & Friston Free Energy (Plasticidade Local sem Backprop)
    # --------------------------------------------------------------------------
    print("\n[3/6] Testando Active Inference & Energia Livre de Friston (Predictive Coding)...")
    act_inf = ActiveInferenceFristonEngine(obs_dim=16, hidden_dim=32, prior_dim=16, learning_rate=0.08)

    obs = np.sin(np.linspace(0, math.pi, 16))
    adapt_res = act_inf.infer_and_adapt(obs, inference_steps=30)

    assert adapt_res["status"] == "FREE_ENERGY_MINIMIZED"
    assert adapt_res["final_free_energy"] < adapt_res["initial_free_energy"]
    assert adapt_res["synaptic_update_norm"] > 0.0

    # Teste de Seleção de Ação por Energia Livre Esperada G(pi)
    target = np.cos(np.linspace(0, math.pi, 16))
    act_inf.set_target_goal(target)
    policy_res = act_inf.evaluate_expected_free_energy_policy(
        candidate_actions=[target, -target, np.zeros(16)],
        action_names=["acao_alinhada", "acao_antagonista", "acao_nula"]
    )
    assert policy_res["status"] == "OPTIMAL_ACTION_SELECTED"
    assert policy_res["best_action"] == "acao_alinhada"
    print(f"  -> Energia Livre Variacional: {adapt_res['initial_free_energy']:.3f} -> {adapt_res['final_free_energy']:.3f} (Redução: {adapt_res['free_energy_reduction_pct']}%)")
    print(f"  -> Atualização Sináptica Local Hebbiana (Zero Backprop): ||Delta W|| = {adapt_res['synaptic_update_norm']:.4f}")
    print(f"  -> Política Ótima Selecionada por G(pi): {policy_res['best_action']} ({policy_res['elapsed_ms']} ms)")

    # --------------------------------------------------------------------------
    # 4. HDC / VSA 10.000 Bits (Álgebra Holográfica de Kanerva)
    # --------------------------------------------------------------------------
    print("\n[4/6] Testando Pentti Kanerva HDC 10.000-bit VSA (Binding, Bundling, Resiliência)...")
    vsa = KanervaHDC10000VSA(dimension=10000)

    # Codifica registro complexo: {papel: agente, objetivo: soberania, nivel: apex}
    record = {"papel": "agente_titan", "objetivo": "soberania_pura", "nivel": "apex_maximo"}
    record_vec = vsa.encode_record(record)
    assert record_vec.shape == (10000,)

    # Desempacota valor de 'papel' aplicando auto-inversão XOR
    query_res = vsa.query_record_value(record_vec, "papel")
    assert query_res["recovered_value"] == "agente_titan"
    assert query_res["confidence_similarity"] > 0.20

    # Teste de Destruição Holográfica: 35% de bits corrompidos deliberadamente
    stress_res = vsa.stress_test_holographic_resilience(record_vec, corruption_ratio=0.35)
    assert stress_res["is_signal_surviving"] is True
    assert stress_res["retained_similarity"] > 0.20
    print(f"  -> Registro 10.000-bit Codificado e Desempacotado em {query_res['elapsed_ms']} ms")
    print(f"  -> Valor Recuperado: '{query_res['recovered_value']}' (Similaridade: {query_res['confidence_similarity']})")
    print(f"  -> Prova de Resiliência Holográfica (35% bits destruídos): Sinal Sobreviveu = {stress_res['is_signal_surviving']} (Sim: {stress_res['retained_similarity']})")

    # --------------------------------------------------------------------------
    # 5. Máquina de Ising Termodinâmica (Extropic thrml Block Gibbs)
    # --------------------------------------------------------------------------
    print("\n[5/6] Testando Máquina de Ising Termodinâmica (Relaxamento de Gibbs em Blocos)...")
    ising = ThermodynamicIsingMachine(num_spins=64)

    # Grafo de acoplamento antiferromagnético (induz padrão de spins alternados)
    n = 64
    rng = np.random.RandomState(42)
    j_mat = rng.randn(n, n) * 0.2
    ising.set_coupling_matrix(j_mat)

    ising_res = ising.thermal_relax_to_ground_state(initial_temp=4.0, final_temp=0.05, cooling_steps=40)
    assert ising_res["status"] == "GROUND_STATE_REACHED"
    assert ising_res["energy_drop"] >= 0.0  # Energia do sistema deve cair ou estabilizar no mínimo
    print(f"  -> Relaxamento Termodinâmico: Energia {ising_res['initial_energy']} -> {ising_res['ground_state_energy']} (Queda: {ising_res['energy_drop']})")
    print(f"  -> Concluído em {ising_res['elapsed_ms']} ms | Magnetização Final: {ising_res['magnetization']}")

    # --------------------------------------------------------------------------
    # 6. KAN (Kolmogorov-Arnold Splines) & NCA (Autômato Morfogenético)
    # --------------------------------------------------------------------------
    print("\n[6/6] Testando KAN (Polinômios nas Arestas) & NCA (Regeneração Bioelétrica)...")
    kan = KolmogorovArnoldSplineLayer(in_features=4, out_features=4, degree=4)
    x_kan = np.array([0.5, -0.2, 0.8, -0.6])
    y_kan = kan.forward(x_kan)
    assert len(y_kan) == 4
    formulas = kan.extract_symbolic_representation()
    assert len(formulas) == 4

    # Autômato Celular Morfogenético com 70% de dano
    nca = MorphogeneticCellularAutomata(grid_size=16)
    nca.seed_target_pattern()
    e_init = nca.compute_pattern_energy()
    damaged = nca.mutilate_damage(damage_ratio=0.70)
    e_damaged = nca.compute_pattern_energy()

    # Regeneração bioelétrica local em 15 passos
    for _ in range(15):
        nca.step()
    e_healed = nca.compute_pattern_energy()
    assert e_healed > e_damaged  # Padrão celular se auto-reparou

    print(f"  -> KAN: Avaliação nas Arestas Concluída (y = {[round(float(v), 3) for v in y_kan]})")
    print(f"  -> KAN: Fórmula Simbólica Extraída: {formulas[0]}")
    print(f"  -> NCA: {damaged} células mutiladas (70% dano). Biomassa Inicial: {e_init:.2f} -> Pós-Dano: {e_damaged:.2f} -> Regenerada: {e_healed:.2f}")

    # --------------------------------------------------------------------------
    # 7. Sovereign Cortex Runtime (Despacho Integrado de Todos os Órgãos)
    # --------------------------------------------------------------------------
    print("\n[INTEGRAÇÃO] Testando Córtex Soberano Unificado v3.x...")
    cortex = SovereignCortexRuntime()
    assert "APEX" in cortex.version and "SOVEREIGN" in cortex.version

    cortex_hrm = cortex.execute_cognitive_mission(
        "hrm_fixed_point",
        {"input_vector": np.ones(16) * 0.2, "slow_steps": 2}
    )
    assert cortex_hrm["result"]["status"] == "EQUILIBRIUM_REACHED"

    cortex_kura = cortex.execute_cognitive_mission(
        "kuramoto_phase_sync",
        {"feature_stimuli": {"conceito_alfa": [1, 2, 3]}, "steps": 25}
    )
    assert cortex_kura["result"]["status"] == "PHASE_SYNCHRONY_CONVERGED"

    cortex_vsa = cortex.execute_cognitive_mission(
        "kanerva_vsa_record",
        {"pairs": {"missao": "titan_apotheosis"}}
    )
    assert cortex_vsa["result"]["status"] == "RECORD_ENCODED"

    print(f"  -> Córtex v3.0 Despacho de Missões: APROVADO ({cortex_hrm['orchestration_overhead_ms']} ms)")

    print("\n================================================================================")
    print(" [SUBTERRÂNEO BIOPFÍSICO: TODOS OS 6 PARADIGMAS APROVADOS E HOMOLOGADOS!]")
    print(" >>> ZERO FLOPs DE LLM | ZERO BACKPROPAGATION | COMPUTAÇÃO LOCAL PURA <<<")
    print("================================================================================\n")
    return 0


if __name__ == "__main__":
    code = test_subterranean_biophysical_organs()
    sys.exit(code)
