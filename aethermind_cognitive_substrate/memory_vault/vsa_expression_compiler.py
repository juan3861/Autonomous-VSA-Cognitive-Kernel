"""Fused VSA Expression Graph Compiler & Bytecode VM Frontend.

Lowers symbolic 10,240-bit Vector Symbolic Architecture (VSA) AST expressions
(bind, permute, unpermute, bundle, hamming distance) into a compact L1-resident
`VsaOp` bytecode stream executed inside `aether_cortex_vsa` AVX2 registers in a
single FFI call with zero intermediate Python/NumPy heap allocations.
"""
from __future__ import annotations

import ctypes
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

from ..physical_bridge.native_cortex_dll_singleton import get_native_cortex_dll

WORDS = 160

OP_LOAD_INPUT = 1
OP_LOAD_SEED = 2
OP_BIND_XOR = 3
OP_PERMUTE = 4
OP_UNPERMUTE = 5
OP_BUNDLE_TWO = 6
OP_BUNDLE_RANGE = 7
OP_HAMMING_DIST = 8
OP_STORE_OUTPUT = 9


class VsaOp(ctypes.Structure):
    """Exact #[repr(C)] mirror of Rust `vsa_graph_vm::VsaOp` (16 bytes)."""

    _fields_ = [
        ("opcode", ctypes.c_uint8),
        ("dst", ctypes.c_uint8),
        ("src_a", ctypes.c_uint8),
        ("src_b", ctypes.c_uint8),
        ("imm", ctypes.c_uint64),
    ]


class VSAExpr:
    """Symbolic AST node representing a deferred 10,240-bit VSA expression."""

    def bind(self, other: "VSAExpr") -> "VSABind":
        return VSABind(self, other)

    def __xor__(self, other: "VSAExpr") -> "VSABind":
        return VSABind(self, other)

    def permute(self, steps: int) -> "VSAPermute":
        return VSAPermute(self, steps=steps, inverse=False)

    def unpermute(self, steps: int) -> "VSAPermute":
        return VSAPermute(self, steps=steps, inverse=True)

    def bundle(self, other: "VSAExpr", tie_seed: int = 0x517cc1b727220a95) -> "VSABundleTwo":
        return VSABundleTwo(self, other, tie_seed=tie_seed)


class VSAVar(VSAExpr):
    """Input vector variable referencing an external uint64[160] hypervector."""

    def __init__(self, name: str):
        self.name = name


class VSASeed(VSAExpr):
    """Deterministic orthogonal symbol generated directly inside Rust from seed."""

    def __init__(self, seed: int):
        self.seed = int(seed)


class VSABind(VSAExpr):
    """Holographic XOR binding node: a ^ b."""

    def __init__(self, left: VSAExpr, right: VSAExpr):
        self.left = left
        self.right = right


class VSAPermute(VSAExpr):
    """Circular bit-word permutation node: rho^steps(x) or rho^-steps(x)."""

    def __init__(self, child: VSAExpr, steps: int, inverse: bool = False):
        self.child = child
        self.steps = int(steps)
        self.inverse = bool(inverse)


class VSABundleTwo(VSAExpr):
    """Two-operand majority superposition with deterministic tie-breaking."""

    def __init__(self, left: VSAExpr, right: VSAExpr, tie_seed: int = 0x517cc1b727220a95):
        self.left = left
        self.right = right
        self.tie_seed = int(tie_seed)


class VSAExpressionCompiler:
    """Compiles a list of VSA AST outputs and Hamming queries into native bytecode."""

    def __init__(self):
        self._lib = get_native_cortex_dll()
        try:
            from ..physical_bridge.fast_vsa_bridge import _load_cython_ext
            self._cy = _load_cython_ext()
        except Exception:
            self._cy = None

    @property
    def is_native_ready(self) -> bool:
        return self._lib is not None and hasattr(self._lib, "vsa_eval_graph_bytecode")

    def compile_program(
        self,
        outputs: Optional[List[VSAExpr]] = None,
        hamming_queries: Optional[List[Tuple[VSAExpr, VSAExpr]]] = None,
    ) -> Tuple[List[VsaOp], Dict[str, int]]:
        """Lower symbolic AST expressions into register-allocated `VsaOp` bytecode."""
        outputs = outputs or []
        hamming_queries = hamming_queries or []

        ops: List[VsaOp] = []
        input_slots: Dict[str, int] = {}
        node_reg: Dict[int, int] = {}
        next_reg = 0

        def alloc_reg() -> int:
            nonlocal next_reg
            if next_reg >= 32:
                raise MemoryError("Expression graph exceeds 32 L1 VSA hardware registers.")
            r = next_reg
            next_reg += 1
            return r

        def emit(node: VSAExpr) -> int:
            nid = id(node)
            if nid in node_reg:
                return node_reg[nid]

            if isinstance(node, VSAVar):
                if node.name not in input_slots:
                    input_slots[node.name] = len(input_slots)
                in_idx = input_slots[node.name]
                dst = alloc_reg()
                ops.append(VsaOp(OP_LOAD_INPUT, dst, in_idx, 0, 0))
            elif isinstance(node, VSASeed):
                dst = alloc_reg()
                ops.append(VsaOp(OP_LOAD_SEED, dst, 0, 0, ctypes.c_uint64(node.seed).value))
            elif isinstance(node, VSABind):
                ra = emit(node.left)
                rb = emit(node.right)
                dst = alloc_reg()
                ops.append(VsaOp(OP_BIND_XOR, dst, ra, rb, 0))
            elif isinstance(node, VSAPermute):
                ra = emit(node.child)
                dst = alloc_reg()
                op = OP_UNPERMUTE if node.inverse else OP_PERMUTE
                ops.append(VsaOp(op, dst, ra, 0, ctypes.c_uint64(node.steps).value))
            elif isinstance(node, VSABundleTwo):
                ra = emit(node.left)
                rb = emit(node.right)
                dst = alloc_reg()
                ops.append(VsaOp(OP_BUNDLE_TWO, dst, ra, rb, ctypes.c_uint64(node.tie_seed).value))
            else:
                raise TypeError(f"Unsupported VSA AST node: {type(node)}")

            node_reg[nid] = dst
            return dst

        for out_idx, expr in enumerate(outputs):
            r = emit(expr)
            ops.append(VsaOp(OP_STORE_OUTPUT, out_idx, r, 0, 0))

        for q_idx, (lhs, rhs) in enumerate(hamming_queries):
            ra = emit(lhs)
            rb = emit(rhs)
            ops.append(VsaOp(OP_HAMMING_DIST, q_idx, ra, rb, 0))

        return ops, input_slots

    def execute_compiled(
        self,
        ops: List[VsaOp],
        input_slots: Dict[str, int],
        bindings: Dict[str, np.ndarray],
        n_outputs: int = 0,
        n_scalars: int = 0,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Execute pre-compiled bytecode against concrete uint64[160] bindings."""
        if not self.is_native_ready:
            raise RuntimeError("Native Rust vsa_eval_graph_bytecode symbol unavailable.")

        n_inputs = len(input_slots)
        if n_inputs > 0:
            in_buf = np.empty((n_inputs, WORDS), dtype=np.uint64)
            for name, idx in input_slots.items():
                vec = bindings[name]
                if vec.dtype != np.uint64 or vec.shape != (WORDS,):
                    raise ValueError(f"Input '{name}' must be uint64[{WORDS}].")
                in_buf[idx, :] = vec
            in_ptr = in_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        else:
            in_buf = np.empty((0, WORDS), dtype=np.uint64)
            in_ptr = ctypes.POINTER(ctypes.c_uint64)()

        if n_outputs > 0:
            out_buf = np.zeros((n_outputs, WORDS), dtype=np.uint64)
            out_ptr = out_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        else:
            out_buf = np.empty((0, WORDS), dtype=np.uint64)
            out_ptr = ctypes.POINTER(ctypes.c_uint64)()

        if n_scalars > 0:
            scalar_buf = np.zeros(n_scalars, dtype=np.uint32)
            scalar_ptr = scalar_buf.ctypes.data_as(ctypes.POINTER(ctypes.c_uint32))
        else:
            scalar_buf = np.empty(0, dtype=np.uint32)
            scalar_ptr = ctypes.POINTER(ctypes.c_uint32)()

        op_arr = (VsaOp * len(ops))(*ops)
        if self._cy is not None and hasattr(self._cy, "cy_eval_graph"):
            op_bytes = np.frombuffer(op_arr, dtype=np.uint8)
            status = int(self._cy.cy_eval_graph(op_bytes, len(ops), in_buf, out_buf, scalar_buf))
        else:
            status = int(
                self._lib.vsa_eval_graph_bytecode(
                    op_arr,
                    len(ops),
                    in_ptr,
                    n_inputs,
                    out_ptr,
                    n_outputs,
                    scalar_ptr,
                    n_scalars,
                )
            )
        if status != 0:
            raise RuntimeError(f"vsa_eval_graph_bytecode failed with status={status}")

        return out_buf, scalar_buf

    def evaluate(
        self,
        bindings: Dict[str, np.ndarray],
        outputs: Optional[List[VSAExpr]] = None,
        hamming_queries: Optional[List[Tuple[VSAExpr, VSAExpr]]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Compile and evaluate a VSA expression graph in one fused native call."""
        outputs = outputs or []
        hamming_queries = hamming_queries or []
        ops, slots = self.compile_program(outputs=outputs, hamming_queries=hamming_queries)
        return self.execute_compiled(
            ops=ops,
            input_slots=slots,
            bindings=bindings,
            n_outputs=len(outputs),
            n_scalars=len(hamming_queries),
        )
