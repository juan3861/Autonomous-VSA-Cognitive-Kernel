"""
Counterfactual Reasoner (Pearl Level 3 Causality: Abduction -> Action -> Prediction)
Evaluates retrospective queries: "Given observed state (X=x, Y=y), what would Y have been if X had been x'?"

Methodology:
1. Abduction: Compute background exogenous noise U from observed facts and structural equations.
2. Action: Perform graph surgery, forcing X := x_prime (eliminating ancestral dependencies of X).
3. Prediction: Propagate updated state downstream using modified equations and computed noise U.
"""

from __future__ import annotations

import time
import math
from typing import Dict, Any, List, Optional, Tuple
import networkx as nx

class CounterfactualReasoner:
    """Motor de Raciocínio Contrafactual Puro (Nível 3 de Judea Pearl)."""

    def __init__(self):
        self.dag = nx.DiGraph()
        self.equations: Dict[str, str] = {}
        self.noise_symbols: Dict[str, str] = {}

    def add_variable(self, name: str, equation_str: str, noise_name: Optional[str] = None):
        """
        Registra variável endógena com equação determinística:
        Ex: Y = 2.0 * X + U_Y
        """
        import re
        var = name.strip().lower()
        self.equations[var] = equation_str
        self.dag.add_node(var)
        
        # Detecta automaticamente se há símbolo de ruído na equação começando com 'u_'
        if noise_name:
            self.noise_symbols[var] = noise_name.lower()
        else:
            tokens = re.findall(r"\bu_[a-zA-Z0-9_]*\b", equation_str.lower())
            if tokens:
                self.noise_symbols[var] = tokens[0]
            else:
                self.noise_symbols[var] = f"u_{var}"

        all_tokens = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", equation_str)
        for tok in all_tokens:
            t = tok.lower()
            if t != var and not t.startswith("u_") and not t.isdigit():
                self.dag.add_edge(t, var)

    def evaluate_counterfactual(
        self,
        factual_observations: Dict[str, float],
        counterfactual_intervention: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Executa a Tríade de Judea Pearl:
        1. Abdução: infere U_i a partir de fatos reais.
        2. Ação: substitui X por x' mutilando dependências de X.
        3. Predição: recalcula o mundo contrafactual propagando os U_i abduzidos.
        """
        start = time.perf_counter()
        
        # -------------------------------------------------------------
        # PASSO 1: ABDUÇÃO (Inferência do Ruído Exógeno Passado)
        # -------------------------------------------------------------
        exogenous_noise: Dict[str, float] = {}
        for var, eq in self.equations.items():
            u_name = self.noise_symbols[var]
            if var in factual_observations:
                observed_val = factual_observations[var]
                # Avalia o componente determinístico f(PA) com U = 0
                eval_env = {k: factual_observations.get(k, 0.0) for k in self.dag.predecessors(var)}
                eval_env[u_name] = 0.0
                try:
                    det_val = float(eval(eq, {"__builtins__": None, "math": math}, eval_env))
                    # Resíduo é o ruído latente exógeno que realmente ocorreu
                    exogenous_noise[u_name] = observed_val - det_val
                except Exception:
                    exogenous_noise[u_name] = 0.0
            else:
                exogenous_noise[u_name] = 0.0

        # -------------------------------------------------------------
        # PASSO 2: AÇÃO (Cirurgia de Grafo Contrafactual)
        # -------------------------------------------------------------
        # Cria cópia mutilada onde as variáveis de intervenção perdem seus pais
        counterfactual_state = dict(factual_observations)
        counterfactual_state.update(counterfactual_intervention)
        intervened_vars = {k.strip().lower() for k in counterfactual_intervention.keys()}

        # -------------------------------------------------------------
        # PASSO 3: PREDIÇÃO (Propagação no Mundo Contrafactual)
        # -------------------------------------------------------------
        try:
            topo_order = list(nx.topological_sort(self.dag))
        except Exception:
            topo_order = list(self.dag.nodes())

        for node in topo_order:
            if node in intervened_vars:
                # O valor é fixado pela intervenção contrafactual
                continue
            
            if node in self.equations:
                eq = self.equations[node]
                u_name = self.noise_symbols[node]
                eval_env = {p: counterfactual_state.get(p, 0.0) for p in self.dag.predecessors(node)}
                eval_env[u_name] = exogenous_noise.get(u_name, 0.0)
                try:
                    counterfactual_state[node] = float(eval(eq, {"__builtins__": None, "math": math}, eval_env))
                except Exception:
                    pass

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "COUNTERFACTUAL_EVALUATED",
            "factual_observations": factual_observations,
            "abduced_exogenous_noise": {k: round(v, 4) for k, v in exogenous_noise.items()},
            "counterfactual_intervention": counterfactual_intervention,
            "counterfactual_world_state": {k: round(v, 4) for k, v in counterfactual_state.items()},
            "elapsed_ms": round(elapsed_ms, 3)
        }
