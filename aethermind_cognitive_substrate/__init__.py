from __future__ import annotations
import os
from typing import TYPE_CHECKING, Any

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

if TYPE_CHECKING:
    from .sovereign_cortex_runtime import SovereignCortexRuntime

__all__ = ["SovereignCortexRuntime"]


def __getattr__(name: str) -> Any:
    if name == "SovereignCortexRuntime":
        from .sovereign_cortex_runtime import SovereignCortexRuntime
        globals()["SovereignCortexRuntime"] = SovereignCortexRuntime
        return SovereignCortexRuntime
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
