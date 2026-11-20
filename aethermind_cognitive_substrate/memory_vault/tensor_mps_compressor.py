"""Tensor Network Matrix Product State (MPS / Tensor-Train SVD) Compressor (quimb / TensorNetwork Inspiration).

Organ 42 do Substrato Cognitivo Não-LLM (AetherCOS v4.5).
Quebra a Maldição da Dimensionalidade O(n^d) decompondo tensores cognitivos multi-modo
de alta ordem em uma cadeia de núcleos de ordem-3 (Matrix Product State / Tensor-Train):
    T[i_1, i_2, ..., i_d] ~= G_1[:, i_1, :] @ G_2[:, i_2, :] @ ... @ G_d[:, i_d, :]
usando SVD sequencial truncado (TT-SVD de Oseledets, 2011) com dimensão máxima de ligação
(bond dimension) chi_max e tolerância de truncamento relativo epsilon:
- Calcula Entropia de Emaranhamento de Von Neumann S_vN = - sum p_j ln(p_j) na ligação central.
- Executa produto interno exato <T_A, T_B> diretamente no espaço MPS comprimido em tempo
  polinomial O(d * chi^3 * n) sem expandir o tensor completo.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class TensorNetworkMPSCompressor:
    """
    Compressor de Redes Tensoriais Matrix Product State (MPS / TT-SVD).
    Permite representar, contrair e medir entropia de estados de alta ordem em memória polinomial.
    """

    def __init__(self, max_bond_dim: int = 16, svd_rel_tol: float = 1e-4):
        self.max_bond_dim = max_bond_dim
        self.svd_rel_tol = svd_rel_tol

    def compress_tensor_tt_svd(
        self,
        tensor: np.ndarray,
        max_bond_dim: Optional[int] = None,
        svd_rel_tol: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Executa decomposição TT-SVD em um tensor d-dimensional `tensor` de forma (n_1, ..., n_d).
        Retorna os núcleos MPS G_k de forma (r_{k-1}, n_k, r_k), taxas de compressão,
        erro relativo de Frobenius e entropia de emaranhamento de Von Neumann no corte central.
        """
        t0 = time.perf_counter()
        T = np.array(tensor, dtype=np.float64)
        shape = T.shape
        d = T.ndim
        if d < 2:
            T = T.reshape(1, -1)
            shape = T.shape
            d = 2

        chi_cap = max_bond_dim if max_bond_dim is not None else self.max_bond_dim
        tol = svd_rel_tol if svd_rel_tol is not None else self.svd_rel_tol

        raw_params = int(T.size)
        norm_T = float(np.linalg.norm(T))
        delta = (tol / math.sqrt(max(1, d - 1))) * (norm_T if norm_T > 1e-12 else 1.0)

        cores: List[np.ndarray] = []
        bond_dims: List[int] = [1]
        bond_entropies: List[float] = []

        C = T.copy()
        r_prev = 1

        for k in range(d - 1):
            n_k = shape[k]
            C = C.reshape(r_prev * n_k, -1)
            U, S, Vt = np.linalg.svd(C, full_matrices=False)

            # Truncamento por energia espectral + teto de dimensão de ligação chi_cap
            s_sq = S ** 2
            total_s_sq = float(np.sum(s_sq))
            cum_rem = np.cumsum(s_sq[::-1])[::-1]
            # Quantos modos precisamos manter para que o erro descartado <= delta^2
            rank = len(S)
            for idx_r in range(1, len(S) + 1):
                rem_err_sq = float(cum_rem[idx_r]) if idx_r < len(S) else 0.0
                if rem_err_sq <= delta ** 2:
                    rank = idx_r
                    break

            rank = max(1, min(rank, chi_cap, len(S)))

            # Entropia de Von Neumann desta ligação bipartida
            s_kept = S[:rank]
            probs = (s_kept ** 2) / (float(np.sum(s_kept ** 2)) + 1e-15)
            vn_entropy = float(-np.sum(probs * np.log(probs + 1e-15)))
            bond_entropies.append(round(vn_entropy, 5))

            U_r = U[:, :rank]
            S_r = S[:rank]
            Vt_r = Vt[:rank, :]

            core_k = U_r.reshape(r_prev, n_k, rank)
            cores.append(core_k)
            bond_dims.append(rank)

            C = (S_r[:, np.newaxis] * Vt_r)
            r_prev = rank

        # Último núcleo (r_{d-1}, n_d, 1)
        last_core = C.reshape(r_prev, shape[-1], 1)
        cores.append(last_core)
        bond_dims.append(1)

        mps_params = sum(int(c.size) for c in cores)
        reconstructed = self.reconstruct_tensor(cores)
        rel_error = float(np.linalg.norm(T - reconstructed) / (norm_T + 1e-12))

        mid_idx = max(0, (len(bond_entropies) - 1) // 2)
        central_entropy = bond_entropies[mid_idx] if bond_entropies else 0.0
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "MPS_TENSOR_TRAIN_COMPRESSED",
            "tensor_shape": list(shape),
            "tensor_order": d,
            "bond_dimensions": bond_dims,
            "max_bond_used": max(bond_dims),
            "raw_parameters": raw_params,
            "mps_parameters": mps_params,
            "compression_ratio": round(raw_params / max(1, mps_params), 3),
            "relative_frobenius_error": float(f"{rel_error:.3e}"),
            "central_von_neumann_entropy": central_entropy,
            "bond_entropies": bond_entropies,
            "cores": cores,
            "elapsed_ms": round(elapsed_ms, 3)
        }

    @staticmethod
    def reconstruct_tensor(cores: List[np.ndarray]) -> np.ndarray:
        """Contrai toda a cadeia MPS G_1 ... G_d de volta ao tensor completo."""
        acc = cores[0]  # (1, n_1, r_1)
        for core in cores[1:]:
            # Contrato último índice de acc com o primeiro de core: tensordot(..., axes=([-1], [0]))
            acc = np.tensordot(acc, core, axes=([-1], [0]))
        return np.squeeze(acc, axis=(0, -1))

    @staticmethod
    def mps_inner_product(cores_a: List[np.ndarray], cores_b: List[np.ndarray]) -> float:
        """
        Calcula o produto interno exato <A, B> diretamente na forma comprimida MPS
        sem reconstruir nenhum dos tensores completos em memória!
        Complexidade O(d * chi^3 * n).
        """
        assert len(cores_a) == len(cores_b), "MPS devem ter a mesma ordem tensorial"
        # Ambiente esquerdo E de forma (rA_0=1, rB_0=1)
        env = np.ones((1, 1), dtype=np.float64)
        for ca, cb in zip(cores_a, cores_b):
            # ca: (ra_l, n, ra_r), cb: (rb_l, n, rb_r)
            # env_ca: (rb_l, n, ra_r)
            tmp = np.tensordot(env, ca, axes=([0], [0]))
            # contrai rb_l e n com cb -> (ra_r, rb_r)
            env = np.tensordot(tmp, cb, axes=([0, 1], [0, 1]))
        return float(env[0, 0])
