/**
 * @file autonomous_vsa.h
 * @brief Autonomous VSA Cognitive Kernel — Bare-Metal C99 / C++17 C-ABI Header
 * @version 7.2.0
 *
 * Exposes all 20 LTO-compiled Rust C-ABI mathematical kernels for direct embedding
 * in C, C++, robotics middleware, and zero-copy Cython/FFI runtimes.
 */

#ifndef AUTONOMOUS_VSA_H
#define AUTONOMOUS_VSA_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

#define AUTONOMOUS_VSA_WORDS 160
#define AUTONOMOUS_VSA_BITS  10240

/* Fused VSA Expression Graph Bytecode Opcodes */
typedef enum VsaOpCode {
    VSA_OP_LOAD_INPUT   = 1,
    VSA_OP_LOAD_SEED    = 2,
    VSA_OP_BIND_XOR     = 3,
    VSA_OP_PERMUTE      = 4,
    VSA_OP_UNPERMUTE    = 5,
    VSA_OP_BUNDLE_TWO   = 6,
    VSA_OP_BUNDLE_RANGE = 7,
    VSA_OP_HAMMING_DIST = 8,
    VSA_OP_STORE_OUTPUT = 9
} VsaOpCode;

typedef struct VsaOp {
    uint8_t  opcode;
    uint8_t  dst;
    uint8_t  src_a;
    uint8_t  src_b;
    uint64_t imm;
} VsaOp;

/* -------------------------------------------------------------------------- */
/* 1. 10,240-bit Hyperdimensional Computing (VSA) & Fused AVX2 Graph VM       */
/* -------------------------------------------------------------------------- */
void     vsa_create_from_seed(uint64_t seed, uint64_t* out_buf);
void     vsa_bind(const uint64_t* a_buf, const uint64_t* b_buf, uint64_t* out_buf);
uint32_t vsa_hamming_distance(const uint64_t* a_buf, const uint64_t* b_buf);
uint32_t vsa_hamming_distance_batch(const uint64_t* a_buf, const uint64_t* b_buf, uint32_t n_iterations);
void     vsa_bundle_two(const uint64_t* a_buf, const uint64_t* b_buf, uint64_t tie_breaker_seed, uint64_t* out_buf);
double   vsa_resonance_sigma(uint32_t dist);
double   vsa_free_energy_friston(uint32_t hamming_dist);

int32_t  vsa_eval_graph_bytecode(
    const VsaOp* ops_ptr,
    size_t       n_ops,
    const uint64_t* in_vecs_ptr,
    size_t       n_inputs,
    uint64_t*    out_vecs_ptr,
    size_t       n_outputs,
    uint32_t*    out_scalars_ptr,
    size_t       n_scalars
);

/* -------------------------------------------------------------------------- */
/* 2. Biophysical & Neural Solvers (HRM Fixed-Point & Ising Spin Glass)       */
/* -------------------------------------------------------------------------- */
size_t hrm_fast_fixed_point_solve(
    const double* w_ll,
    const double* w_hl,
    const double* w_in,
    const double* b_l,
    const double* z_h,
    const double* x_in,
    double*       z_l_io,
    size_t        dim_fast,
    size_t        dim_slow,
    size_t        dim_in,
    size_t        max_cycles,
    double        tol
);

float ising_compute_energy(
    const float*  j_mat,
    const float*  h_bias,
    const int8_t* spins,
    size_t        num_spins
);

float ising_block_gibbs_relax(
    const float*  j_mat,
    const float*  h_bias,
    int8_t*       spins_io,
    size_t        num_spins,
    float         initial_temp,
    float         final_temp,
    size_t        cooling_steps,
    uint64_t      seed
);

/* -------------------------------------------------------------------------- */
/* 3. Sub-Millisecond Graph Search & Spatial Planning (HNSW & RRT*)           */
/* -------------------------------------------------------------------------- */
float hnsw_cosine_distance_f32(const float* v1, const float* v2, size_t dim);

void hnsw_batch_cosine_distances_f32(
    const float* query,
    const float* candidates_flat,
    float*       out_distances,
    size_t       num_candidates,
    size_t       dim
);

int32_t rrt_star_nearest_and_radius_f64(
    const double* tree_nodes_ptr,
    size_t        n_nodes,
    size_t        dim,
    const double* query_ptr,
    double        radius,
    size_t*       out_nearest_idx,
    double*       out_min_dist,
    size_t*       out_near_indices,
    size_t        max_near,
    size_t*       out_near_count
);

/* -------------------------------------------------------------------------- */
/* 4. Physics, Temporal Logic, Particle Filter, Stability & Sparse Kernels    */
/* -------------------------------------------------------------------------- */
double symplectic_yoshida4_coupled_f64(
    double* q_io,
    double* p_io,
    size_t  dof,
    double  mass,
    double  stiffness,
    double  beta,
    double  dt,
    size_t  steps
);

double stl_globally_upper_robustness_f64(
    const double* trace_ptr,
    size_t        len,
    double        upper_limit
);

int32_t smc_quadratic_track_f64(
    const double* obs_ptr,
    size_t        num_obs,
    size_t        num_particles,
    double        process_noise_std,
    double        obs_noise_std,
    double        init_low,
    double        init_high,
    double        resample_ratio,
    uint64_t      seed,
    double*       out_metrics_ptr
);

double lyapunov_smith_doubling_f64(
    const double* a_ptr,
    const double* q_ptr,
    size_t        n,
    size_t        max_iters,
    double        tol,
    double*       p_out_ptr,
    size_t*       iters_out_ptr
);

double spectral_power_iteration_f64(
    const double* a_ptr,
    size_t        n,
    size_t        max_iters,
    double        tol
);

size_t omp_sparse_project_f64(
    const double* dict_ptr,
    size_t        n_rows,
    size_t        n_cols,
    const double* residual_ptr,
    double*       out_correlations
);

#ifdef __cplusplus
}
#endif

#endif /* AUTONOMOUS_VSA_H */
