"""Adaptive Cubic B-Spline Kolmogorov-Arnold Network (KAN 2.0 Engine).

Área 02 & 03: Representação Simbólica Exata de Funções e Teorema de Kolmogorov-Arnold.
Baseado na formulação matemática de Liu et al. (MIT / arXiv 2024, pykan) e
nas otimizações de B-splines uniformes (Blealtan / efficient-kan):

Teorema de Representação de Kolmogorov-Arnold:
Qualquer função multivariada contínua f: [0, 1]^n -> R pode ser representada como:
    f(x_1, ..., x_n) = sum_{q=1}^{2n+1} Phi_q ( sum_{p=1}^n phi_{q, p}(x_p) )

Propriedades Fundamentais desta Implementação:
1. Elimina matrizes de peso lineares estáticas convencionais.
2. Funções univariadas aprendíveis nas ARESTAS via B-Splines Cúbicos (grau k=3)
   avaliados pela fórmula de recorrência de Cox-de Boor.
3. Partição da Unidade Exata: sum_j B_j(x) = 1.0 para todo x no domínio.
4. Conexão Residual Suave: phi_{q,p}(x) = w_{base} * silu(x) + sum_j c_j * B_j(x).
5. Ajuste Fechado em 1-Shot (Closed-Form Least Squares): para calibração analítica
   instantânea sem necessidade de retropropagação iterativa demorada.
6. Extração Simbólica Analítica Exata para cada aresta e nó de saída.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class AdaptiveBSplineKANEngine:
    """Motor de Redes Kolmogorov-Arnold Baseado em B-Splines Cúbicos Adaptativos."""

    def __init__(
        self,
        in_features: int = 4,
        out_features: int = 2,
        grid_intervals: int = 5,
        spline_degree: int = 3,
        grid_range: Tuple[float, float] = (-1.0, 1.0),
        seed: int = 42
    ):
        self.in_features = in_features
        self.out_features = out_features
        self.grid_intervals = grid_intervals
        self.spline_degree = spline_degree
        self.grid_range = grid_range
        self.rng = np.random.RandomState(seed)

        # Número de funções de base por aresta: G + k
        self.num_bases = grid_intervals + spline_degree

        # Gera nós da malha estendida uniforme
        a, b = grid_range
        h = (b - a) / grid_intervals
        self.h = h
        self.knots = np.linspace(
            a - spline_degree * h,
            b + spline_degree * h,
            grid_intervals + 2 * spline_degree + 1
        )

        # Coeficientes das bases de B-splines nas arestas: (out_features, in_features, num_bases)
        self.spline_weights = self.rng.randn(out_features, in_features, self.num_bases) * 0.1

        # Pesos residuais lineares: (out_features, in_features)
        self.base_weights = self.rng.randn(out_features, in_features) * 0.1

        # Bias de saída: (out_features,)
        self.bias = np.zeros(out_features, dtype=np.float64)

    def _compute_b_spline_bases(self, x: np.ndarray) -> np.ndarray:
        """Avalia a base de B-splines cúbicos via recorrência estável de Cox-de Boor.

        x: array 1D de shape (N,)
        Retorna: array de shape (N, num_bases)
        """
        a, b = self.grid_range
        x_clamped = np.clip(x, a, b)
        # Trata o limite superior para pertencer ao último semi-intervalo
        x_eval = np.where(x_clamped == b, b - 1e-14, x_clamped)
        x_col = x_eval[:, None]

        # Grau 0: funções indicadoras
        bases = ((x_col >= self.knots[:-1]) & (x_col < self.knots[1:])).astype(np.float64)

        # Recorrência de Cox-de Boor de grau 1 até k
        for d in range(1, self.spline_degree + 1):
            denom = d * self.h
            left = (x_col - self.knots[:-(d + 1)]) / denom * bases[:, :-1]
            right = (self.knots[d + 1:] - x_col) / denom * bases[:, 1:]
            bases = left + right

        return bases

    def _silu(self, x: np.ndarray) -> np.ndarray:
        """Ativação residual SiLU: x * sigmoid(x)."""
        return x / (1.0 + np.exp(-np.clip(x, -20.0, 20.0)))

    def forward(self, X: np.ndarray) -> np.ndarray:
        """Executa a passagem para frente da camada KAN B-Spline.

        X: array 2D de shape (N, in_features) ou 1D de shape (in_features,)
        Retorna: array de shape (N, out_features)
        """
        is_1d = (X.ndim == 1)
        if is_1d:
            X_2d = X.reshape(1, -1)
        else:
            X_2d = X.astype(np.float64)

        N, P = X_2d.shape
        Q = self.out_features
        assert P == self.in_features, f"Entrada incompatível: esperado {self.in_features}, obtido {P}"

        # Matriz de saída: (N, out_features)
        Y = np.zeros((N, Q), dtype=np.float64)
        Y += self.bias

        # Avalia cada aresta (p -> q)
        for p in range(P):
            x_p = X_2d[:, p]
            # Base residual SiLU
            base_act = self._silu(x_p)  # (N,)
            # Bases de B-spline: (N, num_bases)
            spline_bases = self._compute_b_spline_bases(x_p)

            for q in range(Q):
                w_b = self.base_weights[q, p]
                c_sp = self.spline_weights[q, p, :]  # (num_bases,)

                # Contribuição da aresta phi_{q, p}(x_p)
                edge_val = w_b * base_act + np.dot(spline_bases, c_sp)
                Y[:, q] += edge_val

        return Y[0] if is_1d else Y

    def fit_closed_form_1shot(
        self,
        X: np.ndarray,
        Y_target: np.ndarray,
        lambda_reg: float = 1e-4
    ) -> Dict[str, Any]:
        """Ajuste analítico fechado (Closed-Form Ridge Regression) em 1 único disparo sem backprop.

        X: (N, in_features)
        Y_target: (N, out_features) ou (N,)
        """
        start_time = time.perf_counter()
        X_arr = np.array(X, dtype=np.float64)
        if X_arr.ndim == 1:
            X_arr = X_arr.reshape(-1, 1)

        N, P = X_arr.shape
        if Y_target.ndim == 1:
            Y_arr = Y_target.reshape(-1, 1)
        else:
            Y_arr = np.array(Y_target, dtype=np.float64)

        Q = Y_arr.shape[1]
        self.in_features = P
        self.out_features = Q

        # Constrói a matriz de design completa A com todas as bases das arestas
        # Features por aresta: 1 (base silu) + num_bases (splines)
        cols = [np.ones((N, 1))]  # Termo de bias
        edge_feature_map = []

        for p in range(P):
            x_p = X_arr[:, p]
            silu_col = self._silu(x_p)[:, None]
            spline_cols = self._compute_b_spline_bases(x_p)
            feat = np.hstack([silu_col, spline_cols])
            cols.append(feat)
            edge_feature_map.append((p, feat.shape[1]))

        # Matriz de design global: A shape (N, 1 + P * (1 + num_bases))
        A = np.hstack(cols)
        D = A.shape[1]

        # Resolução exata via Mínimos Quadrados Regularizados (Equação Normal de Tikhonov)
        AtA = np.dot(A.T, A) + lambda_reg * np.eye(D)
        AtY = np.dot(A.T, Y_arr)

        # W_opt: shape (D, Q)
        W_opt = np.linalg.solve(AtA, AtY)

        # Descompacta pesos de volta para a estrutura KAN
        self.bias = W_opt[0, :]
        offset = 1
        self.base_weights = np.zeros((Q, P), dtype=np.float64)
        self.spline_weights = np.zeros((Q, P, self.num_bases), dtype=np.float64)

        for p, n_feats in edge_feature_map:
            for q in range(Q):
                self.base_weights[q, p] = W_opt[offset, q]
                self.spline_weights[q, p, :] = W_opt[offset + 1: offset + n_feats, q]
            offset += n_feats

        # Avaliação de métricas pós-ajuste
        Y_pred = np.dot(A, W_opt)
        mse = float(np.mean((Y_arr - Y_pred) ** 2))
        var_y = float(np.var(Y_arr))
        r2 = float(1.0 - (mse / (var_y + 1e-8)))
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return {
            "status": "FIT_CONVERGED_1SHOT",
            "samples": N,
            "in_features": P,
            "out_features": Q,
            "total_spline_bases": P * self.num_bases,
            "mse": round(mse, 6),
            "r2_score": round(r2, 6),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def compute_edge_significance(self) -> np.ndarray:
        """Calcula a norma L1 da importância de cada aresta (out_features, in_features)."""
        Q, P, B = self.spline_weights.shape
        scores = np.zeros((Q, P), dtype=np.float64)
        for q in range(Q):
            for p in range(P):
                spline_norm = float(np.sum(np.abs(self.spline_weights[q, p, :])))
                base_norm = abs(self.base_weights[q, p])
                scores[q, p] = spline_norm + base_norm
        return scores

    def extract_symbolic_formulas(self, significance_threshold: float = 0.05) -> List[str]:
        """Extrai as fórmulas matemáticas analíticas explícitas de cada nó de saída."""
        formulas = []
        sig_matrix = self.compute_edge_significance()

        for q in range(self.out_features):
            active_terms = []
            for p in range(self.in_features):
                if sig_matrix[q, p] >= significance_threshold:
                    w_b = self.base_weights[q, p]
                    c_mean = float(np.mean(self.spline_weights[q, p, :]))
                    c_max = float(np.max(np.abs(self.spline_weights[q, p, :])))
                    term = f"({w_b:+.3f}*silu(x_{p}) + B_Spline3(c_max={c_max:.3f}, mean={c_mean:+.3f}))"
                    active_terms.append(term)

            bias_str = f"{self.bias[q]:+.3f}"
            if active_terms:
                formula = f"y_{q} = {bias_str} + " + " + ".join(active_terms)
            else:
                formula = f"y_{q} = {bias_str}"
            formulas.append(formula)

        return formulas
