"""SymPy Computer Algebra System (CAS) Engine (AetherMind Cognitive Substrate).

Área 03: Matemática Simbólica, Raciocínio Formal e Álgebra Exata.
Executa resolução de equações, cálculo diferencial/integral, álgebra linear e
simplificações sem risco de alucinação aritmética.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Union

_sp = None


def _get_sp():
    global _sp
    if _sp is None:
        import sympy as sp
        _sp = sp
    return _sp


class SymPyCASEngine:
    """Motor de Computação Algébrica Simbólica Exata baseado no SymPy."""

    def __init__(self):
        pass

    def solve_algebraic_equation(self, equation_str: str, target_var: str = "x") -> Dict[str, Any]:
        """Resolve uma equação algébrica exata (linear, polinomial, exponencial, trigonométrica)."""
        sp = _get_sp()
        start = time.perf_counter()
        target = sp.Symbol(target_var)
        
        # Converte equação "LHS = RHS" para "LHS - RHS = 0"
        if "=" in equation_str:
            parts = equation_str.split("=")
            lhs = sp.sympify(parts[0].strip())
            rhs = sp.sympify(parts[1].strip())
            expr = lhs - rhs
        else:
            expr = sp.sympify(equation_str.strip())

        solutions = sp.solve(expr, target)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "equation": str(expr) + " = 0",
            "target": target_var,
            "solutions": [str(sol) for sol in solutions],
            "latex": sp.latex(solutions),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def solve_linear_system(self, equations: List[str], variables: List[str]) -> Dict[str, Any]:
        """Resolve um sistema linear exato de N equações e N incógnitas."""
        sp = _get_sp()
        start = time.perf_counter()
        sym_vars = [sp.Symbol(v) for v in variables]
        sym_eqs = []
        for eq in equations:
            if "=" in eq:
                p = eq.split("=")
                sym_eqs.append(sp.sympify(p[0]) - sp.sympify(p[1]))
            else:
                sym_eqs.append(sp.sympify(eq))

        sol = sp.linsolve(sym_eqs, sym_vars)
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "variables": variables,
            "solution": str(sol),
            "latex": sp.latex(sol),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def compute_calculus(self, expr_str: str, var: str = "x", op: str = "diff", order: int = 1) -> Dict[str, Any]:
        """Executa cálculo diferencial ou integral simbólico exato."""
        sp = _get_sp()
        start = time.perf_counter()
        x = sp.Symbol(var)
        expr = sp.sympify(expr_str)

        if op.lower() == "diff":
            result = sp.diff(expr, x, order)
        elif op.lower() in ("integrate", "int"):
            result = sp.integrate(expr, x)
        elif op.lower() == "series":
            result = sp.series(expr, x, n=order)
        else:
            raise ValueError(f"Operação não suportada: {op}")

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "operation": op,
            "variable": var,
            "input_expression": str(expr),
            "result": str(result),
            "latex": sp.latex(result),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def compute_matrix_properties(self, matrix_data: List[List[Union[int, float, str]]]) -> Dict[str, Any]:
        """Calcula autovalores, autovetores, determinante, traço e inversa de uma matriz exata."""
        sp = _get_sp()
        start = time.perf_counter()
        M = sp.Matrix(matrix_data)

        det = M.det()
        trace = M.trace()
        eigenvals = {str(val): mult for val, mult in M.eigenvals().items()}
        
        is_invertible = bool(det != 0)
        inv = str(M.inv()) if is_invertible else None

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "rows": M.rows,
            "cols": M.cols,
            "determinant": str(det),
            "trace": str(trace),
            "eigenvalues": eigenvals,
            "is_invertible": is_invertible,
            "inverse": inv,
            "charpoly": str(M.charpoly().as_expr()),
            "elapsed_ms": round(elapsed_ms, 3)
        }
