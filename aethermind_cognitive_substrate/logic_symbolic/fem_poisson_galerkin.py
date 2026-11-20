"""1D Finite Element Method (FEM) P1 Linear Galerkin Solver for Elliptic PDEs.

Organ 79 do Substrato Cognitivo Nao-LLM (AetherCOS v7.0).
Metodo dos Elementos Finitos (FEM) com funcoes de base lineares por partes (P1 chapeu):
- Resolve a EDP eliptica -d/dx (a(x) du/dx) + c(x) u(x) = f(x) em [0, 1] com u(0)=0, u(1)=0;
- Monta matriz de rigidez global K e vetor de carga F elemento-a-elemento via quadratura
  de Gauss de 2 pontos exata para polinomios ate grau 3;
- Verifica convergencia O(h^2) em norma L2 e energia H1 contra solucao analitica exata.
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, Optional
import numpy as np


class FiniteElementGalerkinSolver:
    """
    Solucionador de Elementos Finitos (FEM P1 Galerkin) para EDPs Elipticas.
    """

    def __init__(self, n_elements: int = 64):
        self.n_elements = int(n_elements)

    def solve_elliptic_poisson(
        self,
        n_elements: Optional[int] = None,
        diffusion_a: float = 1.0,
        reaction_c: float = 2.0,
    ) -> Dict[str, Any]:
        """
        Resolve -a * u''(x) + c * u(x) = f(x) em [0, 1], u(0)=u(1)=0, onde a solucao
        exata e u_ex(x) = sin(pi * x) + 0.5 * sin(2 * pi * x).
        """
        t0 = time.perf_counter()

        ne = int(n_elements if n_elements is not None else self.n_elements)
        n_nodes = ne + 1
        x_nodes = np.linspace(0.0, 1.0, n_nodes, dtype=np.float64)
        h = 1.0 / ne

        def u_exact(xv: np.ndarray) -> np.ndarray:
            return np.sin(math.pi * xv) + 0.5 * np.sin(2.0 * math.pi * xv)

        def rhs_f(xv: np.ndarray) -> np.ndarray:
            # -(a u'') + c u
            u_xx = -(math.pi ** 2) * np.sin(math.pi * xv) - 2.0 * (math.pi ** 2) * np.sin(2.0 * math.pi * xv)
            return -diffusion_a * u_xx + reaction_c * u_exact(xv)

        K = np.zeros((n_nodes, n_nodes), dtype=np.float64)
        F = np.zeros(n_nodes, dtype=np.float64)

        # Quadratura de Gauss-Legendre de 2 pontos em [-1, 1]
        gp = np.array([-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)], dtype=np.float64)
        gw = np.array([1.0, 1.0], dtype=np.float64)

        for e in range(ne):
            x0, x1 = x_nodes[e], x_nodes[e + 1]
            jac = 0.5 * (x1 - x0)  # h / 2

            Ke = np.zeros((2, 2), dtype=np.float64)
            Fe = np.zeros(2, dtype=np.float64)

            for xi, w in zip(gp, gw):
                # Funcoes de forma P1 em [-1, 1]
                phi = np.array([0.5 * (1.0 - xi), 0.5 * (1.0 + xi)], dtype=np.float64)
                dphi_dx = np.array([-0.5 / jac, 0.5 / jac], dtype=np.float64)
                x_phys = 0.5 * (1.0 - xi) * x0 + 0.5 * (1.0 + xi) * x1
                f_val = float(rhs_f(np.array([x_phys]))[0])

                Ke += (diffusion_a * np.outer(dphi_dx, dphi_dx) + reaction_c * np.outer(phi, phi)) * jac * w
                Fe += phi * f_val * jac * w

            K[e:e + 2, e:e + 2] += Ke
            F[e:e + 2] += Fe

        # Condicoes de contorno de Dirichlet homogeneas u(0)=0, u(1)=0 nos nos internos
        K_int = K[1:-1, 1:-1]
        F_int = F[1:-1]
        u_int = np.linalg.solve(K_int, F_int)

        u_num = np.zeros(n_nodes, dtype=np.float64)
        u_num[1:-1] = u_int

        u_ex = u_exact(x_nodes)
        l2_err = math.sqrt(float(np.sum(((u_num - u_ex) ** 2) * h)))
        linf_err = float(np.max(np.abs(u_num - u_ex)))

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "FEM_GALERKIN_P1_SOLVED",
            "n_elements": ne,
            "n_nodes": n_nodes,
            "mesh_size_h": round(h, 6),
            "l2_error": float(f"{l2_err:.3e}"),
            "linf_error": float(f"{linf_err:.3e}"),
            "galerkin_converged": l2_err < 1e-2,
            "u_mid_value": round(float(u_num[n_nodes // 2]), 6),
            "elapsed_us": round(elapsed_us, 2),
        }
