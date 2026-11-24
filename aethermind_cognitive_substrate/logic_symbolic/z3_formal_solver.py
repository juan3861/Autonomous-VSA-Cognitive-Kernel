"""Z3 Formal Solver & Theorem Prover Engine (AetherMind Cognitive Substrate).

Área 03: Matemática Simbólica, Raciocínio Formal e SMT.
Provador formal matemático sem LLM: satisfatibilidade, verificação de invariantes,
resolução exata de restrições e otimização por Programação Inteira/Real.
"""
from __future__ import annotations

import threading
import time
from typing import Dict, Any, List, Optional, Tuple, Union
import z3

# Global re-entrant lock protecting Z3's non-thread-safe default global Context across parallel DAG waves.
Z3_GLOBAL_LOCK = threading.RLock()


class Z3FormalSolver:
    """Motor de Verificação Formal e SMT baseado no Z3Prover."""

    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms

    def solve_constraints(self, declarations: Dict[str, str], constraints: List[str]) -> Dict[str, Any]:
        """Resolve um sistema arbitrário de restrições SMT.
        
        Args:
            declarations: Dicionário mapeando nome da variável para tipo ('int', 'real', 'bool').
            constraints: Lista de expressões Python avaliáveis com as variáveis Z3.
        """
        start = time.perf_counter()
        with Z3_GLOBAL_LOCK:
            solver = z3.Solver()
            solver.set("timeout", self.timeout_ms)

            env: Dict[str, Any] = {}
            for var_name, var_type in declarations.items():
                if var_type.lower() == "int":
                    env[var_name] = z3.Int(var_name)
                elif var_type.lower() == "real":
                    env[var_name] = z3.Real(var_name)
                elif var_type.lower() == "bool":
                    env[var_name] = z3.Bool(var_name)
                else:
                    raise ValueError(f"Tipo não suportado: {var_type}")

            for c_str in constraints:
                expr = eval(c_str, {"__builtins__": None, "z3": z3}, env)
                solver.add(expr)

            check_res = solver.check()
            elapsed_ms = (time.perf_counter() - start) * 1000.0

            if check_res == z3.sat:
                model = solver.model()
                solution = {}
                for k, v in env.items():
                    val = model.eval(v, model_completion=True)
                    solution[k] = str(val)
                return {
                    "status": "SAT",
                    "is_satisfiable": True,
                    "solution": solution,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "model_raw": str(model)
                }
            elif check_res == z3.unsat:
                return {
                    "status": "UNSAT",
                    "is_satisfiable": False,
                    "solution": None,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "reason": "Contradição estrita detectada nas restrições fornecidas"
                }
            else:
                return {
                    "status": "UNKNOWN",
                    "is_satisfiable": None,
                    "solution": None,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "reason": solver.reason_unknown()
                }

    def verify_invariant(self, declarations: Dict[str, str], precondition: str, postcondition: str) -> Dict[str, Any]:
        """Verifica formalmente se Precondition -> Postcondition é um Teorema Válido.
        
        Método de Prova: Uma implicação P => Q é válida se e somente se P and not(Q) for UNSAT.
        """
        start = time.perf_counter()
        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)

        env: Dict[str, Any] = {}
        for var_name, var_type in declarations.items():
            if var_type.lower() == "int":
                env[var_name] = z3.Int(var_name)
            elif var_type.lower() == "real":
                env[var_name] = z3.Real(var_name)
            elif var_type.lower() == "bool":
                env[var_name] = z3.Bool(var_name)
            else:
                raise ValueError(f"Tipo não suportado: {var_type}")

        def _parse_z3_formula(expr_str: str) -> Any:
            parts = [p.strip() for p in expr_str.split(" and ") if p.strip()]
            parsed = [eval(p, {"__builtins__": None, "z3": z3}, env) for p in parts]
            if len(parsed) == 1:
                return parsed[0]
            return z3.And(*parsed)

        pre_expr = _parse_z3_formula(precondition)
        post_expr = _parse_z3_formula(postcondition)

        # Procura por contraexemplo: pre_expr and not(post_expr)
        solver.add(pre_expr)
        solver.add(z3.Not(post_expr))

        check_res = solver.check()
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if check_res == z3.unsat:
            return {
                "verified": True,
                "status": "PROVEN_VALID",
                "explanation": "Teorema formalmente provado: nenhum contraexemplo existe.",
                "elapsed_ms": round(elapsed_ms, 3)
            }
        elif check_res == z3.sat:
            model = solver.model()
            counterexample = {k: str(model.eval(v, model_completion=True)) for k, v in env.items()}
            return {
                "verified": False,
                "status": "COUNTEREXAMPLE_FOUND",
                "counterexample": counterexample,
                "explanation": "Invariante violada! Contraexemplo gerado automaticamente.",
                "elapsed_ms": round(elapsed_ms, 3)
            }
        else:
            return {
                "verified": False,
                "status": "UNKNOWN",
                "reason": solver.reason_unknown(),
                "elapsed_ms": round(elapsed_ms, 3)
            }

    def optimize_objective(
        self,
        declarations: Dict[str, str],
        constraints: List[str],
        objective: str,
        minimize: bool = True
    ) -> Dict[str, Any]:
        """Otimização matemática exata com Z3.Optimize."""
        start = time.perf_counter()
        opt = z3.Optimize()

        env: Dict[str, Any] = {}
        for var_name, var_type in declarations.items():
            if var_type.lower() == "int":
                env[var_name] = z3.Int(var_name)
            elif var_type.lower() == "real":
                env[var_name] = z3.Real(var_name)
            elif var_type.lower() == "bool":
                env[var_name] = z3.Bool(var_name)

        for c_str in constraints:
            opt.add(eval(c_str, {"__builtins__": None, "z3": z3}, env))

        obj_expr = eval(objective, {"__builtins__": None, "z3": z3}, env)
        handle = opt.minimize(obj_expr) if minimize else opt.maximize(obj_expr)

        check_res = opt.check()
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        if check_res == z3.sat:
            model = opt.model()
            solution = {k: str(model.eval(v, model_completion=True)) for k, v in env.items()}
            opt_val = str(model.eval(handle.value(), model_completion=True))
            return {
                "status": "OPTIMAL",
                "optimal_value": opt_val,
                "solution": solution,
                "elapsed_ms": round(elapsed_ms, 3)
            }
        else:
            return {
                "status": "INFEASIBLE_OR_UNBOUNDED",
                "optimal_value": None,
                "solution": None,
                "elapsed_ms": round(elapsed_ms, 3)
            }
