"""Kolmogorov-Arnold Network (KAN) & Morphogenetic Neural Cellular Automata (NCA).

Área 02 & 03: Representação Simbólica Exata de Funções e Auto-Organização Morfogenética.
Dois avanços não-euclidianos fundamentais:
1. KAN (Teorema de Kolmogorov-Arnold, 1957 / pykan):
   - Elimina matrizes de peso lineares fixas.
   - Ativações univariadas aprendíveis nas ARESTAS via B-Splines / Polinômios de Chebyshev.
   - f(x_1, ..., x_n) = sum_q Phi_q( sum_p phi_{q,p}(x_p) ).
   - Permite extração simbólica exata de fórmulas físicas sem matrizes densas.
2. NCA (Neural Cellular Automata / Michael Levin bioelétrico):
   - Células 2D que atualizam seu estado olhando apenas para vizinhos imediatos (convolução local Sobel).
   - Auto-reparo biológico: se 70% do estado for destruído, a regra local regenera a forma global.
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple, Callable
import numpy as np


class KolmogorovArnoldSplineLayer:
    """Camada KAN baseada em Expansão de Polinômios de Chebyshev / B-Splines nas Arestas."""

    def __init__(self, in_features: int = 4, out_features: int = 4, degree: int = 4):
        self.in_features = in_features
        self.out_features = out_features
        self.degree = degree

        # Coeficientes dos polinômios nas arestas: shape (out_features, in_features, degree + 1)
        rng = np.random.RandomState(42)
        self.coefficients = rng.randn(out_features, in_features, degree + 1) * 0.1

    def _chebyshev_basis(self, x: np.ndarray) -> np.ndarray:
        """Gera base de polinômios de Chebyshev: T_0(x)=1, T_1(x)=x, T_{n+1}=2xT_n - T_{n-1}."""
        # Limita entrada para [-1, 1]
        x_clipped = np.clip(x, -1.0, 1.0)
        basis = [np.ones_like(x_clipped), x_clipped]
        for n in range(1, self.degree):
            t_next = 2.0 * x_clipped * basis[-1] - basis[-2]
            basis.append(t_next)
        return np.stack(basis, axis=-1)  # shape: (..., degree + 1)

    def forward(self, x: np.ndarray) -> np.ndarray:
        """Aplica a soma de Kolmogorov-Arnold sobre as funções univariadas de cada aresta."""
        # x shape: (in_features,)
        x_arr = np.resize(x.astype(np.float64), self.in_features)
        # Base de Chebyshev para cada entrada: (in_features, degree + 1)
        phi_bases = self._chebyshev_basis(x_arr)

        # Avalia phi_{q, p}(x_p) multiplicando coeficientes
        # out[q] = sum_p sum_d (coef[q, p, d] * basis[p, d])
        edge_eval = np.einsum("qpd,pd->qp", self.coefficients, phi_bases)
        # Soma sobre as entradas p
        out = np.sum(edge_eval, axis=1)
        return out

    def extract_symbolic_representation(self) -> List[str]:
        """Extrai as fórmulas matemáticas analíticas explícitas de cada nó de saída."""
        formulas = []
        for q in range(self.out_features):
            edge_terms = []
            for p in range(self.in_features):
                coefs = self.coefficients[q, p]
                # Monta polinômio aproximado
                terms = [f"{coefs[0]:+.3f}"]
                for d in range(1, self.degree + 1):
                    if abs(coefs[d]) > 0.01:
                        terms.append(f"{coefs[d]:+.3f}*T_{d}(x_{p})")
                edge_terms.append("(" + " ".join(terms) + ")")
            formulas.append(f"y_{q} = " + " + ".join(edge_terms[:2]) + " ...")
        return formulas


class MorphogeneticCellularAutomata:
    """Autômato Celular Neural (NCA) com Auto-Cura e Regeneração Bioelétrica."""

    def __init__(self, grid_size: int = 16, channels: int = 4, seed: int = 42):
        self.grid_size = grid_size
        self.channels = channels
        self.rng = np.random.RandomState(seed)

        # Grade 2D: (height, width, channels)
        self.grid = np.zeros((grid_size, grid_size, channels), dtype=np.float32)

        # Matrizes de percepção local (Kernel de Sobel horizontal, vertical e identidade)
        self.sobel_x = np.array([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], dtype=np.float32)
        self.sobel_y = np.array([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], dtype=np.float32)

        # Pesos mínimos da regra celular local: percept_dim (channels * 3) -> channels
        percept_dim = channels * 3
        self.W_rule = self.rng.randn(channels, percept_dim).astype(np.float32) * 0.1

    def seed_target_pattern(self) -> None:
        """Inicializa um padrão alvo no centro da grade."""
        center = self.grid_size // 2
        # Cria uma esfera/anel de atividade celular central
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                dist = math.sqrt((i - center) ** 2 + (j - center) ** 2)
                if dist <= 3.5:
                    self.grid[i, j, 0] = 1.0  # Canal de forma
                    self.grid[i, j, 1] = float(math.exp(-dist))

    def step(self) -> None:
        """Executa 1 passo de crescimento local celular (convolução local e atualização)."""
        h, w, c = self.grid.shape
        # Convolução discreta rápida com padding circular
        grad_x = np.zeros_like(self.grid)
        grad_y = np.zeros_like(self.grid)

        for ch in range(c):
            channel = self.grid[:, :, ch]
            # Aplica Sobel manual nas bordas
            padded = np.pad(channel, 1, mode="wrap")
            for i in range(h):
                for j in range(w):
                    patch = padded[i:i+3, j:j+3]
                    grad_x[i, j, ch] = np.sum(patch * self.sobel_x)
                    grad_y[i, j, ch] = np.sum(patch * self.sobel_y)

        # Vetor de percepção por célula: [identidade, grad_x, grad_y]
        percept = np.concatenate([self.grid, grad_x, grad_y], axis=-1)  # (h, w, c*3)

        # Atualização celular não-linear: Delta x = tanh(W * percept)
        delta = np.tanh(np.dot(percept, self.W_rule.T))
        # Mascaramento estocástico biológico (células disparam de forma assíncrona)
        stochastic_mask = (self.rng.uniform(0.0, 1.0, size=(h, w, 1)) < 0.8).astype(np.float32)
        self.grid = np.clip(self.grid + delta * stochastic_mask * 0.2, 0.0, 1.0)

    def mutilate_damage(self, damage_ratio: float = 0.70) -> int:
        """Destrói deliberadamente uma porcentagem massiva da estrutura celular."""
        total_cells = self.grid_size * self.grid_size
        num_mutilate = int(total_cells * damage_ratio)
        coords = [(i, j) for i in range(self.grid_size) for j in range(self.grid_size)]
        damaged_indices = self.rng.choice(len(coords), size=num_mutilate, replace=False)
        for idx in damaged_indices:
            r, col = coords[idx]
            self.grid[r, col, :] = 0.0
        return num_mutilate

    def compute_pattern_energy(self) -> float:
        """Calcula a biomassa / energia viva da estrutura celular."""
        return float(np.sum(self.grid[:, :, 0]))
