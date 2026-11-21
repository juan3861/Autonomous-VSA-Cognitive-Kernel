# cython: language_level=3, boundscheck=False, wraparound=False, cdivision=True
"""Zero-Copy Cython C-Extension wrapping Autonomous VSA Rust C-ABI (`autonomous_vsa.h`)."""

from libc.stdint cimport uint8_t, uint32_t, uint64_t, int32_t
from libc.stddef cimport size_t
import numpy as np
cimport numpy as cnp

cdef extern from "autonomous_vsa.h":
    ctypedef struct VsaOp:
        uint8_t  opcode
        uint8_t  dst
        uint8_t  src_a
        uint8_t  src_b
        uint64_t imm

    void     vsa_create_from_seed(uint64_t seed, uint64_t* out_buf) nogil
    void     vsa_bind(const uint64_t* a_buf, const uint64_t* b_buf, uint64_t* out_buf) nogil
    uint32_t vsa_hamming_distance(const uint64_t* a_buf, const uint64_t* b_buf) nogil
    uint32_t vsa_hamming_distance_batch(const uint64_t* a_buf, const uint64_t* b_buf, uint32_t n_iterations) nogil
    void     vsa_bundle_two(const uint64_t* a_buf, const uint64_t* b_buf, uint64_t tie_breaker_seed, uint64_t* out_buf) nogil
    int32_t  vsa_eval_graph_bytecode(
        const VsaOp*    ops_ptr,
        size_t          n_ops,
        const uint64_t* in_vecs_ptr,
        size_t          n_inputs,
        uint64_t*       out_vecs_ptr,
        size_t          n_outputs,
        uint32_t*       out_scalars_ptr,
        size_t          n_scalars
    ) nogil
    double   spectral_power_iteration_f64(const double* a_ptr, size_t n, size_t max_iters, double tol) nogil
    double   lyapunov_smith_doubling_f64(
        const double* a_ptr,
        const double* q_ptr,
        size_t        n,
        size_t        max_iters,
        double        tol,
        double*       p_out_ptr,
        size_t*       iters_out_ptr
    ) nogil


DEF VSA_WORDS = 160


def cy_create_from_seed(uint64_t seed) -> cnp.ndarray:
    """Allocate and fill a 10,240-bit uint64[160] hypervector directly in C."""
    cdef cnp.ndarray[uint64_t, ndim=1] out = np.empty(VSA_WORDS, dtype=np.uint64)
    cdef uint64_t* ptr = <uint64_t*>out.data
    with nogil:
        vsa_create_from_seed(seed, ptr)
    return out


def cy_bind_into(const uint64_t[::1] a, const uint64_t[::1] b, uint64_t[::1] out) -> None:
    """Zero-allocation, zero-copy XOR bind directly into preallocated output buffer."""
    if a.shape[0] != VSA_WORDS or b.shape[0] != VSA_WORDS or out.shape[0] != VSA_WORDS:
        raise ValueError("Hypervector buffers must have length 160 (uint64).")
    with nogil:
        vsa_bind(&a[0], &b[0], &out[0])


def cy_bind(const uint64_t[::1] a, const uint64_t[::1] b) -> cnp.ndarray:
    """Return a^b as uint64[160] with zero Python ctypes overhead."""
    cdef cnp.ndarray[uint64_t, ndim=1] out = np.empty(VSA_WORDS, dtype=np.uint64)
    cdef uint64_t* out_ptr = <uint64_t*>out.data
    if a.shape[0] != VSA_WORDS or b.shape[0] != VSA_WORDS:
        raise ValueError("Hypervector buffers must have length 160 (uint64).")
    with nogil:
        vsa_bind(&a[0], &b[0], out_ptr)
    return out


def cy_hamming_distance(const uint64_t[::1] a, const uint64_t[::1] b) -> uint32_t:
    """Zero-overhead hardware POPCNT Hamming distance over 10,240 bits."""
    if a.shape[0] != VSA_WORDS or b.shape[0] != VSA_WORDS:
        raise ValueError("Hypervector buffers must have length 160 (uint64).")
    cdef uint32_t d
    with nogil:
        d = vsa_hamming_distance(&a[0], &b[0])
    return d


def cy_hamming_distance_batch(const uint64_t[::1] a, const uint64_t[::1] b, uint32_t n_iterations) -> uint32_t:
    """Batched native Hamming distance execution inside nogil Rust loop."""
    if a.shape[0] != VSA_WORDS or b.shape[0] != VSA_WORDS:
        raise ValueError("Hypervector buffers must have length 160 (uint64).")
    cdef uint32_t d
    with nogil:
        d = vsa_hamming_distance_batch(&a[0], &b[0], n_iterations)
    return d


def cy_spectral_power_iteration(const double[:, ::1] a, size_t max_iters=500, double tol=1e-11) -> float:
    """Zero-copy Cython dispatch to Rust LTO Rayleigh spectral radius estimator."""
    cdef size_t n = a.shape[0]
    if n == 0 or a.shape[1] != n:
        raise ValueError("Matrix must be non-empty square float64.")
    cdef double rho
    with nogil:
        rho = spectral_power_iteration_f64(&a[0, 0], n, max_iters, tol)
    return rho


def cy_eval_graph(
    const uint8_t[::1] ops_bytes,
    size_t n_ops,
    const uint64_t[:, ::1] in_vecs,
    uint64_t[:, ::1] out_vecs,
    uint32_t[::1] out_scalars,
) -> int:
    """Zero-copy Cython dispatch to the Fused AVX2 VSA Expression Graph VM."""
    if ops_bytes.shape[0] < n_ops * sizeof(VsaOp):
        raise ValueError("Bytecode buffer smaller than n_ops * sizeof(VsaOp).")
    cdef const VsaOp* ops_ptr = <const VsaOp*>&ops_bytes[0]
    cdef const uint64_t* in_ptr = &in_vecs[0, 0] if in_vecs.shape[0] > 0 else NULL
    cdef uint64_t* out_ptr = &out_vecs[0, 0] if out_vecs.shape[0] > 0 else NULL
    cdef uint32_t* sc_ptr = &out_scalars[0] if out_scalars.shape[0] > 0 else NULL
    cdef int32_t st
    with nogil:
        st = vsa_eval_graph_bytecode(
            ops_ptr, n_ops,
            in_ptr, <size_t>in_vecs.shape[0],
            out_ptr, <size_t>out_vecs.shape[0],
            sc_ptr, <size_t>out_scalars.shape[0],
        )
    return int(st)


def cy_lyapunov_smith_doubling(
    const double[:, ::1] a,
    const double[:, ::1] q,
    double[:, ::1] p_out,
    size_t max_iters=64,
    double tol=1e-12,
):
    """Zero-copy Cython dispatch to Rust LTO Smith Doubling Lyapunov solver."""
    cdef size_t n = a.shape[0]
    if n == 0 or a.shape[1] != n or q.shape[0] != n or q.shape[1] != n or p_out.shape[0] != n or p_out.shape[1] != n:
        raise ValueError("Matrices A, Q, P_out must have identical square shape (n, n).")
    cdef size_t iters_used = 0
    cdef double res
    with nogil:
        res = lyapunov_smith_doubling_f64(&a[0, 0], &q[0, 0], n, max_iters, tol, &p_out[0, 0], &iters_used)
    return (res, int(iters_used))
