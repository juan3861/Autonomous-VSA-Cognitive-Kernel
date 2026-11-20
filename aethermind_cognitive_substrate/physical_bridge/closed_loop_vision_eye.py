"""Closed-Loop Desktop Eye & Window Inspector (AetherMind Cognitive Substrate).

Áreas 04 & 09: Automação Desktop (RPA), Visão e Percepção Multimodal.
Inspeção de janelas ativas, coordenadas de interface e verificação fechada
do ambiente desktop via Win32 API direta, sem automação cega e sem LLM.
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys
import time
from typing import Dict, Any, List, Optional, Tuple


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long)
    ]


class ClosedLoopVisionEye:
    """Sensor Closed-Loop de Janelas e Elementos de Desktop do Windows."""

    def __init__(self):
        self._is_windows = (sys.platform == "win32")

    def inspect_visible_windows(self, max_windows: int = 25) -> Dict[str, Any]:
        """Varre todas as janelas visíveis no desktop com título e dimensões."""
        start = time.perf_counter()
        if not self._is_windows:
            return {"status": "NOT_WINDOWS", "windows": [], "elapsed_ms": 0.0}

        windows = []

        def enum_windows_callback(hwnd, extra):
            if ctypes.windll.user32.IsWindowVisible(hwnd):
                length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()

                    rect = RECT()
                    ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                    width = rect.right - rect.left
                    height = rect.bottom - rect.top

                    if width > 50 and height > 50:
                        windows.append({
                            "hwnd": hwnd,
                            "title": title,
                            "x": rect.left,
                            "y": rect.top,
                            "width": width,
                            "height": height
                        })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
        callback = WNDENUMPROC(enum_windows_callback)
        ctypes.windll.user32.EnumWindows(callback, None)

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "status": "SUCCESS",
            "total_visible_windows": len(windows),
            "windows": windows[:max_windows],
            "elapsed_ms": round(elapsed_ms, 3)
        }

    def verify_window_exists(self, title_substring: str) -> Dict[str, Any]:
        """Verifica deterministicamente se uma janela esperada existe e está aberta."""
        start = time.perf_counter()
        res = self.inspect_visible_windows(max_windows=100)
        sub = title_substring.strip().lower()

        matched = [w for w in res.get("windows", []) if sub in w["title"].lower()]
        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "query_substring": title_substring,
            "exists": len(matched) > 0,
            "matches_count": len(matched),
            "matched_windows": matched,
            "elapsed_ms": round(elapsed_ms, 3)
        }
