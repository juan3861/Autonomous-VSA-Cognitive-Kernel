"""NOTEARS Continuous Optimization Causal Discovery Engine.

Área 05: Causalidade Estrutural e Descoberta de Grafos Acíclicos Dirigidos (DAGs).
Baseado no avanço matemático de Zheng et al. (NeurIPS 2018):
"DAGs with NO TEARS: Continuous Optimization for Structure Learning".

Em vez de buscas combinatórias exponenciais NP-difíceis (como o algoritmo PC clássico),
o NOTEARS transforma a restrição puramente combinatória de aciclicidade em uma restrição
suave e contínua via exponencial de matrizes:
    h(W) = Tr(exp(W o W)) - d = 0

Propriedades fundamentais:
1. h(W) >= 0 para qualquer matriz de adjacência W.
2. h(W) = 0 se e somente se o grafo gerado por W for estritamente um DAG (sem ciclos dirigidos).
3. Gradiente contínuo analítico:
    grad_h(W) = 2 * (exp(W o W))^T o W
onde 'o' denota o produto de Hadamard (elemento a elemento).
"""
from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


class ContinuousNOTEARSEngine:
    """Motor de Descoberta Causal Contínua via Otimização em Silício (NOTEARS)."""

    def __init__(
        self,
        lambda1: float = 0.05,
        max_iter: int = 50,
        h_tol: float = 1e-8,
        rho_max: float = 1e16,
        w_threshold: float = 0.25
    ):
        self.lambda1 = lambda1
        self.max_iter = max_iter
        self.h_tol = h_tol
        self.rho_max = rho_max
        self.w_threshold = w_threshold

    @staticmethod
    def _h(W: np.ndarray) -> float:
        """Restrição de aciclicidade suave h(W) = Tr(exp(W o W)) - d."""
        import scipy.linalg
        d = W.shape[0]
        M = W * W
        E = scipy.linalg.expm(M)
        h = float(np.trace(E) - d)
        return max(0.0, h)

    @staticmethod
    def _grad_h(W: np.ndarray) -> np.ndarray:
        """Gradiente analítico exato da restrição de aciclicidade."""
        import scipy.linalg
        M = W * W
        E = scipy.linalg.expm(M)
        return 2.0 * (E.T * W)

    def _loss_and_grad(
        self,
        W: np.ndarray,
        X: np.ndarray,
        rho: float,
        alpha: float
    ) -> Tuple[float, np.ndarray]:
        """Calcula o valor e o gradiente do Lagrangeano Aumentado."""
        n, d = X.shape
        # Erro quadrático de mínimos quadrados: 0.5/n * ||X - XW||_F^2
        R = X - np.dot(X, W)
        loss = 0.5 / n * np.sum(R ** 2)
        grad_loss = - (1.0 / n) * np.dot(X.T, R)

        # Termo de aciclicidade h(W)
        h_val = self._h(W)
        grad_h_val = self._grad_h(W)

        # Lagrangeano aumentado: L = loss + alpha * h + 0.5 * rho * h^2
        augmented_val = loss + alpha * h_val + 0.5 * rho * (h_val ** 2)
        augmented_grad = grad_loss + (alpha + rho * h_val) * grad_h_val

        return augmented_val, augmented_grad

    def fit(
        self,
        X: np.ndarray,
        var_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Aprende o DAG causal contínuo a partir de dados observacionais X (n x d)."""
        from scipy.optimize import minimize
        start_time = time.perf_counter()
        n, d = X.shape

        if var_names is None:
            var_names = [f"X_{i}" for i in range(d)]

        # Centraliza os dados
        X_centered = X - np.mean(X, axis=0)

        # Inicialização: matriz de pesos nula
        W = np.zeros((d, d), dtype=np.float64)
        rho = 1.0
        alpha = 0.0
        h_val = np.inf

        # Bounds: a diagonal deve ser exatamente zero (sem auto-laços diretos)
        bounds = []
        for i in range(d):
            for j in range(d):
                if i == j:
                    bounds.append((0.0, 0.0))
                else:
                    bounds.append((None, None))

        history = []

        for iteration in range(self.max_iter):
            # Função objetivo para o otimizador L-BFGS-B
            def objective(w_flat):
                w_mat = w_flat.reshape((d, d))
                val, grad = self._loss_and_grad(w_mat, X_centered, rho, alpha)
                # Adiciona regularização L2 suave para estabilidade
                val += 0.5 * self.lambda1 * np.sum(w_mat ** 2)
                grad += self.lambda1 * w_mat
                return val, grad.flatten()

            # Otimização irrestrita na iteração interna com L-BFGS-B
            res = minimize(
                fun=objective,
                x0=W.flatten(),
                method="L-BFGS-B",
                jac=True,
                bounds=bounds,
                options={"maxiter": 100, "ftol": 1e-9}
            )

            W_new = res.x.reshape((d, d))
            h_new = self._h(W_new)

            history.append({
                "iteration": iteration + 1,
                "h_val": float(h_new),
                "rho": float(rho),
                "alpha": float(alpha)
            })

            # Atualização do multiplicador e da penalidade
            if h_new > 0.25 * h_val:
                rho = min(rho * 10.0, self.rho_max)
            alpha += rho * h_new
            W = W_new
            h_val = h_new

            if h_val <= self.h_tol or rho >= self.rho_max:
                break

        # Pós-processamento: limiar de corte para esparsidade causal
        W_thresholded = np.copy(W)
        W_thresholded[np.abs(W_thresholded) < self.w_threshold] = 0.0

        # Verificação formal de aciclicidade do grafo limiarizado
        is_dag, cycles_found = self._verify_acyclicity(W_thresholded)
        if not is_dag:
            # Poda gulosa do arco mais fraco que fecha ciclo
            W_thresholded = self._prune_cycles_greedy(W_thresholded)
            is_dag, _ = self._verify_acyclicity(W_thresholded)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Monta lista de arestas dirigidas
        edges = []
        for i in range(d):
            for j in range(d):
                weight = float(W_thresholded[i, j])
                if abs(weight) > 1e-5:
                    edges.append({
                        "cause": var_names[i],
                        "effect": var_names[j],
                        "weight": round(weight, 4),
                        "abs_strength": round(abs(weight), 4)
                    })

        # Ordena arestas por força de causalidade
        edges.sort(key=lambda x: x["abs_strength"], reverse=True)

        return {
            "status": "SUCCESS" if is_dag else "CONVERGED_WITH_WARNING",
            "is_strictly_dag": is_dag,
            "acyclicity_h_value": float(h_val),
            "iterations_required": len(history),
            "elapsed_ms": round(elapsed_ms, 3),
            "num_variables": d,
            "num_samples": n,
            "edges_count": len(edges),
            "causal_edges": edges,
            "adjacency_matrix": W_thresholded.tolist(),
            "variable_names": var_names
        }

    @staticmethod
    def _verify_acyclicity(adj: np.ndarray) -> Tuple[bool, List[List[int]]]:
        """Testa se a matriz de adjacência forma um DAG estrito via ordenação topológica."""
        d = adj.shape[0]
        # Constrói lista de adjacências para pesos não nulos
        graph = {i: [] for i in range(d)}
        in_degree = {i: 0 for i in range(d)}
        for i in range(d):
            for j in range(d):
                if abs(adj[i, j]) > 1e-6:
                    graph[i].append(j)
                    in_degree[j] += 1

        # Algoritmo de Kahn
        queue = [i for i in range(d) if in_degree[i] == 0]
        visited_count = 0

        while queue:
            curr = queue.pop(0)
            visited_count += 1
            for neighbor in graph[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        is_dag = (visited_count == d)
        return is_dag, []

    @staticmethod
    def _prune_cycles_greedy(adj: np.ndarray) -> np.ndarray:
        """Poda arestas com menores pesos absolutos até garantir DAG estrito."""
        W = np.copy(adj)
        d = W.shape[0]

        while True:
            is_dag, _ = ContinuousNOTEARSEngine._verify_acyclicity(W)
            if is_dag:
                break
            # Encontra a aresta com menor peso absoluto não-nulo e remove
            non_zero_indices = np.argwhere(np.abs(W) > 1e-6)
            if len(non_zero_indices) == 0:
                break
            weights = [abs(W[i, j]) for i, j in non_zero_indices]
            min_idx = np.argmin(weights)
            rem_i, rem_j = non_zero_indices[min_idx]
            W[rem_i, rem_j] = 0.0

        return W
