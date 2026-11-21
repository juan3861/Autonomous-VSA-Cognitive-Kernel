"""Cross-Platform Cython Zero-Copy Native Extension Builder.

Compiles `fast_vsa_ext.pyx` directly against `autonomous_vsa.h` and the
release Rust C-ABI library (`aether_cortex_vsa`). On Windows, bypasses
setuptools MSVC discovery stalls by invoking `vcvars64.bat` + `cl.exe`
when present, and uses standard `setuptools` on Linux/macOS.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent.parent
INCLUDE_DIR = PROJECT_ROOT / "aether_cortex_vsa" / "include"
LIB_DIR = PROJECT_ROOT / "aether_cortex_vsa" / "target" / "release"
PYX_PATH = ROOT / "fast_vsa_ext.pyx"


def build_windows() -> int:
    import numpy as np

    py_inc = Path(sys.prefix) / "include"
    py_libs = Path(sys.prefix) / "libs"
    np_inc = Path(np.get_include())
    py_ver_tag = f"cp{sys.version_info.major}{sys.version_info.minor}-win_amd64"
    out_pyd = ROOT / f"fast_vsa_ext.{py_ver_tag}.pyd"
    c_out = ROOT / "fast_vsa_ext.c"
    py_lib = f"python{sys.version_info.major}{sys.version_info.minor}.lib"

    vcvars_candidates = [
        Path(r"C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Community\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Professional\VC\Auxiliary\Build\vcvars64.bat"),
        Path(r"C:\Program Files\Microsoft Visual Studio\2022\Enterprise\VC\Auxiliary\Build\vcvars64.bat"),
    ]
    vcvars = next((p for p in vcvars_candidates if p.exists()), None)
    import tempfile

    lines = []
    if vcvars:
        lines.append(f'@call "{vcvars}"')
    lines.append(f'"{sys.executable}" -m cython -3 "{PYX_PATH}" -o "{c_out}"')
    lines.append('if errorlevel 1 exit /b %errorlevel%')
    lines.append(
        f'cl.exe /O2 /MD /LD /I"{py_inc}" /I"{np_inc}" /I"{INCLUDE_DIR}" '
        f'"{c_out}" /Fe:"{out_pyd}" /link '
        f'/LIBPATH:"{py_libs}" /LIBPATH:"{LIB_DIR}" aether_cortex_vsa.dll.lib {py_lib}'
    )
    with tempfile.NamedTemporaryFile("w", suffix=".cmd", delete=False, encoding="utf-8") as tf:
        tf.write("\r\n".join(lines) + "\r\n")
        bat_path = tf.name
    try:
        proc = subprocess.run(["cmd.exe", "/c", bat_path], cwd=str(ROOT))
        return proc.returncode
    finally:
        try:
            os.remove(bat_path)
        except OSError:
            pass


def build_posix() -> int:
    from setuptools import Extension, setup
    from Cython.Build import cythonize
    import numpy as np

    ext = Extension(
        name="aethermind_cognitive_substrate.physical_bridge.fast_vsa_ext",
        sources=[str(PYX_PATH)],
        include_dirs=[str(INCLUDE_DIR), np.get_include()],
        library_dirs=[str(LIB_DIR)],
        libraries=["aether_cortex_vsa"],
        runtime_library_dirs=[str(LIB_DIR)],
    )
    os.chdir(str(PROJECT_ROOT))
    setup(
        name="fast_vsa_ext",
        ext_modules=cythonize([ext], language_level="3"),
        script_args=["build_ext", "--inplace"],
    )
    return 0


if __name__ == "__main__":
    rc = build_windows() if sys.platform.startswith("win") else build_posix()
    raise SystemExit(rc)
