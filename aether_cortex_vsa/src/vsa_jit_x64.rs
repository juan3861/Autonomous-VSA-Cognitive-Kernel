//! Zero-Dependency Native x86_64 AVX2 Machine-Code JIT Emitter (W^X Verified).
//!
//! Emits genuine x86_64 AVX2 (`vmovdqu` / `vpxor` / `vzeroupper`) machine instructions
//! into writable pages (`PAGE_READWRITE`), flips permissions strictly via W^X
//! (`PAGE_EXECUTE_READ`), and executes multi-input 10,240-bit VSA XOR chains with
//! zero bytecode dispatch loop overhead. Falls back cleanly on non-x86_64 / wasm32.

#[cfg(target_arch = "x86_64")]
use core::ffi::c_void;
use crate::WORDS;

#[repr(C)]
pub struct JitXorHandle {
    pub code_ptr: *mut u8,
    pub code_size: usize,
    pub n_inputs: usize,
    pub is_native_jit: bool,
}

#[cfg(all(target_arch = "x86_64", windows))]
mod win32_mem {
    use core::ffi::c_void;
    pub const MEM_COMMIT: u32 = 0x1000;
    pub const MEM_RESERVE: u32 = 0x2000;
    pub const MEM_RELEASE: u32 = 0x8000;
    pub const PAGE_READWRITE: u32 = 0x04;
    pub const PAGE_EXECUTE_READ: u32 = 0x20;

    extern "system" {
        pub fn VirtualAlloc(lpAddress: *mut c_void, dwSize: usize, flAllocationType: u32, flProtect: u32) -> *mut c_void;
        pub fn VirtualProtect(lpAddress: *mut c_void, dwSize: usize, flNewProtect: u32, lpflOldProtect: *mut u32) -> i32;
        pub fn VirtualFree(lpAddress: *mut c_void, dwSize: usize, dwFreeType: u32) -> i32;
        pub fn GetCurrentProcess() -> *mut c_void;
        pub fn FlushInstructionCache(hProcess: *mut c_void, lpBaseAddress: *const c_void, dwSize: usize) -> i32;
    }
}

#[cfg(all(target_arch = "x86_64", unix))]
mod posix_mem {
    use core::ffi::c_void;
    pub const PROT_READ: i32 = 1;
    pub const PROT_WRITE: i32 = 2;
    pub const PROT_EXEC: i32 = 4;
    pub const MAP_PRIVATE: i32 = 2;
    #[cfg(target_os = "linux")]
    pub const MAP_ANONYMOUS: i32 = 0x20;
    #[cfg(target_os = "macos")]
    pub const MAP_ANONYMOUS: i32 = 0x1000;

    extern "C" {
        pub fn mmap(addr: *mut c_void, len: usize, prot: i32, flags: i32, fd: i32, offset: isize) -> *mut c_void;
        pub fn mprotect(addr: *mut c_void, len: usize, prot: i32) -> i32;
        pub fn munmap(addr: *mut c_void, len: usize) -> i32;
    }
}

#[cfg(target_arch = "x86_64")]
fn build_avx2_xor_machine_code(n_inputs: usize) -> Vec<u8> {
    let mut code = Vec::with_capacity(64 + n_inputs * 20);

    // Function signature: extern "C" fn(in_ptrs: *const *const u64, out_buf: *mut u64)
    // Normalize arguments into r10 (in_ptrs) and r11 (out_buf), preserving all callee-saved regs.
    #[cfg(windows)]
    {
        // mov r10, rcx ; mov r11, rdx
        code.extend_from_slice(&[0x49, 0x89, 0xCA, 0x49, 0x89, 0xD3]);
    }
    #[cfg(not(windows))]
    {
        // mov r10, rdi ; mov r11, rsi
        code.extend_from_slice(&[0x49, 0x89, 0xFA, 0x49, 0x89, 0xF3]);
    }

    // xor r8d, r8d  (byte offset = 0 .. 1280)
    code.extend_from_slice(&[0x45, 0x31, 0xC0]);

    let loop_start = code.len();

    // mov rax, [r10]
    code.extend_from_slice(&[0x49, 0x8B, 0x02]);
    // vmovdqu ymm0, [rax + r8]
    code.extend_from_slice(&[0xC4, 0xA1, 0x7E, 0x6F, 0x04, 0x00]);

    for k in 1..n_inputs {
        let disp = (k * 8) as u32;
        // mov rax, [r10 + disp32]
        code.extend_from_slice(&[0x49, 0x8B, 0x82]);
        code.extend_from_slice(&disp.to_le_bytes());
        // vmovdqu ymm1, [rax + r8]
        code.extend_from_slice(&[0xC4, 0xA1, 0x7E, 0x6F, 0x0C, 0x00]);
        // vpxor ymm0, ymm0, ymm1
        code.extend_from_slice(&[0xC5, 0xFD, 0xEF, 0xC1]);
    }

    // vmovdqu [r11 + r8], ymm0
    code.extend_from_slice(&[0xC4, 0x81, 0x7E, 0x7F, 0x04, 0x03]);
    // add r8, 32
    code.extend_from_slice(&[0x49, 0x83, 0xC0, 0x20]);
    // cmp r8, 1280  (WORDS * 8 = 1280)
    code.extend_from_slice(&[0x49, 0x81, 0xF8]);
    code.extend_from_slice(&((WORDS * 8) as u32).to_le_bytes());

    // jl loop_start (0F 8C rel32)
    let next_ip = code.len() + 6;
    let rel = (loop_start as isize - next_ip as isize) as i32;
    code.extend_from_slice(&[0x0F, 0x8C]);
    code.extend_from_slice(&rel.to_le_bytes());

    // vzeroupper ; ret
    code.extend_from_slice(&[0xC5, 0xF8, 0x77, 0xC3]);
    code
}

/// Compile a native x86_64 AVX2 machine-code kernel for XOR-binding `n_inputs` 10,240-bit hypervectors.
#[no_mangle]
pub extern "C" fn vsa_jit_compile_xor_chain(n_inputs: usize) -> *mut JitXorHandle {
    if n_inputs == 0 {
        return core::ptr::null_mut();
    }

    #[cfg(target_arch = "x86_64")]
    if std::is_x86_feature_detected!("avx2") {
        let code = build_avx2_xor_machine_code(n_inputs);
        let size = code.len().max(4096);

        #[cfg(windows)]
        unsafe {
            let mem = win32_mem::VirtualAlloc(
                core::ptr::null_mut(),
                size,
                win32_mem::MEM_COMMIT | win32_mem::MEM_RESERVE,
                win32_mem::PAGE_READWRITE,
            ) as *mut u8;
            if !mem.is_null() {
                core::ptr::copy_nonoverlapping(code.as_ptr(), mem, code.len());
                let mut old_prot: u32 = 0;
                if win32_mem::VirtualProtect(mem as *mut c_void, size, win32_mem::PAGE_EXECUTE_READ, &mut old_prot) != 0 {
                    win32_mem::FlushInstructionCache(win32_mem::GetCurrentProcess(), mem as *const c_void, code.len());
                    return Box::into_raw(Box::new(JitXorHandle {
                        code_ptr: mem,
                        code_size: size,
                        n_inputs,
                        is_native_jit: true,
                    }));
                }
                win32_mem::VirtualFree(mem as *mut c_void, 0, win32_mem::MEM_RELEASE);
            }
        }

        #[cfg(unix)]
        unsafe {
            let mem = posix_mem::mmap(
                core::ptr::null_mut(),
                size,
                posix_mem::PROT_READ | posix_mem::PROT_WRITE,
                posix_mem::MAP_PRIVATE | posix_mem::MAP_ANONYMOUS,
                -1,
                0,
            ) as *mut u8;
            if !mem.is_null() && (mem as isize) != -1 {
                core::ptr::copy_nonoverlapping(code.as_ptr(), mem, code.len());
                if posix_mem::mprotect(mem as *mut c_void, size, posix_mem::PROT_READ | posix_mem::PROT_EXEC) == 0 {
                    return Box::into_raw(Box::new(JitXorHandle {
                        code_ptr: mem,
                        code_size: size,
                        n_inputs,
                        is_native_jit: true,
                    }));
                }
                posix_mem::munmap(mem as *mut c_void, size);
            }
        }
    }

    // Portable scalar fallback handle (non-x86_64, non-AVX2, or wasm32)
    Box::into_raw(Box::new(JitXorHandle {
        code_ptr: core::ptr::null_mut(),
        code_size: 0,
        n_inputs,
        is_native_jit: false,
    }))
}

/// Execute a compiled JIT XOR chain handle against an array of `n_inputs` hypervector pointers.
#[no_mangle]
pub extern "C" fn vsa_jit_exec_xor_chain(
    handle: *const JitXorHandle,
    in_ptrs: *const *const u64,
    out_buf: *mut u64,
) -> i32 {
    if handle.is_null() || in_ptrs.is_null() || out_buf.is_null() {
        return -1;
    }
    let h = unsafe { &*handle };
    if h.is_native_jit && !h.code_ptr.is_null() {
        let jit_fn: extern "C" fn(*const *const u64, *mut u64) =
            unsafe { core::mem::transmute(h.code_ptr) };
        jit_fn(in_ptrs, out_buf);
        return 1; // Executed native x86_64 AVX2 machine code
    }

    // Scalar fallback
    unsafe {
        let ptr_slice = core::slice::from_raw_parts(in_ptrs, h.n_inputs);
        let p0 = core::slice::from_raw_parts(ptr_slice[0], WORDS);
        let out = core::slice::from_raw_parts_mut(out_buf, WORDS);
        out.copy_from_slice(p0);
        for &p in &ptr_slice[1..] {
            let pk = core::slice::from_raw_parts(p, WORDS);
            for w in 0..WORDS {
                out[w] ^= pk[w];
            }
        }
    }
    0
}

#[no_mangle]
pub extern "C" fn vsa_jit_free_xor_chain(handle: *mut JitXorHandle) {
    if handle.is_null() {
        return;
    }
    let h = unsafe { Box::from_raw(handle) };
    if h.is_native_jit && !h.code_ptr.is_null() {
        #[cfg(all(target_arch = "x86_64", windows))]
        unsafe {
            win32_mem::VirtualFree(h.code_ptr as *mut c_void, 0, win32_mem::MEM_RELEASE);
        }
        #[cfg(all(target_arch = "x86_64", unix))]
        unsafe {
            posix_mem::munmap(h.code_ptr as *mut c_void, h.code_size);
        }
    }
}

#[cfg(test)]
mod jit_tests {
    use super::*;
    use crate::Hypervector;

    #[test]
    fn test_native_x64_avx2_jit_xor_chain_bit_exact() {
        let h0 = Hypervector::from_seed(101);
        let h1 = Hypervector::from_seed(202);
        let h2 = Hypervector::from_seed(303);
        let h3 = Hypervector::from_seed(404);
        let h4 = Hypervector::from_seed(505);

        let expected = h0.bind(&h1).bind(&h2).bind(&h3).bind(&h4);

        let handle = vsa_jit_compile_xor_chain(5);
        assert!(!handle.is_null());

        let ptrs = [h0.0.as_ptr(), h1.0.as_ptr(), h2.0.as_ptr(), h3.0.as_ptr(), h4.0.as_ptr()];
        let mut out = [0u64; WORDS];
        let exec_mode = vsa_jit_exec_xor_chain(handle, ptrs.as_ptr(), out.as_mut_ptr());
        vsa_jit_free_xor_chain(handle);

        assert!(exec_mode == 1 || exec_mode == 0);
        #[cfg(target_arch = "x86_64")]
        if std::is_x86_feature_detected!("avx2") {
            assert_eq!(exec_mode, 1, "Must execute native emitted x86_64 AVX2 machine code");
        }
        assert_eq!(out, expected.0, "JIT emitted AVX2 output must be bit-exact");
    }
}
