pub mod vsa_graph_vm;
pub use vsa_graph_vm::{VsaOp, vsa_eval_graph_bytecode};
pub mod vsa_jit_x64;
pub use vsa_jit_x64::{JitXorHandle, vsa_jit_compile_xor_chain, vsa_jit_exec_xor_chain, vsa_jit_free_xor_chain};

#[no_mangle]
pub extern "C" fn vsa_wasm_alloc(bytes: usize) -> *mut u8 {
    if bytes == 0 {
        return core::ptr::null_mut();
    }
    let mut buf = Vec::<u8>::with_capacity(bytes);
    let ptr = buf.as_mut_ptr();
    core::mem::forget(buf);
    ptr
}

#[no_mangle]
pub extern "C" fn vsa_wasm_free(ptr: *mut u8, bytes: usize) {
    if ptr.is_null() || bytes == 0 {
        return;
    }
    unsafe {
        let _ = Vec::from_raw_parts(ptr, 0, bytes);
    }
}

pub const WORDS: usize = 160;
pub const BITS: usize = WORDS * 64;
pub const EXPECTED_RANDOM_DIST: f64 = (BITS as f64) * 0.5; // 5120.0
pub const STD_DEV_BITS: f64 = 50.59644256269407; // sqrt(10240 * 0.25)

#[derive(Clone, Copy, PartialEq, Eq)]
#[repr(align(32))]
pub struct Hypervector(pub [u64; WORDS]);

impl Hypervector {
    pub const fn zero() -> Self {
        Self([0u64; WORDS])
    }

    pub fn from_seed(mut state: u64) -> Self {
        let mut words = [0u64; WORDS];
        for w in words.iter_mut() {
            state = state.wrapping_add(0x9e3779b97f4a7c15);
            let mut z = state;
            z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
            z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
            *w = z ^ (z >> 31);
        }
        Self(words)
    }

    #[inline(always)]
    pub fn bind(&self, other: &Self) -> Self {
        let mut out = [0u64; WORDS];
        for i in 0..WORDS {
            out[i] = self.0[i] ^ other.0[i];
        }
        Self(out)
    }

    #[inline(always)]
    pub fn hamming_distance(&self, other: &Self) -> usize {
        let mut dist = 0usize;
        for i in 0..WORDS {
            dist += (self.0[i] ^ other.0[i]).count_ones() as usize;
        }
        dist
    }
}

// ============================================================================
// EXPORTAÇÃO C-ABI NATIVA PARA CARREGAMENTO DIRETO EM PYTHON (ctypes / FFI)
// Zero Cópia, Zero Overhead de Processo, Batched SIMD Execution
// ============================================================================

#[no_mangle]
pub extern "C" fn vsa_create_from_seed(seed: u64, out_buf: *mut u64) {
    if out_buf.is_null() { return; }
    let hv = Hypervector::from_seed(seed);
    unsafe {
        std::ptr::copy_nonoverlapping(hv.0.as_ptr(), out_buf, WORDS);
    }
}

#[no_mangle]
pub extern "C" fn vsa_bind(a_buf: *const u64, b_buf: *const u64, out_buf: *mut u64) {
    if a_buf.is_null() || b_buf.is_null() || out_buf.is_null() { return; }
    unsafe {
        for i in 0..WORDS {
            *out_buf.add(i) = *a_buf.add(i) ^ *b_buf.add(i);
        }
    }
}

#[no_mangle]
pub extern "C" fn vsa_hamming_distance(a_buf: *const u64, b_buf: *const u64) -> u32 {
    if a_buf.is_null() || b_buf.is_null() { return 0; }
    let mut dist = 0u32;
    unsafe {
        for i in 0..WORDS {
            dist += (*a_buf.add(i) ^ *b_buf.add(i)).count_ones();
        }
    }
    dist
}

/// Execução em lote nativa bare-metal: elimina 100% da sobrecarga de crossing de ponte FFI!
#[no_mangle]
pub extern "C" fn vsa_hamming_distance_batch(a_buf: *const u64, b_buf: *const u64, n_iterations: u32) -> u32 {
    if a_buf.is_null() || b_buf.is_null() { return 0; }
    let mut dist = 0u32;
    unsafe {
        for _ in 0..n_iterations {
            dist = 0;
            for i in 0..WORDS {
                dist += (*a_buf.add(i) ^ *b_buf.add(i)).count_ones();
            }
        }
    }
    dist
}

#[no_mangle]
pub extern "C" fn vsa_bundle_two(a_buf: *const u64, b_buf: *const u64, tie_breaker_seed: u64, out_buf: *mut u64) {
    if a_buf.is_null() || b_buf.is_null() || out_buf.is_null() { return; }
    let tie = Hypervector::from_seed(tie_breaker_seed);
    unsafe {
        for i in 0..WORDS {
            let a = *a_buf.add(i);
            let b = *b_buf.add(i);
            let t = tie.0[i];
            *out_buf.add(i) = (a & b) | (b & t) | (a & t);
        }
    }
}

#[no_mangle]
pub extern "C" fn vsa_resonance_sigma(dist: u32) -> f64 {
    (EXPECTED_RANDOM_DIST - dist as f64) / STD_DEV_BITS
}

#[no_mangle]
pub extern "C" fn vsa_free_energy_friston(hamming_dist: u32) -> f64 {
    let dist = hamming_dist as f64;
    (dist / EXPECTED_RANDOM_DIST).min(1.0)
}

// ============================================================================
// HIERARCHICAL REASONING MODEL (HRM / TRM) BARE-METAL FIXED-POINT SOLVER
// Banacha Contraction Mapping Theorem solved in native CPU registers
// Precomputes static bias projections; executes Jacobi iterations with zero allocations.
// ============================================================================

#[no_mangle]
pub extern "C" fn hrm_fast_fixed_point_solve(
    w_ll: *const f64,
    w_hl: *const f64,
    w_in: *const f64,
    b_l: *const f64,
    z_h: *const f64,
    x_in: *const f64,
    z_l_io: *mut f64,
    dim_fast: usize,
    dim_slow: usize,
    dim_in: usize,
    max_cycles: usize,
    tol: f64,
) -> usize {
    if w_ll.is_null() || z_l_io.is_null() || dim_fast == 0 {
        return 0;
    }
    unsafe {
        // Precompute static bias term: bias[i] = b_l[i] + sum(W_HL * z_h) + sum(W_in * x_in)
        let mut bias = vec![0.0f64; dim_fast];
        for i in 0..dim_fast {
            let mut val = if !b_l.is_null() { *b_l.add(i) } else { 0.0 };
            if !w_hl.is_null() && !z_h.is_null() {
                for k in 0..dim_slow {
                    val += *w_hl.add(i * dim_slow + k) * *z_h.add(k);
                }
            }
            if !w_in.is_null() && !x_in.is_null() {
                for m in 0..dim_in {
                    val += *w_in.add(i * dim_in + m) * *x_in.add(m);
                }
            }
            bias[i] = val;
        }

        let mut current = vec![0.0f64; dim_fast];
        for i in 0..dim_fast {
            current[i] = *z_l_io.add(i);
        }

        let mut next = vec![0.0f64; dim_fast];
        let mut converged_cycles = max_cycles;

        for cycle in 0..max_cycles {
            let mut delta_sq = 0.0f64;
            for i in 0..dim_fast {
                let row_offset = i * dim_fast;
                let mut sum = bias[i];
                for j in 0..dim_fast {
                    sum += *w_ll.add(row_offset + j) * current[j];
                }
                let val_next = sum.tanh();
                next[i] = val_next;
                let diff = val_next - current[i];
                delta_sq += diff * diff;
            }

            let delta = delta_sq.sqrt();
            current.copy_from_slice(&next);

            if delta < tol {
                converged_cycles = cycle + 1;
                break;
            }
        }

        for i in 0..dim_fast {
            *z_l_io.add(i) = current[i];
        }

        converged_cycles
    }
}

// ============================================================================
// THERMODYNAMIC ISING SPIN GLASS BARE-METAL ACCELERATOR (EXTROPIC PARADIGM)
// High-performance Two-Color Block Gibbs relaxation for N spins (up to 4096+)
// ============================================================================

#[no_mangle]
pub extern "C" fn ising_compute_energy(
    j_mat: *const f32,
    h_bias: *const f32,
    spins: *const i8,
    num_spins: usize,
) -> f32 {
    if j_mat.is_null() || spins.is_null() || num_spins == 0 {
        return 0.0;
    }
    unsafe {
        let mut interaction_energy = 0.0f32;
        let mut field_energy = 0.0f32;

        for i in 0..num_spins {
            let s_i = *spins.add(i) as f32;
            let row_offset = i * num_spins;
            let mut row_sum = 0.0f32;
            for j in 0..num_spins {
                row_sum += *j_mat.add(row_offset + j) * (*spins.add(j) as f32);
            }
            interaction_energy += s_i * row_sum;

            if !h_bias.is_null() {
                field_energy += *h_bias.add(i) * s_i;
            }
        }

        -0.5 * interaction_energy - field_energy
    }
}

#[no_mangle]
pub extern "C" fn ising_block_gibbs_relax(
    j_mat: *const f32,
    h_bias: *const f32,
    spins_io: *mut i8,
    num_spins: usize,
    initial_temp: f32,
    final_temp: f32,
    cooling_steps: usize,
    mut seed: u64,
) -> f32 {
    if j_mat.is_null() || spins_io.is_null() || num_spins == 0 || cooling_steps == 0 {
        return 0.0;
    }
    if seed == 0 {
        seed = 0x853c49e6748fea9b;
    }

    unsafe {
        let mut current_spins = vec![0i8; num_spins];
        let mut best_spins = vec![0i8; num_spins];
        for i in 0..num_spins {
            current_spins[i] = *spins_io.add(i);
            best_spins[i] = current_spins[i];
        }

        let mut best_energy = ising_compute_energy(j_mat, h_bias, current_spins.as_ptr(), num_spins);
        let decay = if cooling_steps > 1 {
            (final_temp / initial_temp.max(1e-4)).powf(1.0 / (cooling_steps - 1) as f32)
        } else {
            1.0
        };
        let mut temp = initial_temp;

        let mut rng_state = seed;
        let mut next_rand = move || -> f32 {
            rng_state ^= rng_state << 13;
            rng_state ^= rng_state >> 7;
            rng_state ^= rng_state << 17;
            (rng_state & 0xFFFFFF) as f32 / 16777216.0f32
        };

        for _ in 0..cooling_steps {
            let beta = 1.0 / temp.max(1e-4);

            // Update Block A (even indices)
            for i in (0..num_spins).step_by(2) {
                let row_offset = i * num_spins;
                let mut field = if !h_bias.is_null() { *h_bias.add(i) } else { 0.0 };
                for j in 0..num_spins {
                    field += *j_mat.add(row_offset + j) * (current_spins[j] as f32);
                }
                let prob_plus = 1.0 / (1.0 + (-2.0 * beta * field).exp());
                current_spins[i] = if next_rand() < prob_plus { 1 } else { -1 };
            }

            // Update Block B (odd indices)
            for i in (1..num_spins).step_by(2) {
                let row_offset = i * num_spins;
                let mut field = if !h_bias.is_null() { *h_bias.add(i) } else { 0.0 };
                for j in 0..num_spins {
                    field += *j_mat.add(row_offset + j) * (current_spins[j] as f32);
                }
                let prob_plus = 1.0 / (1.0 + (-2.0 * beta * field).exp());
                current_spins[i] = if next_rand() < prob_plus { 1 } else { -1 };
            }

            let energy = ising_compute_energy(j_mat, h_bias, current_spins.as_ptr(), num_spins);
            if energy < best_energy {
                best_energy = energy;
                best_spins.copy_from_slice(&current_spins);
            }

            temp *= decay;
        }

        // Write optimal ground state spins back
        for i in 0..num_spins {
            *spins_io.add(i) = best_spins[i];
        }

        best_energy
    }
}

/// Computes normalized cosine distance `max(0.0, 1.0 - dot(v1, v2))` in bare-metal Rust SIMD.
#[no_mangle]
pub extern "C" fn hnsw_cosine_distance_f32(
    v1: *const f32,
    v2: *const f32,
    dim: usize,
) -> f32 {
    if v1.is_null() || v2.is_null() || dim == 0 {
        return 1.0;
    }
    unsafe {
        let mut dot: f32 = 0.0;
        for i in 0..dim {
            dot += *v1.add(i) * *v2.add(i);
        }
        (1.0 - dot).max(0.0)
    }
}

/// Batch cosine distance evaluation for HNSW adjacency lists in bare-metal Rust.
#[no_mangle]
pub extern "C" fn hnsw_batch_cosine_distances_f32(
    query: *const f32,
    candidates_flat: *const f32,
    out_distances: *mut f32,
    num_candidates: usize,
    dim: usize,
) {
    if query.is_null() || candidates_flat.is_null() || out_distances.is_null() || dim == 0 {
        return;
    }
    unsafe {
        for c in 0..num_candidates {
            let base = c * dim;
            let mut dot: f32 = 0.0;
            for i in 0..dim {
                dot += *query.add(i) * *candidates_flat.add(base + i);
            }
            *out_distances.add(c) = (1.0 - dot).max(0.0);
        }
    }
}

// ============================================================================
// BARE-METAL YOSHIDA-4 SYMPLECTIC INTEGRATOR & STL QUANTITATIVE KERNELS
// Compiled C-ABI kernels for sub-millisecond Hamiltonian physics & formal LTL/STL
// ============================================================================

#[inline(always)]
unsafe fn hamiltonian_energy_and_grad(
    q: &[f64],
    p: &[f64],
    grad: &mut [f64],
    mass: f64,
    stiffness: f64,
    beta: f64,
) -> f64 {
    let n = q.len();
    let mut kin = 0.0f64;
    let mut pot = 0.0f64;
    for i in 0..n {
        let qi = q[i];
        let pi = p[i];
        let q2 = qi * qi;
        kin += 0.5 * pi * pi / mass;
        pot += 0.5 * stiffness * q2 + 0.25 * beta * q2 * q2;
        grad[i] = stiffness * qi + beta * qi * q2;
    }
    for i in 0..n.saturating_sub(1) {
        let diff = q[i] - q[i + 1];
        pot += 0.1 * diff * diff;
        grad[i] += 0.2 * diff;
        grad[i + 1] -= 0.2 * diff;
    }
    kin + pot
}

#[no_mangle]
pub extern "C" fn symplectic_yoshida4_coupled_f64(
    q_io: *mut f64,
    p_io: *mut f64,
    dof: usize,
    mass: f64,
    stiffness: f64,
    beta: f64,
    dt: f64,
    steps: usize,
) -> f64 {
    if q_io.is_null() || p_io.is_null() || dof == 0 || steps == 0 {
        return -1.0;
    }
    unsafe {
        let mut q = vec![0.0f64; dof];
        let mut p = vec![0.0f64; dof];
        let mut grad = vec![0.0f64; dof];
        for i in 0..dof {
            q[i] = *q_io.add(i);
            p[i] = *p_io.add(i);
        }

        let w1: f64 = 1.3512071919596578;
        let w0: f64 = -1.7024143839193153;
        let weights = [w1, w0, w1];

        let h0 = hamiltonian_energy_and_grad(&q, &p, &mut grad, mass, stiffness, beta);
        let mut max_drift = 0.0f64;

        for _ in 0..steps {
            for &w in &weights {
                let hdt = w * dt;
                let _ = hamiltonian_energy_and_grad(&q, &p, &mut grad, mass, stiffness, beta);
                for i in 0..dof {
                    p[i] -= 0.5 * hdt * grad[i];
                    q[i] += hdt * (p[i] / mass);
                }
                let _ = hamiltonian_energy_and_grad(&q, &p, &mut grad, mass, stiffness, beta);
                for i in 0..dof {
                    p[i] -= 0.5 * hdt * grad[i];
                }
            }
            let ht = hamiltonian_energy_and_grad(&q, &p, &mut grad, mass, stiffness, beta);
            let drift = (ht - h0).abs();
            if drift > max_drift {
                max_drift = drift;
            }
        }

        for i in 0..dof {
            *q_io.add(i) = q[i];
            *p_io.add(i) = p[i];
        }
        max_drift
    }
}

/// Evaluates Signal Temporal Logic Globally upper-bound robustness: min_t (upper_limit - trace[t]).
#[no_mangle]
pub extern "C" fn stl_globally_upper_robustness_f64(
    trace_ptr: *const f64,
    len: usize,
    upper_limit: f64,
) -> f64 {
    if trace_ptr.is_null() || len == 0 {
        return -1e9;
    }
    unsafe {
        let mut min_rob = f64::INFINITY;
        for i in 0..len {
            let margin = upper_limit - *trace_ptr.add(i);
            if margin < min_rob {
                min_rob = margin;
            }
        }
        min_rob
    }
}

#[inline(always)]
fn splitmix64(state: &mut u64) -> u64 {
    *state = state.wrapping_add(0x9e3779b97f4a7c15);
    let mut z = *state;
    z = (z ^ (z >> 30)).wrapping_mul(0xbf58476d1ce4e5b9);
    z = (z ^ (z >> 27)).wrapping_mul(0x94d049bb133111eb);
    z ^ (z >> 31)
}

#[inline(always)]
fn rand_uniform01(state: &mut u64) -> f64 {
    ((splitmix64(state) >> 11) as f64) * (1.0 / ((1u64 << 53) as f64))
}

#[inline(always)]
fn rand_normal(state: &mut u64) -> f64 {
    let mut u1 = rand_uniform01(state);
    if u1 < 1e-12 {
        u1 = 1e-12;
    }
    let u2 = rand_uniform01(state);
    (-2.0 * u1.ln()).sqrt() * (std::f64::consts::TAU * u2).cos()
}

/// Bare-Metal Sequential Monte Carlo (Bootstrap Particle Filter) for 1D quadratic bimodal tracking:
/// y_t = x_t^2 + eps. Uses Log-Sum-Exp normalization and O(N) systematic resampling.
/// `out_metrics_ptr` must hold at least 9 f64 values:
/// [0]=mean, [1]=var, [2]=min_neff, [3]=final_neff, [4]=resample_count,
/// [5]=pos_mass (>0.5), [6]=neg_mass (<-0.5), [7]=pos_centroid, [8]=neg_centroid.
#[no_mangle]
pub extern "C" fn smc_quadratic_track_f64(
    obs_ptr: *const f64,
    num_obs: usize,
    num_particles: usize,
    process_noise_std: f64,
    obs_noise_std: f64,
    init_low: f64,
    init_high: f64,
    resample_ratio: f64,
    seed: u64,
    out_metrics_ptr: *mut f64,
) -> i32 {
    if obs_ptr.is_null() || out_metrics_ptr.is_null() || num_obs == 0 || num_particles < 16 {
        return -1;
    }
    unsafe {
        let mut rng = if seed == 0 { 202619u64 } else { seed };
        let span = init_high - init_low;
        let inv_n = 1.0 / (num_particles as f64);
        let inv_two_var = 1.0 / (2.0 * obs_noise_std * obs_noise_std + 1e-12);

        let mut particles = vec![0.0f64; num_particles];
        let mut next_particles = vec![0.0f64; num_particles];
        let mut weights = vec![inv_n; num_particles];
        let mut log_w = vec![0.0f64; num_particles];
        let mut cdf = vec![0.0f64; num_particles];

        for i in 0..num_particles {
            particles[i] = init_low + span * rand_uniform01(&mut rng);
        }

        let mut min_neff = num_particles as f64;
        let mut final_neff = num_particles as f64;
        let mut resample_count: usize = 0;

        for t in 0..num_obs {
            let y_t = *obs_ptr.add(t);
            let mut max_lw = f64::NEG_INFINITY;

            for i in 0..num_particles {
                let x = 0.98 * particles[i] + process_noise_std * rand_normal(&mut rng);
                particles[i] = x;
                let err = x * x - y_t;
                let ll = -(err * err) * inv_two_var;
                let lw = weights[i].max(1e-300).ln() + ll;
                log_w[i] = lw;
                if lw > max_lw {
                    max_lw = lw;
                }
            }

            let mut sum_w = 0.0f64;
            if max_lw.is_finite() {
                for i in 0..num_particles {
                    let v = (log_w[i] - max_lw).clamp(-500.0, 50.0).exp();
                    weights[i] = v;
                    sum_w += v;
                }
            }
            if sum_w <= 1e-18 || !sum_w.is_finite() {
                for i in 0..num_particles {
                    weights[i] = inv_n;
                }
            } else {
                let inv_sum = 1.0 / sum_w;
                for i in 0..num_particles {
                    weights[i] *= inv_sum;
                }
            }

            let mut sum_sq = 0.0f64;
            for i in 0..num_particles {
                sum_sq += weights[i] * weights[i];
            }
            let neff = 1.0 / sum_sq.max(1e-18);
            if neff < min_neff {
                min_neff = neff;
            }
            final_neff = neff;

            if neff < resample_ratio * (num_particles as f64) {
                let mut acc = 0.0f64;
                for i in 0..num_particles {
                    acc += weights[i];
                    cdf[i] = acc;
                }
                cdf[num_particles - 1] = 1.0;

                let u0 = rand_uniform01(&mut rng) * inv_n;
                let mut j = 0usize;
                let jitter_std = process_noise_std * 0.15;
                for k in 0..num_particles {
                    let pos = u0 + (k as f64) * inv_n;
                    while j + 1 < num_particles && cdf[j] < pos {
                        j += 1;
                    }
                    next_particles[k] = particles[j] + jitter_std * rand_normal(&mut rng);
                }
                std::mem::swap(&mut particles, &mut next_particles);
                for i in 0..num_particles {
                    weights[i] = inv_n;
                }
                resample_count += 1;
            }
        }

        let mut mean = 0.0f64;
        let mut pos_mass = 0.0f64;
        let mut neg_mass = 0.0f64;
        let mut pos_wsum = 0.0f64;
        let mut neg_wsum = 0.0f64;
        for i in 0..num_particles {
            let x = particles[i];
            let w = weights[i];
            mean += w * x;
            if x > 0.5 {
                pos_mass += w;
                pos_wsum += w * x;
            } else if x < -0.5 {
                neg_mass += w;
                neg_wsum += w * x;
            }
        }
        let mut var = 0.0f64;
        for i in 0..num_particles {
            let d = particles[i] - mean;
            var += weights[i] * d * d;
        }

        *out_metrics_ptr.add(0) = mean;
        *out_metrics_ptr.add(1) = var;
        *out_metrics_ptr.add(2) = min_neff;
        *out_metrics_ptr.add(3) = final_neff;
        *out_metrics_ptr.add(4) = resample_count as f64;
        *out_metrics_ptr.add(5) = pos_mass;
        *out_metrics_ptr.add(6) = neg_mass;
        *out_metrics_ptr.add(7) = if pos_mass > 1e-9 { pos_wsum / pos_mass } else { 0.0 };
        *out_metrics_ptr.add(8) = if neg_mass > 1e-9 { neg_wsum / neg_mass } else { 0.0 };
        0
    }
}

#[inline(always)]
fn matmul_nn(a: &[f64], b: &[f64], out: &mut [f64], n: usize) {
    for v in out.iter_mut() {
        *v = 0.0;
    }
    for i in 0..n {
        let row_i = i * n;
        for k in 0..n {
            let aik = a[row_i + k];
            let row_k = k * n;
            for j in 0..n {
                out[row_i + j] += aik * b[row_k + j];
            }
        }
    }
}

#[inline(always)]
fn matmul_at_b_a(a: &[f64], p: &[f64], tmp: &mut [f64], out: &mut [f64], n: usize) {
    // tmp = P * A
    matmul_nn(p, a, tmp, n);
    // out = A^T * tmp
    for v in out.iter_mut() {
        *v = 0.0;
    }
    for k in 0..n {
        let row_k = k * n;
        for i in 0..n {
            let aki = a[row_k + i]; // A^T[i, k] = A[k, i]
            let out_i = i * n;
            for j in 0..n {
                out[out_i + j] += aki * tmp[row_k + j];
            }
        }
    }
}

/// Bare-Metal Discrete Lyapunov / Stein Equation Solver via Smith Quadratic Doubling:
/// Solves A^T * P * A - P = -Q for row-major n x n matrices (n <= 64).
/// Writes symmetric P into `p_out_ptr` (n*n f64) and returns Frobenius residual ||A^T P A - P + Q||_F.
#[no_mangle]
pub extern "C" fn lyapunov_smith_doubling_f64(
    a_ptr: *const f64,
    q_ptr: *const f64,
    n: usize,
    max_iters: usize,
    tol: f64,
    p_out_ptr: *mut f64,
    iters_out_ptr: *mut usize,
) -> f64 {
    if a_ptr.is_null() || q_ptr.is_null() || p_out_ptr.is_null() || n == 0 || n > 64 {
        return -1.0;
    }
    let nn = n * n;
    unsafe {
        let mut a0 = vec![0.0f64; nn];
        let mut q0 = vec![0.0f64; nn];
        for i in 0..nn {
            a0[i] = *a_ptr.add(i);
            q0[i] = *q_ptr.add(i);
        }
        // Symmetrize Q
        for i in 0..n {
            for j in (i + 1)..n {
                let sym = 0.5 * (q0[i * n + j] + q0[j * n + i]);
                q0[i * n + j] = sym;
                q0[j * n + i] = sym;
            }
        }

        let mut ak = a0.clone();
        let mut ak_next = vec![0.0f64; nn];
        let mut pk = q0.clone();
        let mut delta = vec![0.0f64; nn];
        let mut tmp = vec![0.0f64; nn];

        let mut iters_used: usize = 0;
        for it in 0..max_iters {
            iters_used = it + 1;
            matmul_at_b_a(&ak, &pk, &mut tmp, &mut delta, n);
            let mut delta_sq = 0.0f64;
            for i in 0..nn {
                let d = delta[i];
                delta_sq += d * d;
                pk[i] += d;
            }
            for i in 0..n {
                for j in (i + 1)..n {
                    let sym = 0.5 * (pk[i * n + j] + pk[j * n + i]);
                    pk[i * n + j] = sym;
                    pk[j * n + i] = sym;
                }
            }
            if delta_sq.sqrt() < tol {
                break;
            }
            matmul_nn(&ak, &ak, &mut ak_next, n);
            std::mem::swap(&mut ak, &mut ak_next);
        }

        // Compute residual ||A^T P A - P + Q||_F
        matmul_at_b_a(&a0, &pk, &mut tmp, &mut delta, n);
        let mut res_sq = 0.0f64;
        for i in 0..nn {
            let r = delta[i] - pk[i] + q0[i];
            res_sq += r * r;
            *p_out_ptr.add(i) = pk[i];
        }
        if !iters_out_ptr.is_null() {
            *iters_out_ptr = iters_used;
        }
        res_sq.sqrt()
    }
}

/// Bare-Metal LTO Dominant Eigenvalue / Spectral Radius Estimator via Power Iteration (Rayleigh Quotient).
#[no_mangle]
pub extern "C" fn spectral_power_iteration_f64(
    a_ptr: *const f64,
    n: usize,
    max_iters: usize,
    tol: f64,
) -> f64 {
    if a_ptr.is_null() || n == 0 || max_iters == 0 {
        return -1.0;
    }
    unsafe {
        let a = std::slice::from_raw_parts(a_ptr, n * n);
        let mut v = vec![1.0f64 / (n as f64).sqrt(); n];
        let mut w = vec![0.0f64; n];
        let mut lambda_prev = 0.0f64;

        for _ in 0..max_iters {
            for i in 0..n {
                let row = i * n;
                let mut acc = 0.0f64;
                for j in 0..n {
                    acc += a[row + j] * v[j];
                }
                w[i] = acc;
            }
            let mut norm_sq = 0.0f64;
            let mut rayleigh = 0.0f64;
            for i in 0..n {
                norm_sq += w[i] * w[i];
                rayleigh += v[i] * w[i];
            }
            let norm = norm_sq.sqrt();
            if norm < 1e-15 {
                return 0.0;
            }
            let inv_norm = 1.0 / norm;
            for i in 0..n {
                v[i] = w[i] * inv_norm;
            }
            if (rayleigh - lambda_prev).abs() < tol {
                return rayleigh.abs();
            }
            lambda_prev = rayleigh;
        }
        lambda_prev.abs()
    }
}


/// Projeção esparsa OMP (Orthogonal Matching Pursuit) de ultra-alta velocidade.
/// Dado um dicionário D (col-major N x K) e resíduo r (N),
/// calcula argmax_j |D_j^T r| e retorna o índice ótimo.
#[no_mangle]
pub extern "C" fn omp_sparse_project_f64(
    dict_ptr: *const f64,
    n_rows: usize,
    n_cols: usize,
    residual_ptr: *const f64,
    out_correlations: *mut f64,
) -> usize {
    if dict_ptr.is_null() || residual_ptr.is_null() || n_rows == 0 || n_cols == 0 {
        return 0;
    }

    let dict = unsafe { std::slice::from_raw_parts(dict_ptr, n_rows * n_cols) };
    let residual = unsafe { std::slice::from_raw_parts(residual_ptr, n_rows) };

    let mut best_idx = 0usize;
    let mut max_abs_corr = -1.0f64;

    for j in 0..n_cols {
        let col = &dict[j * n_rows..(j + 1) * n_rows];
        let mut dot = 0.0f64;
        for i in 0..n_rows {
            dot += col[i] * residual[i];
        }

        if !out_correlations.is_null() {
            unsafe {
                *out_correlations.add(j) = dot;
            }
        }

        let abs_dot = dot.abs();
        if abs_dot > max_abs_corr {
            max_abs_corr = abs_dot;
            best_idx = j;
        }
    }

    best_idx
}

/// RRT* Nearest Neighbor & Radius Rewiring Batch Kernel.
/// Encontra o vizinho mais próximo e filtra nós dentro do raio R.
#[no_mangle]
pub extern "C" fn rrt_star_nearest_and_radius_f64(
    tree_nodes_ptr: *const f64,
    n_nodes: usize,
    dim: usize,
    query_ptr: *const f64,
    radius: f64,
    out_nearest_idx: *mut usize,
    out_min_dist: *mut f64,
    out_near_indices: *mut usize,
    max_near: usize,
    out_near_count: *mut usize,
) -> i32 {
    if tree_nodes_ptr.is_null() || query_ptr.is_null() || n_nodes == 0 || dim == 0 {
        return -1;
    }

    let nodes = unsafe { std::slice::from_raw_parts(tree_nodes_ptr, n_nodes * dim) };
    let query = unsafe { std::slice::from_raw_parts(query_ptr, dim) };

    let mut min_dist_sq = f64::MAX;
    let mut nearest_idx = 0usize;
    let r_sq = radius * radius;
    let mut near_count = 0usize;

    for i in 0..n_nodes {
        let node_pt = &nodes[i * dim..(i + 1) * dim];
        let mut d_sq = 0.0f64;
        for d in 0..dim {
            let diff = node_pt[d] - query[d];
            d_sq += diff * diff;
        }

        if d_sq < min_dist_sq {
            min_dist_sq = d_sq;
            nearest_idx = i;
        }

        if d_sq <= r_sq && !out_near_indices.is_null() && near_count < max_near {
            unsafe {
                *out_near_indices.add(near_count) = i;
            }
            near_count += 1;
        }
    }

    unsafe {
        if !out_nearest_idx.is_null() {
            *out_nearest_idx = nearest_idx;
        }
        if !out_min_dist.is_null() {
            *out_min_dist = min_dist_sq.sqrt();
        }
        if !out_near_count.is_null() {
            *out_near_count = near_count;
        }
    }

    0
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_omp_sparse_project() {
        let dict = vec![1.0, 0.0, 0.0, 0.0, 1.0, 0.0];
        let residual = vec![0.1, 0.9, 0.0];
        let mut corrs = vec![0.0; 2];

        let best = omp_sparse_project_f64(dict.as_ptr(), 3, 2, residual.as_ptr(), corrs.as_mut_ptr());
        assert_eq!(best, 1);
        assert!((corrs[1] - 0.9).abs() < 1e-9);
    }

    #[test]
    fn test_rrt_star_nearest_and_radius() {
        let nodes = vec![
            0.0, 0.0,
            1.0, 1.0,
            5.0, 5.0,
        ];
        let query = vec![0.9, 0.9];
        let mut nearest_idx = 0usize;
        let mut min_dist = 0.0f64;
        let mut near_indices = vec![0usize; 3];
        let mut near_count = 0usize;

        let status = rrt_star_nearest_and_radius_f64(
            nodes.as_ptr(),
            3,
            2,
            query.as_ptr(),
            0.5,
            &mut nearest_idx,
            &mut min_dist,
            near_indices.as_mut_ptr(),
            3,
            &mut near_count,
        );

        assert_eq!(status, 0);
        assert_eq!(nearest_idx, 1);
        assert!(min_dist < 0.2);
        assert_eq!(near_count, 1);
        assert_eq!(near_indices[0], 1);
    }
}
