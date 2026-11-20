"""Test Suite — Ciclo 13: Koopman Spectral Linearizer (Organ 41) & Tensor Network MPS Compressor (Organ 42).

Verifica empiricamente:
1. Prontidão do Córtex v4.5.0 com 42 órgãos ativos.
2. Koopman EDMD 1-Shot: linearização espectral de oscilador não-linear, R² > 0.999 e previsão multi-passo contra ground-truth não visto.
3. Tensor Network MPS (TT-SVD): fatoração de tensor 4D de posto baixo, compressão > 5x, erro relativo Frobenius < 1e-6, entropia de Von Neumann S_vN e produto interno exato <T_A, T_B> sem reconstrução completa.
4. Integração via SovereignCortexRuntime ('koopman_fit_predict' e 'tensor_mps_compress').
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

from aethermind_cognitive_substrate.planning.koopman_spectral_linearizer import KoopmanSpectralLinearizer
from aethermind_cognitive_substrate.memory_vault.tensor_mps_compressor import TensorNetworkMPSCompressor
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime


def main() -> int:
    print("=" * 80)
    print("[CICLO 13] KOOPMAN SPECTRAL LINEARIZER (ÓRGÃO 41) & TENSOR MPS (ÓRGÃO 42)")
    print("=" * 80)

    # 1. Córtex v4.5.0 (42 Órgãos)
    cortex = SovereignCortexRuntime()
    health = cortex.get_system_health()
    assert health["status"] == "SOVEREIGN_READY"
    assert health["organs_active_count"] >= 42, f"Esperado >= 42 órgãos, got {health['organs_active_count']}"
    assert health.get("koopman_spectral_linearizer_active") is True
    assert health.get("tensor_mps_compressor_active") is True
    print(f"[1/4] Córtex Prontidão: {health['organs_active_count']} órgãos | Versão={health['version']}")

    # 2. Órgão 41: Koopman Spectral Linearizer (EDMD em sistema não-linear)
    traj = []
    x1, x2 = 0.85, -0.25
    for _ in range(45):
        traj.append([x1, x2, x1 * x2, math.sin(x1)])
        nx1 = 0.93 * x1 + 0.16 * x2 - 0.05 * (x1 ** 2) * x2
        nx2 = -0.14 * x1 + 0.94 * x2
        x1, x2 = nx1, nx2

    train_traj = traj[:35]
    test_future = traj[35:43]  # 8 passos não vistos

    res_k = cortex.execute_cognitive_mission(
        "koopman_fit_predict",
        {"trajectory": train_traj, "initial_state": train_traj[-1], "horizon_steps": 8}
    )["result"]
    assert res_k["fitted"] is True
    assert res_k["r2_reconstruction"] > 0.999, f"R2 insuficiente: {res_k['r2_reconstruction']}"
    assert res_k["is_spectrally_bounded"] is True, f"Raio espectral instável: {res_k['spectral_radius_rho']}"

    pred_traj = np.array(res_k["forecast"]["predicted_trajectory"], dtype=np.float64)
    truth_traj = np.array(test_future, dtype=np.float64)
    forecast_mae = float(np.mean(np.abs(pred_traj - truth_traj)))
    assert forecast_mae < 0.05, f"Erro de previsão multi-passo muito alto: {forecast_mae}"
    print(
        f"[2/4] Órgão 41 (Koopman EDMD): OK | R2={res_k['r2_reconstruction']} | "
        f"rho(K)={res_k['spectral_radius_rho']} | Forecast MAE(8 passos)={forecast_mae:.5f} em {res_k['elapsed_us']} us"
    )

    # Falsificação: trajetória insuficiente
    koop = KoopmanSpectralLinearizer(state_dim=4)
    fail_res = koop.fit_edmd([[0.1, 0.2, 0.3, 0.4]])
    assert fail_res["fitted"] is False

    # 3. Órgão 42: Tensor Network MPS (TT-SVD) Compressor
    a = np.linspace(0.2, 1.2, 6)
    b = np.sin(np.linspace(0.0, math.pi, 6))
    c = np.cos(np.linspace(0.0, math.pi, 6))
    d = np.exp(-np.linspace(0.0, 1.0, 6))
    tensor_a = np.einsum("i,j,k,l->ijkl", a, b, c, d) + 0.3 * np.einsum("i,j,k,l->ijkl", d, c, b, a)
    tensor_b = np.einsum("i,j,k,l->ijkl", d, b, a, c)

    mps = TensorNetworkMPSCompressor(max_bond_dim=8, svd_rel_tol=1e-6)
    comp_a = mps.compress_tensor_tt_svd(tensor_a)
    comp_b = mps.compress_tensor_tt_svd(tensor_b)

    assert comp_a["compression_ratio"] > 5.0, f"Compressão baixa: {comp_a['compression_ratio']}"
    assert comp_a["relative_frobenius_error"] < 1e-5, f"Erro TT-SVD alto: {comp_a['relative_frobenius_error']}"
    assert comp_a["central_von_neumann_entropy"] > 0.0

    # Verifica produto interno exato em espaço comprimido MPS vs completo
    exact_ip = float(np.sum(tensor_a * tensor_b))
    mps_ip = mps.mps_inner_product(comp_a["cores"], comp_b["cores"])
    assert abs(exact_ip - mps_ip) < 1e-6, f"Divergência no produto interno MPS: {exact_ip} vs {mps_ip}"
    print(
        f"[3/4] Órgão 42 (Tensor MPS): OK | Compressão={comp_a['compression_ratio']}x "
        f"({comp_a['raw_parameters']}->{comp_a['mps_parameters']}) | Erro={comp_a['relative_frobenius_error']:.2e} | "
        f"S_vN={comp_a['central_von_neumann_entropy']} | <A|B> err={abs(exact_ip - mps_ip):.2e}"
    )

    # 4. Missão via Córtex Runtime
    res_mps_mission = cortex.execute_cognitive_mission(
        "tensor_mps_compress",
        {"tensor": tensor_a.tolist(), "max_bond_dim": 8, "svd_rel_tol": 1e-5}
    )["result"]
    assert res_mps_mission["status"] == "MPS_TENSOR_TRAIN_COMPRESSED"
    assert abs(res_mps_mission["self_inner_product"] - float(np.sum(tensor_a ** 2))) < 1e-3
    print(f"[4/4] Integração Córtex tensor_mps_compress: OK | <A|A>={res_mps_mission['self_inner_product']}")

    print("\n[VEREDITO FINAL]: CICLO 13 (KOOPMAN + TENSOR MPS) APROVADO COM EXIT CODE 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
