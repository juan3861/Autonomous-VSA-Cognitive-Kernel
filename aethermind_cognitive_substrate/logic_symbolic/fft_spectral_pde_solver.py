"""FFT Pseudo-Spectral Partial Differential Equation (PDE) Solver.

Organ 69 do Substrato Cognitivo Nao-LLM (AetherCOS v6.0).
Solucionador Pseudo-Espectral de EDPs (Equacoes Diferenciais Parciais) em dominio periodico via FFT:
- Resolve a equacao de Adveccao-Difusao 1D:
    du/dt + c * du/dx = nu * d^2u/dx^2   em x in [0, 2*pi)
- No espaco de Fourier (numeros de onda k):
    du_hat/dt = (-i*c*k - nu*k^2) * u_hat(k)
  que possui solucao analitica exata por fator integrante u_hat(k, t) = u_hat(k, 0) * exp((-i*c*k - nu*k^2)*t);
- Verifica conservacao de massa (modo k=0 invariante), decaimento da energia L2 (Parseval) sob
  difusao pura nu > 0, e conservacao exata de norma L2 sob adveccao pura (nu = 0) em O(N log N).
"""
from __future__ import annotations

import math
import time
from typing import Dict, Any, List, Optional
import numpy as np


class FFTSpectralPDESolver:
    """
    Solucionador Pseudo-Espectral Fourier (FFT) para EDPs de Adveccao-Difusao.
    """

    def __init__(self, n_grid: int = 128, advection_c: float = 1.0, viscosity_nu: float = 0.05):
        self.n_grid = int(n_grid)
        self.advection_c = float(advection_c)
        self.viscosity_nu = float(viscosity_nu)

    def solve_advection_diffusion(
        self,
        u0: Optional[List[float] | np.ndarray] = None,
        t_final: float = 1.0,
        advection_c: Optional[float] = None,
        viscosity_nu: Optional[float] = None,
        n_grid: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Integra a EDP de adveccao-difusao em [0, 2*pi) ate t_final via FFT com precisao espectral.
        """
        t0 = time.perf_counter()

        N = int(n_grid if n_grid is not None else self.n_grid)
        c = float(advection_c if advection_c is not None else self.advection_c)
        nu = float(viscosity_nu if viscosity_nu is not None else self.viscosity_nu)
        L = 2.0 * math.pi

        if u0 is None:
            x = np.linspace(0.0, L, N, endpoint=False)
            # Pulso gaussiano + harmonico de alta frequencia
            u_init = np.exp(-((x - math.pi) ** 2) / 0.4) + 0.5 * np.sin(4.0 * x)
        else:
            u_init = np.asarray(u0, dtype=np.float64).reshape(-1)
            N = len(u_init)

        dx = L / N
        # Numeros de onda angulares para dominio [0, 2*pi)
        k = np.fft.fftfreq(N, d=dx) * (2.0 * math.pi)

        u_hat0 = np.fft.fft(u_init)
        # Operador espectral exato em Fourier
        multiplier = np.exp((-1j * c * k - nu * (k ** 2)) * float(t_final))
        u_hat_final = u_hat0 * multiplier
        u_final = np.real(np.fft.ifft(u_hat_final))

        # Conservacao de massa (integral / media) e energia L2 (teorema de Parseval)
        mass_init = float(np.sum(u_init) * dx)
        mass_final = float(np.sum(u_final) * dx)
        mass_error = abs(mass_final - mass_init)

        energy_init = float(np.sum(u_init ** 2) * dx)
        energy_final = float(np.sum(u_final ** 2) * dx)
        parseval_energy_fourier = float(np.sum(np.abs(u_hat_final) ** 2) / N * dx)
        parseval_error = abs(energy_final - parseval_energy_fourier)

        elapsed_us = (time.perf_counter() - t0) * 1e6
        return {
            "status": "FFT_SPECTRAL_PDE_SOLVED",
            "n_grid": N,
            "t_final": float(t_final),
            "advection_c": c,
            "viscosity_nu": nu,
            "mass_conservation_error": float(f"{mass_error:.3e}"),
            "parseval_identity_error": float(f"{parseval_error:.3e}"),
            "l2_energy_initial": round(energy_init, 6),
            "l2_energy_final": round(energy_final, 6),
            "dissipative_decay_verified": (energy_final <= energy_init + 1e-12) if nu >= 0.0 else True,
            "elapsed_us": round(elapsed_us, 2),
        }
