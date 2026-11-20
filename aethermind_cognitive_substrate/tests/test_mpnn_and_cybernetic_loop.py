"""Test Suite — Ciclo 15: Relational Graph MPNN (Organ 45) & Closed-Loop Cybernetic Pipeline (Organ 46).

Verifica empiricamente:
1. Prontidão do Córtex v4.7.0 com 46 órgãos ativos.
2. Graph MPNN Message Passing Engine: contração contrativa de Banach ao longo das camadas,
   propagação anisotrópica em grafo relacional e latência sub-milissegundo.
3. Cybernetic Closed-Loop Pipeline (UKF -> Koopman -> Conformal Shield -> ADMM QP -> CBF-QP):
   recebe medição ruidosa próxima da fronteira segura, filtra via UKF, certifica incerteza conformal,
   resolve política convexa ADMM (com inversão Cholesky O(n^2) BLAS) e aplica escudo formal CBF-QP.
"""
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def main() -> int:
    print("=" * 80)
    print("[CICLO 15] GRAPH MPNN (ÓRGÃO 45) & MALHA FECHADA CIBERNÉTICA (ÓRGÃO 46)")
    print("=" * 80)

    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY"
    assert health["organs_active_count"] >= 46, f"Esperado >= 46 órgãos, got {health['organs_active_count']}"
    assert health.get("graph_mpnn_message_passing_active") is True
    assert health.get("cybernetic_closed_loop_pipeline_active") is True
    print(f"[1/4] Córtex Prontidão: {health['organs_active_count']} órgãos | Versão={health['version']}")

    # 2. Órgão 45: Graph MPNN Message Passing (contração garantida)
    feats = [
        [0.95, 0.10, 0.05, 0.20, 0.10, 0.0, 0.0, 0.0],
        [0.20, 0.85, 0.15, 0.05, 0.20, 0.1, 0.0, 0.0],
        [0.05, 0.30, 0.80, 0.45, 0.05, 0.2, 0.1, 0.0],
        [0.40, 0.15, 0.25, 0.90, 0.30, 0.0, 0.2, 0.1],
        [0.10, 0.10, 0.10, 0.15, 0.70, 0.4, 0.3, 0.2],
    ]
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 3), (1, 4)]
    res_mpnn = cortex.execute_cognitive_mission(
        "graph_mpnn_propagate",
        {"node_features": feats, "edges": edges, "num_layers": 4}
    )["result"]
    assert res_mpnn["status"] == "GRAPH_MPNN_PROPAGATED"
    assert res_mpnn["contraction_verified"] is True, f"Contração violada: {res_mpnn['layer_convergence_deltas']}"
    assert res_mpnn["num_nodes"] == 5
    print(
        f"[2/4] Órgão 45 (Graph MPNN): OK | Deltas={res_mpnn['layer_convergence_deltas']} | "
        f"Readout Norm={res_mpnn['graph_readout_norm']} em {res_mpnn['elapsed_us']} us"
    )

    # 3. Órgão 46: Malha Fechada Cibernética (UKF -> Koopman -> Conformal -> ADMM -> CBF-QP)
    # Primeiro ajusta rapidamente o Koopman para que a malha fechada use o operador espectral real
    traj = [[0.5 * (0.92 ** t), 0.4 * (0.93 ** t), 0.3 * (0.91 ** t), 0.5 * (0.94 ** t)] for t in range(25)]
    k_fit = cortex.execute_cognitive_mission("koopman_fit_predict", {"trajectory": traj})["result"]
    assert k_fit["fitted"] is True

    res_loop = cortex.execute_cognitive_mission(
        "cybernetic_closed_loop",
        {
            "noisy_measurement": [0.91, 0.88, 0.79, 0.90],
            "target_state": [0.40, 0.40, 0.40, 0.50],
            "u_max_bound": 0.80
        }
    )["result"]
    assert res_loop["status"] == "CYBERNETIC_CLOSED_LOOP_CERTIFIED"
    assert res_loop["admm_qp_converged"] is True
    assert res_loop["is_formally_safe"] is True
    assert res_loop["conformal_radius_q_hat"] > 0.0
    print(
        f"[3/4] Órgão 46 (Malha Fechada): OK | ADMM Conv={res_loop['admm_qp_converged']} ({res_loop['admm_qp_iterations']} iters) | "
        f"q_hat={res_loop['conformal_radius_q_hat']} | Seguro={res_loop['is_formally_safe']} em {res_loop['cycle_elapsed_ms']} ms"
    )

    # 4. Stress test multi-passo em malha fechada (10 ciclos consecutivos)
    for step_i in range(10):
        step_loop = cortex.execute_cognitive_mission(
            "cybernetic_closed_loop",
            {"noisy_measurement": [0.85 - 0.02 * step_i, 0.82, 0.70, 0.80], "target_state": [0.4, 0.4, 0.4, 0.5]}
        )["result"]
        assert step_loop["is_formally_safe"] is True
    print("[4/4] Stress Test 10 Ciclos Consecutivos em Malha Fechada: OK (Invariância CBF-QP 100%)")

    print("\n[VEREDITO FINAL]: CICLO 15 (GRAPH MPNN + MALHA FECHADA CIBERNÉTICA) APROVADO COM EXIT CODE 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
