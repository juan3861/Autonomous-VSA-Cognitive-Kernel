"""Win32 System Sentinel & Bare-Metal Hardware Sensor (AetherMind Cognitive Substrate).

Área 13: Governador de Hardware, Térmico, RAM e Sentinela de Ociosidade Win32.
Mede a telemetria do sistema em menos de 0,5 ms sem chamadas bloqueantes:
- CPU e RAM instantâneas via psutil com cache não-bloqueante
- Detecção de ociosidade do usuário via GetLastInputInfo (Win32 API)
- Sinal de evasão imediata (< 0,2 ms) ao toque do mouse/teclado.
"""
from __future__ import annotations

import ctypes
import os
import sys
import time
from typing import Dict, Any, Optional
import psutil


class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_uint),
        ("dwTime", ctypes.c_uint)
    ]


class Win32SystemSentinel:
    """Sensor Bare-Metal do Sistema Operacional Windows e Sentinela de Ociosidade."""

    def __init__(self, idle_threshold_sec: float = 120.0):
        self.idle_threshold_sec = idle_threshold_sec
        self._last_cpu_sample = 0.0
        self._last_sample_time = 0.0
        self._is_windows = (sys.platform == "win32")

    def get_idle_seconds(self) -> float:
        """Calcula há quantos segundos o usuário não mexe no teclado ou mouse via Win32 API."""
        if not self._is_windows:
            return 0.0

        try:
            lii = LASTINPUTINFO()
            lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii)):
                millis_now = ctypes.windll.kernel32.GetTickCount()
                idle_ms = millis_now - lii.dwTime
                return max(0.0, idle_ms / 1000.0)
        except Exception:
            pass
        return 0.0

    def probe_hardware_telemetry(self) -> Dict[str, Any]:
        """Amostra instantânea não-bloqueante de CPU, RAM e ociosidade."""
        start = time.perf_counter()
        now = time.time()

        # Cache não-bloqueante de 100ms para CPU
        if (now - self._last_sample_time) > 0.1:
            self._last_cpu_sample = psutil.cpu_percent(interval=None)
            self._last_sample_time = now

        vm = psutil.virtual_memory()
        idle_secs = self.get_idle_seconds()
        is_user_idle = bool(idle_secs >= self.idle_threshold_sec)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "HEALTHY",
            "cpu_percent": self._last_cpu_sample,
            "ram_percent": vm.percent,
            "ram_available_mb": round(vm.available / (1024 * 1024), 1),
            "ram_critical_panic": bool(vm.percent > 90.0),
            "idle_seconds": round(idle_secs, 2),
            "is_user_idle": is_user_idle,
            "evacuation_signal": not is_user_idle,  # Se o usuário está na máquina, evacua tarefas de fundo
            "elapsed_ms": round(elapsed_ms, 3)
        }
