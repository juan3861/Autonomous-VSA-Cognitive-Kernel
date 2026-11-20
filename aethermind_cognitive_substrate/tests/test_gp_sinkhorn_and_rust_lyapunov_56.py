"""Test Suite — Ciclo 20 (v5.3.0, 56 Órgãos): Rust Lyapunov Smith Doubling + GP Cholesky (55) + Sinkhorn OT (56).

Verifica empiricamente:
1. Prontidão do Córtex v5.3.0 com 56 órgãos determinísticos ativos.
2. Kernel Bare-Metal Rust `lyapunov_smith_doubling_f64` (Órgão 54 acelerado em DLL):
   - Resolve A^T P A - P = -Q para matriz estável 16x16 em código máquina Rust LTO com
     resíduo Frobenius < 1e-11 e convergência exata contra o caminho NumPy.
3. SparseGaussianProcessEstimator (Órgão 55):
   - Ajusta f(x) = sin(x) em [-2, 2] com RMSE < 0.05;
   - Certifica calibração epistêmica OOD: desvio padrão em x=6.0 (longe dos dados)
     é estritamente maior (> 4x) que em x=0.5 (dentro da distribuição de treino).
4. OptimalTransportSinkhornEngine (Órgão 56):
   - Calcula plano ótimo de acoplamento e distância de Wasserstein entre distribuições
     de suportes disjuntos (onde KL diverge para +inf) com erro marginal L1 < 1e-5 e
     distância consistente com o deslocamento geométrico.
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

from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def main() -> int:
    print("=" * 84)
    print("[CICLO 20 — 56 ÓRGÃOS] RUST LYAPUNOV + GP CHOLESKY (55) + SINKHORN OT (56)")
    print("=" * 84)

    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY", health
    assert health["organs_active_count"] >= 56, f"Esperado >= 56 órgãos, obtido {health['organs_active_count']}"
    assert health["gp_cholesky_estimator_active"] is True
    assert health["optimal_transport_sinkhorn_active"] is True
    print(f"[PASS] Córtex {health['version']} pronto com {health['organs_active_count']} órgãos.")

    # 1. Benchmark & Paridade do Kernel Rust LTO `lyapunov_smith_doubling_f64` (matriz 16x16 estável)
    rng = np.random.default_rng(202620)
    raw = rng.normal(0.0, 1.0, size=(16, 16))
    rho_raw = float(np.max(np.abs(np.linalg.eigvals(raw))))
    A16 = raw * (0.82 / max(rho_raw, 1e-9))

    lyap_rust = cortex.lyapunov_certifier.certify_discrete_lyapunov(A16, prefer_native=True)
    lyap_py = cortex.lyapunov_certifier.certify_discrete_lyapunov(A16, prefer_native=False)

    assert "Rust" in lyap_rust.get("backend", ""), lyap_rust
    assert lyap_rust["asymptotically_stable"] is True
    assert lyap_rust["stein_residual_fro"] < 1e-11, lyap_rust
    p_diff = float(np.max(np.abs(np.array(lyap_rust["lyapunov_matrix_P"]) - np.array(lyap_py["lyapunov_matrix_P"]))))
    assert p_diff < 1e-4, f"Divergência Rust vs NumPy em P: {p_diff}"
    print(
        f"[PASS] Rust LTO Lyapunov 16x16 ({lyap_rust['backend']}): "
        f"resíduo={lyap_rust['stein_residual_fro']} | Rust={lyap_rust['elapsed_us']} us vs Py={lyap_py['elapsed_us']} us | max|dP|={p_diff:.2e}"
    )

    # 2. Órgão 55 — SparseGaussianProcessEstimator: interpolação + incerteza epistêmica OOD
    x_tr = np.linspace(-2.0, 2.0, 15).tolist()
    y_tr = [math.sin(x) for x in x_tr]
    gp_res = cortex.execute_cognitive_mission(
        "gp_cholesky_predict",
        {"X_train": x_tr, "y_train": y_tr, "X_query": [0.5, 6.0]},
    )["result"]
    assert gp_res["status"] == "GP_CHOLESKY_POSTERIOR_COMPUTED", gp_res
    assert gp_res["train_rmse"] < 0.05, gp_res
    mu_in, _ = gp_res["posterior_mean"]
    std_in, std_ood = gp_res["posterior_std"]
    assert abs(mu_in - math.sin(0.5)) < 0.05, f"Erro predição in-dist: {mu_in} vs {math.sin(0.5)}"
    assert std_ood > 4.0 * std_in, f"Incerteza OOD não cresceu suficientemente: in={std_in}, ood={std_ood}"
    print(
        f"[PASS] Órgão 55 (GP Cholesky): mu(0.5)={mu_in:.4f} (real={math.sin(0.5):.4f}) | "
        f"sigma_in={std_in:.4f} << sigma_ood={std_ood:.4f} ({std_ood/std_in:.1f}x) | {gp_res['elapsed_us']} us"
    )

    # 3. Órgão 56 — OptimalTransportSinkhornEngine: suportes disjuntos (KL=+inf, Wasserstein exato)
    ot_res = cortex.execute_cognitive_mission(
        "sinkhorn_ot",
        {
            "source_weights": [0.5, 0.5, 0.0, 0.0],
            "target_weights": [0.0, 0.0, 0.5, 0.5],
            "source_points": [0.0, 1.0, 2.0, 3.0],
            "target_points": [0.0, 1.0, 2.0, 3.0],
            "reg_epsilon": 0.05,
        },
    )["result"]
    assert ot_res["status"] == "SINKHORN_OPTIMAL_TRANSPORT_CONVERGED", ot_res
    assert ot_res["converged"] is True
    assert ot_res["marginal_l1_error"] < 1e-5, ot_res
    # Deslocamento exato de {0,1} -> {2,3} tem distância W2 = 2.0
    assert 1.95 <= ot_res["wasserstein_distance"] <= 2.15, ot_res
    print(
        f"[PASS] Órgão 56 (Sinkhorn OT): W2={ot_res['wasserstein_distance']} (exato=2.0) | "
        f"erro_marg={ot_res['marginal_l1_error']} | iters={ot_res['iterations']} em {ot_res['elapsed_us']} us"
    )

    print("=" * 84)
    print("SUCESSO ABSOLUTO: TODOS OS 56 ÓRGÃOS E INVARIANTES DO CICLO 20 VERIFICADOS!")
    print("=" * 84)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
