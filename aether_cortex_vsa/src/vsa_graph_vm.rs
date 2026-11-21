//! Fused VSA Expression Graph Bytecode VM & AVX2 Register-Tiled Kernel.
//!
//! Compiles and evaluates complex DAG chains of 10,240-bit Vector Symbolic
//! Architecture operations (`LOAD`, `SEED`, `BIND`, `PERMUTE`, `BUNDLE`, `HAMMING`)
//! inside L1-resident registers `[Hypervector; MAX_REGS]` in a single FFI crossing
//! with zero intermediate heap allocations.

use crate::Hypervector;
pub const WORDS: usize = crate::WORDS;
pub const MAX_REGS: usize = 32;

pub const OP_LOAD_INPUT: u8 = 1;
pub const OP_LOAD_SEED: u8 = 2;
pub const OP_BIND_XOR: u8 = 3;
pub const OP_PERMUTE: u8 = 4;
pub const OP_UNPERMUTE: u8 = 5;
pub const OP_BUNDLE_TWO: u8 = 6;
pub const OP_BUNDLE_RANGE: u8 = 7;
pub const OP_HAMMING_DIST: u8 = 8;
pub const OP_STORE_OUTPUT: u8 = 9;

#[repr(C)]
#[derive(Clone, Copy, Debug)]
pub struct VsaOp {
    pub opcode: u8,
    pub dst: u8,
    pub src_a: u8,
    pub src_b: u8,
    pub imm: u64,
}

#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2")]
unsafe fn bind_avx2(a: &[u64; WORDS], b: &[u64; WORDS], out: &mut [u64; WORDS]) {
    use std::arch::x86_64::*;
    let pa = a.as_ptr() as *const __m256i;
    let pb = b.as_ptr() as *const __m256i;
    let po = out.as_mut_ptr() as *mut __m256i;
    // WORDS = 160 -> 40 chunks of 4 u64 (256-bit YMM registers)
    let mut i = 0usize;
    while i < 40 {
        let va = _mm256_loadu_si256(pa.add(i));
        let vb = _mm256_loadu_si256(pb.add(i));
        _mm256_storeu_si256(po.add(i), _mm256_xor_si256(va, vb));
        i += 1;
    }
}

#[inline(always)]
fn bind_fast(a: &Hypervector, b: &Hypervector, out: &mut Hypervector, _use_avx2: bool) {
    #[cfg(target_arch = "x86_64")]
    if _use_avx2 {
        unsafe {
            bind_avx2(&a.0, &b.0, &mut out.0);
        }
        return;
    }
    for i in 0..WORDS {
        out.0[i] = a.0[i] ^ b.0[i];
    }
}

#[inline(always)]
fn permute_into(src: &Hypervector, steps: usize, out: &mut Hypervector) {
    let total_bits = WORDS * 64;
    let s = steps % total_bits;
    if s == 0 {
        out.0 = src.0;
        return;
    }
    let word_shift = s / 64;
    let bit_shift = (s % 64) as u32;
    if bit_shift == 0 {
        for i in 0..WORDS {
            out.0[(i + word_shift) % WORDS] = src.0[i];
        }
    } else {
        let inv_shift = 64 - bit_shift;
        for i in 0..WORDS {
            let next_i = (i + 1) % WORDS;
            // Word rotation preserving bit continuity across word boundary
            let dst_idx = (i + word_shift) % WORDS;
            out.0[dst_idx] = (src.0[i] << bit_shift) | (src.0[(i + WORDS - 1) % WORDS] >> inv_shift);
            let _ = next_i;
        }
    }
}

#[inline(always)]
fn unpermute_into(src: &Hypervector, steps: usize, out: &mut Hypervector) {
    let total_bits = WORDS * 64;
    let s = steps % total_bits;
    if s == 0 {
        out.0 = src.0;
        return;
    }
    // Inverse circular shift by total_bits - s
    permute_into(src, total_bits - s, out);
}

#[inline(always)]
fn hamming_unrolled(a: &Hypervector, b: &Hypervector) -> u32 {
    let mut c0 = 0u32;
    let mut c1 = 0u32;
    let mut c2 = 0u32;
    let mut c3 = 0u32;
    let mut i = 0usize;
    while i < WORDS {
        c0 += (a.0[i] ^ b.0[i]).count_ones();
        c1 += (a.0[i + 1] ^ b.0[i + 1]).count_ones();
        c2 += (a.0[i + 2] ^ b.0[i + 2]).count_ones();
        c3 += (a.0[i + 3] ^ b.0[i + 3]).count_ones();
        i += 4;
    }
    c0 + c1 + c2 + c3
}

fn bundle_range_into(
    regs: &[Hypervector; MAX_REGS],
    start_reg: usize,
    count: usize,
    tie_seed: u64,
    out: &mut Hypervector,
) {
    if count == 0 {
        *out = Hypervector::zero();
        return;
    }
    if count == 1 {
        *out = regs[start_reg];
        return;
    }
    let tie = Hypervector::from_seed(tie_seed ^ (count as u64));
    let threshold = count / 2;
    let is_even = count % 2 == 0;

    for w in 0..WORDS {
        let mut res_word = 0u64;
        for bit in 0..64u32 {
            let mask = 1u64 << bit;
            let mut ones = 0usize;
            for k in 0..count {
                if (regs[start_reg + k].0[w] & mask) != 0 {
                    ones += 1;
                }
            }
            let win = if is_even && ones == threshold {
                (tie.0[w] & mask) != 0
            } else {
                ones > threshold
            };
            if win {
                res_word |= mask;
            }
        }
        out.0[w] = res_word;
    }
}

/// Evaluates a compiled VSA expression graph bytecode program in a single FFI crossing.
/// Returns 0 on success, negative error code on invalid pointers/indices.
#[no_mangle]
pub extern "C" fn vsa_eval_graph_bytecode(
    ops_ptr: *const VsaOp,
    n_ops: usize,
    in_vecs_ptr: *const u64,
    n_inputs: usize,
    out_vecs_ptr: *mut u64,
    n_outputs: usize,
    out_scalars_ptr: *mut u32,
    n_scalars: usize,
) -> i32 {
    if ops_ptr.is_null() || n_ops == 0 {
        return -1;
    }

    let ops = unsafe { std::slice::from_raw_parts(ops_ptr, n_ops) };
    let inputs = if !in_vecs_ptr.is_null() && n_inputs > 0 {
        unsafe { std::slice::from_raw_parts(in_vecs_ptr, n_inputs * WORDS) }
    } else {
        &[]
    };
    let outputs = if !out_vecs_ptr.is_null() && n_outputs > 0 {
        unsafe { std::slice::from_raw_parts_mut(out_vecs_ptr, n_outputs * WORDS) }
    } else {
        &mut []
    };
    let scalars = if !out_scalars_ptr.is_null() && n_scalars > 0 {
        unsafe { std::slice::from_raw_parts_mut(out_scalars_ptr, n_scalars) }
    } else {
        &mut []
    };

    #[cfg(target_arch = "x86_64")]
    let use_avx2 = std::is_x86_feature_detected!("avx2");
    #[cfg(not(target_arch = "x86_64"))]
    let use_avx2 = false;

    let mut regs = [Hypervector::zero(); MAX_REGS];
    let mut tmp = Hypervector::zero();

    for op in ops {
        let dst = op.dst as usize;
        let a = op.src_a as usize;
        let b = op.src_b as usize;

        match op.opcode {
            OP_LOAD_INPUT => {
                if dst >= MAX_REGS || a >= n_inputs {
                    return -2;
                }
                regs[dst].0.copy_from_slice(&inputs[a * WORDS..(a + 1) * WORDS]);
            }
            OP_LOAD_SEED => {
                if dst >= MAX_REGS {
                    return -2;
                }
                regs[dst] = Hypervector::from_seed(op.imm);
            }
            OP_BIND_XOR => {
                if dst >= MAX_REGS || a >= MAX_REGS || b >= MAX_REGS {
                    return -2;
                }
                let (ra, rb) = (regs[a], regs[b]);
                bind_fast(&ra, &rb, &mut regs[dst], use_avx2);
            }
            OP_PERMUTE => {
                if dst >= MAX_REGS || a >= MAX_REGS {
                    return -2;
                }
                permute_into(&regs[a], op.imm as usize, &mut tmp);
                regs[dst] = tmp;
            }
            OP_UNPERMUTE => {
                if dst >= MAX_REGS || a >= MAX_REGS {
                    return -2;
                }
                unpermute_into(&regs[a], op.imm as usize, &mut tmp);
                regs[dst] = tmp;
            }
            OP_BUNDLE_TWO => {
                if dst >= MAX_REGS || a >= MAX_REGS || b >= MAX_REGS {
                    return -2;
                }
                let tie = Hypervector::from_seed(op.imm);
                for w in 0..WORDS {
                    let va = regs[a].0[w];
                    let vb = regs[b].0[w];
                    let vt = tie.0[w];
                    tmp.0[w] = (va & vb) | (vb & vt) | (va & vt);
                }
                regs[dst] = tmp;
            }
            OP_BUNDLE_RANGE => {
                if dst >= MAX_REGS || a + b > MAX_REGS {
                    return -2;
                }
                bundle_range_into(&regs, a, b, op.imm, &mut tmp);
                regs[dst] = tmp;
            }
            OP_HAMMING_DIST => {
                if dst >= n_scalars || a >= MAX_REGS || b >= MAX_REGS {
                    return -3;
                }
                scalars[dst] = hamming_unrolled(&regs[a], &regs[b]);
            }
            OP_STORE_OUTPUT => {
                if dst >= n_outputs || a >= MAX_REGS {
                    return -4;
                }
                outputs[dst * WORDS..(dst + 1) * WORDS].copy_from_slice(&regs[a].0);
            }
            _ => return -5,
        }
    }

    0
}

#[cfg(test)]
mod vm_tests {
    use super::*;

    #[test]
    fn test_fused_vsa_vm_bind_permute_hamming_exact() {
        let a = Hypervector::from_seed(111);
        let b = Hypervector::from_seed(222);
        let mut inputs = vec![0u64; 2 * WORDS];
        inputs[..WORDS].copy_from_slice(&a.0);
        inputs[WORDS..2 * WORDS].copy_from_slice(&b.0);

        let ops = [
            VsaOp { opcode: OP_LOAD_INPUT, dst: 0, src_a: 0, src_b: 0, imm: 0 },
            VsaOp { opcode: OP_LOAD_INPUT, dst: 1, src_a: 1, src_b: 0, imm: 0 },
            VsaOp { opcode: OP_PERMUTE, dst: 2, src_a: 0, src_b: 0, imm: 17 },
            VsaOp { opcode: OP_UNPERMUTE, dst: 3, src_a: 2, src_b: 0, imm: 17 },
            VsaOp { opcode: OP_HAMMING_DIST, dst: 0, src_a: 0, src_b: 3, imm: 0 },
            VsaOp { opcode: OP_BIND_XOR, dst: 4, src_a: 0, src_b: 1, imm: 0 },
            VsaOp { opcode: OP_BIND_XOR, dst: 5, src_a: 4, src_b: 1, imm: 0 },
            VsaOp { opcode: OP_HAMMING_DIST, dst: 1, src_a: 0, src_b: 5, imm: 0 },
            VsaOp { opcode: OP_STORE_OUTPUT, dst: 0, src_a: 4, src_b: 0, imm: 0 },
        ];

        let mut out_vec = vec![0u64; WORDS];
        let mut scalars = [999u32; 2];

        let st = vsa_eval_graph_bytecode(
            ops.as_ptr(), ops.len(),
            inputs.as_ptr(), 2,
            out_vec.as_mut_ptr(), 1,
            scalars.as_mut_ptr(), 2,
        );

        assert_eq!(st, 0);
        assert_eq!(scalars[0], 0, "PERMUTE followed by UNPERMUTE must yield 0 Hamming distance");
        assert_eq!(scalars[1], 0, "BIND twice must self-invert to 0 Hamming distance");
        assert_eq!(out_vec, a.bind(&b).0.to_vec());
    }
}
