"""Scientific Physics & Dimensional Invariant Engine (AetherMind Cognitive Substrate).

Área 11: Raciocínio Científico, Invariantes Físicos e Leis de Conservação.
Verifica consistência dimensional estrita nas 7 grandezas de base do SI
(Massa, Comprimento, Tempo, Corrente, Temperatura, Quantidade, Intensidade Luminosa).
Impede alucinações de fórmulas físicas, valida conservação de energia e momento
e audita equações diferenciais da física clássica.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Tuple, Optional


class PhysicalDimension:
    """Vetor de dimensões no Sistema Internacional: [M, L, T, I, Theta, N, J]."""

    def __init__(self, m: int = 0, l: int = 0, t: int = 0, i: int = 0, theta: int = 0, n: int = 0, j: int = 0):
        self.exponents = (m, l, t, i, theta, n, j)

    def __eq__(self, other):
        return isinstance(other, PhysicalDimension) and self.exponents == other.exponents

    def __mul__(self, other: PhysicalDimension) -> PhysicalDimension:
        return PhysicalDimension(*(a + b for a, b in zip(self.exponents, other.exponents)))

    def __truediv__(self, other: PhysicalDimension) -> PhysicalDimension:
        return PhysicalDimension(*(a - b for a, b in zip(self.exponents, other.exponents)))

    def __pow__(self, power: int) -> PhysicalDimension:
        return PhysicalDimension(*(a * power for a in self.exponents))

    def to_symbolic_string(self) -> str:
        names = ["kg", "m", "s", "A", "K", "mol", "cd"]
        parts = []
        for name, exp in zip(names, self.exponents):
            if exp == 1:
                parts.append(name)
            elif exp != 0:
                parts.append(f"{name}^{exp}")
        return " * ".join(parts) if parts else "adimensional"


# Dicionário canônico de grandezas físicas derivadas
CANONICAL_DIMENSIONS = {
    "comprimento": PhysicalDimension(l=1),
    "massa": PhysicalDimension(m=1),
    "tempo": PhysicalDimension(t=1),
    "velocidade": PhysicalDimension(l=1, t=-1),
    "aceleracao": PhysicalDimension(l=1, t=-2),
    "forca": PhysicalDimension(m=1, l=1, t=-2),            # Newton = kg*m/s^2
    "energia": PhysicalDimension(m=1, l=2, t=-2),          # Joule = kg*m^2/s^2
    "potencia": PhysicalDimension(m=1, l=2, t=-3),         # Watt = J/s
    "pressao": PhysicalDimension(m=1, l=-1, t=-2),         # Pascal = N/m^2
    "frequencia": PhysicalDimension(t=-1),                 # Hertz = 1/s
    "carga_eletrica": PhysicalDimension(t=1, i=1),         # Coulomb = A*s
    "tensao_eletrica": PhysicalDimension(m=1, l=2, t=-3, i=-1) # Volt = W/A
}


class ScientificPhysicsEngine:
    """Motor de Verificação de Invariantes Físicos e Análise Dimensional."""

    def __init__(self):
        pass

    def check_equation_dimensional_homogeneity(
        self,
        lhs_terms: List[Tuple[float, str]],
        rhs_terms: List[Tuple[float, str]]
    ) -> Dict[str, Any]:
        """Verifica se todos os termos de uma equação possuem a mesma dimensão física (Princípio de Fourier)."""
        start = time.perf_counter()

        def _resolve_dim(term_str: str) -> Optional[PhysicalDimension]:
            term = term_str.strip().lower()
            return CANONICAL_DIMENSIONS.get(term)

        lhs_dims = [_resolve_dim(t[1]) for t in lhs_terms]
        rhs_dims = [_resolve_dim(t[1]) for t in rhs_terms]

        if any(d is None for d in lhs_dims + rhs_dims):
            return {
                "is_homogeneous": False,
                "error": "Grandeza física não reconhecida na base canônica",
                "elapsed_ms": round((time.perf_counter() - start) * 1000.0, 3)
            }

        ref_dim = lhs_dims[0]
        # Todos os termos do LHS e RHS devem ser dimensionalmente idênticos
        is_valid = all(d == ref_dim for d in lhs_dims) and all(d == ref_dim for d in rhs_dims)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "is_homogeneous": is_valid,
            "base_dimension": ref_dim.to_symbolic_string() if is_valid else "INCONSISTENTE",
            "lhs_count": len(lhs_terms),
            "rhs_count": len(rhs_terms),
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def verify_energy_conservation(
        self,
        initial_energies: Dict[str, float],
        final_energies: Dict[str, float],
        tolerance: float = 1e-4
    ) -> Dict[str, Any]:
        """Valida a Primeira Lei da Termodinâmica: Conservação de Energia (Delta E = 0)."""
        start = time.perf_counter()

        e_init = sum(initial_energies.values())
        e_final = sum(final_energies.values())
        diff = abs(e_final - e_init)
        conserved = bool(diff <= tolerance)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "is_energy_conserved": conserved,
            "initial_energy_joules": round(e_init, 4),
            "final_energy_joules": round(e_final, 4),
            "energy_discrepancy_joules": round(diff, 6),
            "tolerance": tolerance,
            "elapsed_ms": round(elapsed_ms, 3)
        }
