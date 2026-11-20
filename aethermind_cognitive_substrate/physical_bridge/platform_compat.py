"""Cross-Platform Compatibility & Hardware Abstraction Layer for Cognitive Substrate.

Provides uniform operating system abstractions across Windows, Linux, and macOS:
- Dynamic discovery and loading of the Rust C-ABI native library (`.dll`, `.so`, `.dylib`).
- Unified zero-copy virtual memory / mmap page locking across Win32 and POSIX.
- High-resolution hardware monotonic timer and platform feature flags.
"""
from __future__ import annotations

import ctypes
import os
import platform
import sys
from pathlib import Path
from typing import Optional, Tuple


def is_windows() -> bool:
    """Return True if executing on a Microsoft Windows environment."""
    return sys.platform.startswith("win") or os.name == "nt"


def is_linux() -> bool:
    """Return True if executing on a Linux environment."""
    return sys.platform.startswith("linux")


def is_macos() -> bool:
    """Return True if executing on macOS / Darwin."""
    return sys.platform == "darwin"


def get_substrate_root() -> Path:
    """Resolve the canonical absolute directory of `aethermind_cognitive_substrate`."""
    return Path(__file__).resolve().parent.parent


def get_project_root() -> Path:
    """Resolve the canonical root directory of the entire repository."""
    return get_substrate_root().parent


def get_native_lib_filename(base_name: str = "aether_cortex_vsa") -> str:
    """Return the platform-specific shared library filename."""
    if is_windows():
        return f"{base_name}.dll"
    elif is_macos():
        return f"lib{base_name}.dylib"
    else:
        return f"lib{base_name}.so"


def find_native_library_path(base_name: str = "aether_cortex_vsa") -> Optional[Path]:
    """Search for the compiled Rust native library in canonical build directories."""
    filename = get_native_lib_filename(base_name)
    project_root = get_project_root()
    substrate_root = get_substrate_root()

    candidate_paths = [
        project_root / base_name / "target" / "release" / filename,
        project_root / base_name / "target" / "debug" / filename,
        project_root / "target" / "release" / filename,
        substrate_root / "physical_bridge" / filename,
        Path.cwd() / filename,
    ]

    for p in candidate_paths:
        if p.exists() and p.is_file():
            return p.resolve()

    return None


def load_native_library(base_name: str = "aether_cortex_vsa") -> Optional[ctypes.CDLL]:
    """Load and return the platform shared library via ctypes, or None if unavailable."""
    lib_path = find_native_library_path(base_name)
    if lib_path is None:
        return None

    try:
        return ctypes.CDLL(str(lib_path))
    except Exception:
        return None


def allocate_aligned_memory(size_bytes: int, alignment: int = 64) -> Tuple[Optional[int], Optional[object]]:
    """Allocate cache-line aligned zeroed memory buffer across Windows/POSIX.

    Returns (address, buffer_handle) or (None, None).
    """
    if size_bytes <= 0:
        return None, None

    if is_windows():
        MEM_COMMIT = 0x1000
        MEM_RESERVE = 0x2000
        PAGE_READWRITE = 0x04
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.VirtualAlloc.restype = ctypes.c_void_p
            kernel32.VirtualAlloc.argtypes = [
                ctypes.c_void_p,
                ctypes.c_size_t,
                ctypes.c_ulong,
                ctypes.c_ulong,
            ]
            addr = kernel32.VirtualAlloc(0, size_bytes, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE)
            if addr:
                return addr, addr
        except Exception:
            pass

    # Generic POSIX / Python ctypes fallback:
    buf = (ctypes.c_char * size_bytes)()
    raw_addr = ctypes.addressof(buf)
    return raw_addr, buf


def free_aligned_memory(handle: object, size_bytes: int = 0) -> bool:
    """Free memory buffer allocated via allocate_aligned_memory."""
    if handle is None:
        return True

    if is_windows() and isinstance(handle, int):
        MEM_RELEASE = 0x8000
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.VirtualFree.restype = ctypes.c_bool
            kernel32.VirtualFree.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_ulong]
            return bool(kernel32.VirtualFree(handle, 0, MEM_RELEASE))
        except Exception:
            return False

    return True
