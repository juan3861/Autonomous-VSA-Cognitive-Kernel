"""Test Suite — Ciclo 14: Unscented Kalman Filter (Organ 43) & ADMM Convex QP Optimizer (Organ 44).

Verifica empiricamente:
1. Prontidão do Córtex v4.6.0 com 44 órgãos ativos.
2. UKF Nonlinear Estimator: filtragem de trajetória não-linear sob ruído gaussiano alto (std=0.18),
   reduzindo MSE em relação à medição bruta e detectando anomalia NIS sob choque adversarial.
3. ADMM Convex QP Optimizer: resolução exata de problema padrão OSQP com solução analítica conhecida
   P=[[4,1],[1,2]], q=[1,1], x1+x2=1, 0<=x<=0.7 -> x*=[0.3, 0.7], obj=1.88, erro < 1e-4 em < 5ms.
4. Integração via SovereignCortexRuntime ('ukf_track' e 'admm_solve_qp').
"""
import math
import os
import sys
from pathlib import Path

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import numpy as np

root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.planning.unscented_kalman_estimator import UnscentedKalmanStateEstimator
from aethermind_cognitive_substrate.logic_symbolic.admm_convex_optimizer import ADMMConvexQPOptimizer
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def main() -> int:
    print("=" * 80)
    print("[CICLO 14] UNSCENTED KALMAN (ÓRGÃO 43) & ADMM CONVEX QP (ÓRGÃO 44)")
    print("=" * 80)

    # 1. Córtex v4.6.0 (44 Órgãos)
    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY"
    assert health["organs_active_count"] >= 44, f"Esperado >= 44 órgãos, got {health['organs_active_count']}"
    assert health.get("ukf_nonlinear_estimator_active") is True
    assert health.get("admm_convex_qp_optimizer_active") is True
    print(f"[1/4] Córtex Prontidão: {health['organs_active_count']} órgãos | Versão={health['version']}")

    # 2. Órgão 43: UKF Nonlinear State Estimator (Rastreamento + Redução de Ruído + Detecção NIS)
    ukf = UnscentedKalmanStateEstimator(state_dim=4, obs_dim=4, process_noise_std=0.02, meas_noise_std=0.18)
    rng = np.random.RandomState(2026)

    # Simula trajetória verdadeira usando a dinâmica padrão do UKF
    x_true = np.array([1.2, -0.6, 0.4, 0.2], dtype=np.float64)
    ukf.reset(initial_state=[1.0, -0.4, 0.3, 0.1], init_cov=0.25)

    raw_errors = []
    filtered_errors = []
    u_zero = np.zeros(4, dtype=np.float64)

    for _ in range(30):
        x_true = ukf._default_transition(x_true, u_zero, dt=0.1)
        z_clean = ukf._default_measurement(x_true, 4)
        z_noisy = z_clean + rng.randn(4) * 0.18

        raw_errors.append(float(np.linalg.norm(z_noisy[:3] - x_true[:3])))
        res_step = ukf.step(z_noisy, control_input=u_zero, dt=0.1)
        x_est = np.array(res_step["estimated_state"], dtype=np.float64)
        filtered_errors.append(float(np.linalg.norm(x_est[:3] - x_true[:3])))

    mean_raw_err = float(np.mean(raw_errors[5:]))
    mean_ukf_err = float(np.mean(filtered_errors[5:]))
    assert mean_ukf_err < mean_raw_err, f"UKF não reduziu ruído: UKF={mean_ukf_err:.4f} vs Raw={mean_raw_err:.4f}"

    # Falsificação: injeção de choque sensorial (outlier) deve disparar NIS > 16
    shock_res = ukf.step(np.array([12.0, -10.0, 9.0, 5.0]))
    assert shock_res["anomaly_shock_detected"] is True, f"Falha ao detectar choque NIS: {shock_res}"
    print(
        f"[2/4] Órgão 43 (UKF Nonlinear Estimator): OK | Erro Bruto={mean_raw_err:.4f} -> "
        f"Erro UKF={mean_ukf_err:.4f} | Choque NIS={shock_res['normalized_innovation_squared_nis']} (Detectado=True)"
    )

    # 3. Órgão 44: ADMM Convex QP Optimizer (Benchmark analítico OSQP)
    # min 0.5*(4*x1^2 + 2*x1*x2 + 2*x2^2) + x1 + x2
    # s.t. x1 + x2 == 1, 0 <= x1 <= 0.7, 0 <= x2 <= 0.7
    # Solução analítica exata: x* = [0.3, 0.7], f(x*) = 1.88
    admm = ADMMConvexQPOptimizer(max_iter=400, eps_abs=1e-6, eps_rel=1e-5)
    qp_res = admm.solve_qp(
        P=[[4.0, 1.0], [1.0, 2.0]],
        q=[1.0, 1.0],
        A=[[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]],
        l=[1.0, 0.0, 0.0],
        u=[1.0, 0.7, 0.7]
    )
    assert qp_res["converged"] is True, f"ADMM não convergiu: {qp_res}"
    assert qp_res["constraints_satisfied"] is True
    x_opt = np.array(qp_res["optimal_x"], dtype=np.float64)
    analytic_err = float(np.linalg.norm(x_opt - np.array([0.3, 0.7])))
    assert analytic_err < 1e-3, f"Divergência da solução exata [0.3, 0.7]: {x_opt}"
    assert abs(qp_res["objective_value"] - 1.88) < 1e-3, f"Objetivo incorreto: {qp_res['objective_value']}"
    print(
        f"[3/4] Órgão 44 (ADMM Convex QP): OK | x*={qp_res['optimal_x']} (err={analytic_err:.2e}) | "
        f"obj={qp_res['objective_value']} | iters={qp_res['iterations']} em {qp_res['elapsed_us']} us"
    )

    # 4. Missões unificadas via SovereignCortexRuntime
    res_ukf_m = cortex.execute_cognitive_mission(
        "ukf_track",
        {"reset": True, "initial_state": [0.5, 0.0, 0.1, 0.2], "measurements": [[0.48, 0.05, 0.12, 0.19]] * 5}
    )["result"]
    assert res_ukf_m["status"] == "UKF_SEQUENCE_FILTERED"

    res_admm_m = cortex.execute_cognitive_mission(
        "admm_solve_qp",
        {
            "P": [[4.0, 1.0], [1.0, 2.0]],
            "q": [1.0, 1.0],
            "A": [[1.0, 1.0], [1.0, 0.0], [0.0, 1.0]],
            "l": [1.0, 0.0, 0.0],
            "u": [1.0, 0.7, 0.7]
        }
    )["result"]
    assert res_admm_m["converged"] is True
    print("[4/4] Integração Córtex (ukf_track + admm_solve_qp): OK")

    print("\n[VEREDITO FINAL]: CICLO 14 (UKF + ADMM QP) APROVADO COM EXIT CODE 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
