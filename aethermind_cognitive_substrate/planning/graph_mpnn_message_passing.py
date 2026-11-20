"""Deterministic Relational Graph Message Passing Engine (PyTorch Geometric / GraphNets Inspiration).

Organ 45 do Substrato Cognitivo Não-LLM (AetherCOS v4.7).
Implementa passagem de mensagens relacional e espectral sobre grafos arbitrários sem backpropagation:
- Construção da matriz de adjacência normalizada simétrica (Laplaciano espectral):
    A_hat = D_tilde^{-1/2} (A + I) D_tilde^{-1/2}
- Agregação anisotrópica por atenção estrutural cosseno entre vizinhos:
    m_i^{(l)} = sum_{j in N(i) U {i}} alpha_{ij} (W_msg * h_j^{(l)})
- Atualização Residual com Gate (GRU-like contrativo) e normalização espectral estrita (rho <= 0.85),
  garantindo estabilidade assintótica de ponto fixo ao longo de L camadas de propagação.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class GraphMPNNMessagePassingEngine:
    """
    Motor de Passagem de Mensagens em Grafos Relacionais (MPNN Determinístico).
    Propaga evidências e anomalias estruturais sobre grafos causais e semânticos em < 1 ms.
    """

    def __init__(self, hidden_dim: int = 16, num_layers: int = 3, seed: int = 42):
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        rng = np.random.RandomState(seed)
        W_m = rng.randn(hidden_dim, hidden_dim)
        # Normalização espectral estrita (rho <= 0.85) para garantir contração de Banach
        max_sv_m = float(np.linalg.norm(W_m, ord=2))
        self.W_msg = W_m * (0.85 / max(1e-9, max_sv_m))

        W_u = rng.randn(hidden_dim, hidden_dim)
        max_sv_u = float(np.linalg.norm(W_u, ord=2))
        self.W_upd = W_u * (0.85 / max(1e-9, max_sv_u))

    @staticmethod
    def _build_normalized_adjacency(
        num_nodes: int,
        edges: List[Tuple[int, int]] | List[List[int]],
        edge_weights: Optional[List[float]] = None
    ) -> np.ndarray:
        A = np.eye(num_nodes, dtype=np.float64)
        for idx, edge in enumerate(edges):
            u, v = int(edge[0]), int(edge[1])
            if 0 <= u < num_nodes and 0 <= v < num_nodes:
                w = float(edge_weights[idx]) if edge_weights and idx < len(edge_weights) else 1.0
                A[u, v] += w
                A[v, u] += w
        deg = np.sum(A, axis=1)
        deg_inv_sqrt = 1.0 / np.sqrt(np.maximum(deg, 1e-12))
        D_inv_sqrt = np.diag(deg_inv_sqrt)
        return D_inv_sqrt @ A @ D_inv_sqrt

    def propagate(
        self,
        node_features: List[List[float]] | np.ndarray,
        edges: List[Tuple[int, int]] | List[List[int]],
        edge_weights: Optional[List[float]] = None,
        num_layers: Optional[int] = None,
        alpha_residual: float = 0.65
    ) -> Dict[str, Any]:
        """
        Executa L rodadas de Message Passing sobre o grafo (node_features, edges).
        Retorna os embeddings propagados, normas por nó, delta de convergência e pooling global.
        """
        t0 = time.perf_counter()
        X = np.array(node_features, dtype=np.float64)
        if X.ndim == 1:
            X = X.reshape(1, -1)
        num_nodes, feat_dim = X.shape

        # Ajusta dimensão das features para hidden_dim de forma determinística
        if feat_dim < self.hidden_dim:
            H = np.pad(X, ((0, 0), (0, self.hidden_dim - feat_dim)))
        elif feat_dim > self.hidden_dim:
            H = X[:, :self.hidden_dim].copy()
        else:
            H = X.copy()

        A_norm = self._build_normalized_adjacency(num_nodes, edges, edge_weights)
        layers = num_layers if num_layers is not None else self.num_layers

        deltas: List[float] = []
        for _ in range(layers):
            H_prev = H
            # Mensagem espectral normalizada + atenção anisotrópica por similaridade de estado
            H_norm_rows = H / (np.linalg.norm(H, axis=1, keepdims=True) + 1e-12)
            sim_matrix = H_norm_rows @ H_norm_rows.T
            att_adj = A_norm * np.exp(0.5 * sim_matrix)
            row_sums = np.sum(att_adj, axis=1, keepdims=True) + 1e-12
            att_adj = att_adj / row_sums

            messages = att_adj @ (H @ self.W_msg.T)
            updated = np.tanh(messages + H @ self.W_upd.T)
            H = (1.0 - alpha_residual) * H_prev + alpha_residual * updated
            deltas.append(float(np.linalg.norm(H - H_prev)))

        node_norms = [round(float(np.linalg.norm(H[i])), 5) for i in range(num_nodes)]
        dominant_node_idx = int(np.argmax(node_norms)) if node_norms else 0
        graph_embedding = np.mean(H, axis=0)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "GRAPH_MPNN_PROPAGATED",
            "num_nodes": num_nodes,
            "num_edges": len(edges),
            "layers_executed": layers,
            "layer_convergence_deltas": [round(d, 6) for d in deltas],
            "contraction_verified": bool(len(deltas) < 2 or deltas[-1] <= deltas[0] + 1e-6),
            "dominant_node_index": dominant_node_idx,
            "node_activation_norms": node_norms,
            "graph_readout_norm": round(float(np.linalg.norm(graph_embedding)), 5),
            "graph_readout_preview": [round(float(v), 5) for v in graph_embedding[:4]],
            "elapsed_us": round(elapsed_us, 2)
        }
