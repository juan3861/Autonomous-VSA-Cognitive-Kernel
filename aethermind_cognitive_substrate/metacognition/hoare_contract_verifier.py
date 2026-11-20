"""Hoare Logic Triples & Weakest Precondition Verifier (AetherMind Cognitive Substrate).

Áreas 02 & 07: Engenharia de Código, Verificação Formal e Cadinho Red-Team.
Implementa o cálculo de Menor Pré-Condição de Dijkstra (Weakest Precondition wp(C, Q))
e a prova formal de Triplas de Hoare {P} C {Q} via SMT (Z3Prover).
Verifica a correção parcial de programas antes da execução no sistema operacional.
"""
from __future__ import annotations

import re
import time
from typing import Dict, Any, List, Optional, Tuple
import z3


class HoareContractVerifier:
    """Verificador Formal de Contratos e Triplas de Hoare."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def substitute_var_in_expr(self, expr_str: str, var_name: str, replacement_expr: str) -> str:
        """Substituição sintática segura de variável por expressão: Q[var <- repl]."""
        pattern = r"\b" + re.escape(var_name) + r"\b"
        return re.sub(pattern, f"({replacement_expr})", expr_str)

    def compute_weakest_precondition_assignment(self, assignment_var: str, expr: str, postcondition: str) -> str:
        """Regra de Atribuição de Hoare: wp(x := E, Q) = Q[x <- E]."""
        return self.substitute_var_in_expr(postcondition, assignment_var, expr)

    def verify_hoare_triple_assignment(
        self,
        declarations: Dict[str, str],
        precondition: str,
        assignment_var: str,
        assigned_expr: str,
        postcondition: str
    ) -> Dict[str, Any]:
        """Verifica formalmente se a Tripla {P} x := E {Q} é Válida.
        
        Teorema: A tripla é válida se e somente se P => wp(x := E, Q) for uma tautologia (UNSAT do negado).
        """
        start = time.perf_counter()
        wp_str = self.compute_weakest_precondition_assignment(assignment_var, assigned_expr, postcondition)

        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)

        env: Dict[str, Any] = {}
        for v_name, v_type in declarations.items():
            if v_type.lower() == "int":
                env[v_name] = z3.Int(v_name)
            elif v_type.lower() == "real":
                env[v_name] = z3.Real(v_name)
            elif v_type.lower() == "bool":
                env[v_name] = z3.Bool(v_name)

        def _parse_formula(s: str) -> Any:
            parts = [p.strip() for p in s.split(" and ") if p.strip()]
            parsed = [eval(p, {"__builtins__": None, "z3": z3}, env) for p in parts]
            if len(parsed) == 1:
                return parsed[0]
            return z3.And(*parsed)

        p_ast = _parse_formula(precondition)
        wp_ast = _parse_formula(wp_str)

        # Procura contraexemplo: P and not(wp)
        solver.add(p_ast)
        solver.add(z3.Not(wp_ast))

        check_res = solver.check()
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if check_res == z3.unsat:
            return {
                "is_contract_valid": True,
                "status": "HOARE_TRIPLE_PROVEN",
                "precondition": precondition,
                "command": f"{assignment_var} := {assigned_expr}",
                "weakest_precondition": wp_str,
                "postcondition": postcondition,
                "elapsed_ms": round(elapsed_ms, 3)
            }
        elif check_res == z3.sat:
            model = solver.model()
            ce = {k: str(model.eval(v, model_completion=True)) for k, v in env.items()}
            return {
                "is_contract_valid": False,
                "status": "COUNTEREXAMPLE_VIOLATION",
                "counterexample": ce,
                "precondition": precondition,
                "command": f"{assignment_var} := {assigned_expr}",
                "weakest_precondition": wp_str,
                "postcondition": postcondition,
                "explanation": "Contrato violado! O comando quebra a pós-condição sob este contraexemplo.",
                "elapsed_ms": round(elapsed_ms, 3)
            }
        else:
            return {
                "is_contract_valid": False,
                "status": "UNKNOWN",
                "reason": solver.reason_unknown(),
                "elapsed_ms": round(elapsed_ms, 3)
            }
