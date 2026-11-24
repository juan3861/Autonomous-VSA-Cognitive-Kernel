"""Vulkan 1.3 Batch VSA Hamming & Cosine GPU Compute Engine (AMD Radeon RX 580 Wave64).

Dispatches thousands of 10,240-bit hypervector Hamming distance comparisons and dense
float32 cosine similarity computations across the 2,304 Wave64 cores of the AMD RX 580
via `vulkan-1.dll` HOST_VISIBLE | HOST_COHERENT zero-copy VRAM buffers and SPIR-V shaders.
Falls back deterministically to NumPy/CPU if Vulkan hardware is unavailable (e.g., CI).
"""
from __future__ import annotations

import ctypes
import time
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np

from .vulkan_polaris_compute_pipeline import (
    VkApplicationInfo,
    VkInstanceCreateInfo,
    VkPhysicalDeviceProperties,
    VkDeviceQueueCreateInfo,
    VkDeviceCreateInfo,
    VkShaderModuleCreateInfo,
    VkDescriptorSetLayoutBinding,
    VkDescriptorSetLayoutCreateInfo,
    VkPushConstantRange,
    VkPipelineLayoutCreateInfo,
    VkPipelineShaderStageCreateInfo,
    VkComputePipelineCreateInfo,
    VkCommandPoolCreateInfo,
    VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo,
    VkSubmitInfo,
)
from .vulkan_zero_copy_vram_buffer import (
    VkPhysicalDeviceMemoryProperties,
    VkBufferCreateInfo,
    VkMemoryRequirements,
    VkMemoryAllocateInfo,
    VkDescriptorPoolSize,
    VkDescriptorPoolCreateInfo,
    VkDescriptorSetAllocateInfo,
    VkDescriptorBufferInfo,
    VkWriteDescriptorSet,
)


class BatchPushConstants(ctypes.Structure):
    _fields_ = [
        ("num_candidates", ctypes.c_uint32),
        ("stride_words", ctypes.c_uint32),
    ]


class VulkanBatchVSAEngine:
    """RX 580 SPIR-V Wave64 Batch Compute Dispatcher for VSA Hamming & Dense Cosine."""

    def __init__(self):
        self.shaders_dir = Path(__file__).resolve().parent.parent / "logic_symbolic" / "shaders"
        self.vsa_spv_path = self.shaders_dir / "vsa_batch_hamming.spv"
        self.cosine_spv_path = self.shaders_dir / "batch_cosine_sim.spv"
        self.permuted_xor_spv_path = self.shaders_dir / "vsa_batch_permuted_xor.spv"
        self.vk_dll: Optional[ctypes.CDLL] = None
        self.is_available: bool = False
        self._probe_vulkan()

    def _probe_vulkan(self) -> None:
        try:
            self.vk_dll = ctypes.WinDLL("vulkan-1.dll")
            self._setup_prototypes()
            self.is_available = True
        except Exception:
            self.vk_dll = None
            self.is_available = False

    def _setup_prototypes(self) -> None:
        if self.vk_dll is None:
            return
        vk = self.vk_dll
        vk.vkCreateComputePipelines.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
            ctypes.POINTER(VkComputePipelineCreateInfo), ctypes.c_void_p,
            ctypes.POINTER(ctypes.c_void_p)
        ]
        vk.vkCreateComputePipelines.restype = ctypes.c_int32
        vk.vkBindBufferMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64]
        vk.vkBindBufferMemory.restype = ctypes.c_int32
        vk.vkMapMemory.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint64,
            ctypes.c_uint64, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p)
        ]
        vk.vkMapMemory.restype = ctypes.c_int32
        vk.vkUnmapMemory.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        vk.vkUnmapMemory.restype = None
        vk.vkUpdateDescriptorSets.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(VkWriteDescriptorSet),
            ctypes.c_uint32, ctypes.c_void_p
        ]
        vk.vkUpdateDescriptorSets.restype = None
        vk.vkCmdBindPipeline.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p]
        vk.vkCmdBindDescriptorSets.argtypes = [
            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.POINTER(ctypes.c_void_p),
            ctypes.c_uint32, ctypes.c_void_p
        ]
        vk.vkCmdPushConstants.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p
        ]
        vk.vkCmdDispatch.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]

    def _dispatch_3buffer_shader(
        self,
        spv_path: Path,
        buf0_bytes: bytes,
        buf1_bytes: bytes,
        out_byte_size: int,
        num_candidates: int,
        stride_words: int,
    ) -> Dict[str, Any]:
        """Execute a generic 3-storage-buffer Wave64 SPIR-V compute shader on RX 580."""
        t0 = time.perf_counter()
        vk = self.vk_dll
        if not self.is_available or vk is None or not spv_path.exists():
            return {"gpu_executed": False, "status": "VULKAN_UNAVAILABLE"}

        spv_bytes = spv_path.read_bytes()
        app_info = VkApplicationInfo(0, None, b"Aether_Batch_GPU", 1, b"AetherCOS_v7_3", 1, (1 << 22) | (3 << 12))
        inst_info = VkInstanceCreateInfo(1, None, 0, ctypes.pointer(app_info), 0, None, 0, None)
        instance = ctypes.c_void_p()
        if vk.vkCreateInstance(ctypes.byref(inst_info), None, ctypes.byref(instance)) != 0:
            return {"gpu_executed": False, "status": "VK_INSTANCE_FAILED"}

        try:
            dev_cnt = ctypes.c_uint32(0)
            vk.vkEnumeratePhysicalDevices(instance, ctypes.byref(dev_cnt), None)
            if dev_cnt.value == 0:
                return {"gpu_executed": False, "status": "NO_VULKAN_DEVICE"}
            devs = (ctypes.c_void_p * dev_cnt.value)()
            vk.vkEnumeratePhysicalDevices(instance, ctypes.byref(dev_cnt), devs)
            phys_dev = ctypes.c_void_p(devs[0])

            props = VkPhysicalDeviceProperties()
            vk.vkGetPhysicalDeviceProperties(phys_dev, ctypes.byref(props))
            gpu_name = props.deviceName.decode("utf-8", errors="replace").strip("\x00")

            mem_props = VkPhysicalDeviceMemoryProperties()
            vk.vkGetPhysicalDeviceMemoryProperties(phys_dev, ctypes.byref(mem_props))
            mem_type_idx = 0
            for i in range(mem_props.memoryTypeCount):
                if (mem_props.memoryTypes[i].propertyFlags & 0x06) == 0x06:
                    mem_type_idx = i
                    break

            prio = ctypes.c_float(1.0)
            q_info = VkDeviceQueueCreateInfo(2, None, 0, 0, 1, ctypes.pointer(prio))
            d_info = VkDeviceCreateInfo(3, None, 0, 1, ctypes.pointer(q_info), 0, None, 0, None, None)
            logical_dev = ctypes.c_void_p()
            vk.vkCreateDevice(phys_dev, ctypes.byref(d_info), None, ctypes.byref(logical_dev))

            try:
                def _alloc_mapped(b_size: int, initial: Optional[bytes]):
                    b_info = VkBufferCreateInfo(12, None, 0, b_size, 0x20, 0, 0, None)
                    bh = ctypes.c_void_p()
                    vk.vkCreateBuffer(logical_dev, ctypes.byref(b_info), None, ctypes.byref(bh))
                    req = VkMemoryRequirements()
                    vk.vkGetBufferMemoryRequirements(logical_dev, bh, ctypes.byref(req))
                    m_info = VkMemoryAllocateInfo(5, None, max(b_size, req.size), mem_type_idx)
                    mh = ctypes.c_void_p()
                    vk.vkAllocateMemory(logical_dev, ctypes.byref(m_info), None, ctypes.byref(mh))
                    vk.vkBindBufferMemory(logical_dev, bh, mh, 0)
                    ptr = ctypes.c_void_p()
                    vk.vkMapMemory(logical_dev, mh, 0, b_size, 0, ctypes.byref(ptr))
                    if initial is not None:
                        ctypes.memmove(ptr.value, initial, b_size)
                    return bh, mh, ptr, b_size

                b0, m0, p0, s0 = _alloc_mapped(len(buf0_bytes), buf0_bytes)
                b1, m1, p1, s1 = _alloc_mapped(len(buf1_bytes), buf1_bytes)
                b2, m2, p2, s2 = _alloc_mapped(out_byte_size, None)

                try:
                    code_arr = (ctypes.c_uint32 * (len(spv_bytes) // 4)).from_buffer_copy(spv_bytes)
                    sm_info = VkShaderModuleCreateInfo(16, None, 0, len(spv_bytes), ctypes.cast(code_arr, ctypes.POINTER(ctypes.c_uint32)))
                    shader_mod = ctypes.c_void_p()
                    vk.vkCreateShaderModule(logical_dev, ctypes.byref(sm_info), None, ctypes.byref(shader_mod))

                    bindings = (VkDescriptorSetLayoutBinding * 3)(
                        VkDescriptorSetLayoutBinding(0, 7, 1, 0x20, None),
                        VkDescriptorSetLayoutBinding(1, 7, 1, 0x20, None),
                        VkDescriptorSetLayoutBinding(2, 7, 1, 0x20, None),
                    )
                    dsl_info = VkDescriptorSetLayoutCreateInfo(32, None, 0, 3, bindings)
                    desc_layout = ctypes.c_void_p()
                    vk.vkCreateDescriptorSetLayout(logical_dev, ctypes.byref(dsl_info), None, ctypes.byref(desc_layout))

                    pool_size = VkDescriptorPoolSize(7, 3)
                    pool_info = VkDescriptorPoolCreateInfo(33, None, 0, 1, 1, ctypes.pointer(pool_size))
                    desc_pool = ctypes.c_void_p()
                    vk.vkCreateDescriptorPool(logical_dev, ctypes.byref(pool_info), None, ctypes.byref(desc_pool))

                    layouts_arr = (ctypes.c_void_p * 1)(desc_layout.value)
                    ds_alloc = VkDescriptorSetAllocateInfo(34, None, desc_pool.value, 1, layouts_arr)
                    desc_set = ctypes.c_void_p()
                    vk.vkAllocateDescriptorSets(logical_dev, ctypes.byref(ds_alloc), ctypes.byref(desc_set))

                    bi0 = VkDescriptorBufferInfo(b0.value, 0, s0)
                    bi1 = VkDescriptorBufferInfo(b1.value, 0, s1)
                    bi2 = VkDescriptorBufferInfo(b2.value, 0, s2)
                    writes = (VkWriteDescriptorSet * 3)(
                        VkWriteDescriptorSet(35, None, desc_set.value, 0, 0, 1, 7, None, ctypes.pointer(bi0), None),
                        VkWriteDescriptorSet(35, None, desc_set.value, 1, 0, 1, 7, None, ctypes.pointer(bi1), None),
                        VkWriteDescriptorSet(35, None, desc_set.value, 2, 0, 1, 7, None, ctypes.pointer(bi2), None),
                    )
                    vk.vkUpdateDescriptorSets(logical_dev, 3, writes, 0, None)

                    push_range = VkPushConstantRange(0x20, 0, 8)
                    pl_info = VkPipelineLayoutCreateInfo(30, None, 0, 1, layouts_arr, 1, ctypes.pointer(push_range))
                    pipeline_layout = ctypes.c_void_p()
                    vk.vkCreatePipelineLayout(logical_dev, ctypes.byref(pl_info), None, ctypes.byref(pipeline_layout))

                    stage_info = VkPipelineShaderStageCreateInfo(18, None, 0, 0x20, shader_mod.value, b"main", None)
                    cp_info = VkComputePipelineCreateInfo(29, None, 0, stage_info, pipeline_layout.value, None, -1)
                    pipeline = ctypes.c_void_p()
                    vk.vkCreateComputePipelines(logical_dev, None, 1, ctypes.byref(cp_info), None, ctypes.byref(pipeline))

                    cp_pool_info = VkCommandPoolCreateInfo(39, None, 2, 0)
                    cmd_pool = ctypes.c_void_p()
                    vk.vkCreateCommandPool(logical_dev, ctypes.byref(cp_pool_info), None, ctypes.byref(cmd_pool))

                    cmd_alloc = VkCommandBufferAllocateInfo(40, None, cmd_pool.value, 0, 1)
                    cmd_buf = ctypes.c_void_p()
                    vk.vkAllocateCommandBuffers(logical_dev, ctypes.byref(cmd_alloc), ctypes.byref(cmd_buf))

                    begin_info = VkCommandBufferBeginInfo(42, None, 1, None)
                    vk.vkBeginCommandBuffer(cmd_buf, ctypes.byref(begin_info))
                    vk.vkCmdBindPipeline(cmd_buf, 1, pipeline)
                    ds_arr = (ctypes.c_void_p * 1)(desc_set.value)
                    vk.vkCmdBindDescriptorSets(cmd_buf, 1, pipeline_layout, 0, 1, ds_arr, 0, None)

                    pc = BatchPushConstants(num_candidates, stride_words)
                    vk.vkCmdPushConstants(cmd_buf, pipeline_layout, 0x20, 0, 8, ctypes.byref(pc))
                    groups_x = (num_candidates + 63) // 64
                    vk.vkCmdDispatch(cmd_buf, groups_x, 1, 1)
                    vk.vkEndCommandBuffer(cmd_buf)

                    queue = ctypes.c_void_p()
                    vk.vkGetDeviceQueue(logical_dev, 0, 0, ctypes.byref(queue))
                    cmd_bufs_arr = (ctypes.c_void_p * 1)(cmd_buf.value)
                    sub_info = VkSubmitInfo(4, None, 0, None, None, 1, cmd_bufs_arr, 0, None)

                    t_gpu = time.perf_counter()
                    res_sub = vk.vkQueueSubmit(queue, 1, ctypes.byref(sub_info), None)
                    res_wait = vk.vkQueueWaitIdle(queue)
                    gpu_ms = (time.perf_counter() - t_gpu) * 1000.0

                    raw_out = ctypes.string_at(p2.value, out_byte_size)

                    vk.vkDestroyCommandPool(logical_dev, cmd_pool, None)
                    vk.vkDestroyPipeline(logical_dev, pipeline, None)
                    vk.vkDestroyPipelineLayout(logical_dev, pipeline_layout, None)
                    vk.vkDestroyDescriptorPool(logical_dev, desc_pool, None)
                    vk.vkDestroyDescriptorSetLayout(logical_dev, desc_layout, None)
                    vk.vkDestroyShaderModule(logical_dev, shader_mod, None)

                    return {
                        "gpu_executed": (res_sub == 0 and res_wait == 0),
                        "gpu_name": gpu_name,
                        "gpu_queue_ms": round(gpu_ms, 3),
                        "total_ms": round((time.perf_counter() - t0) * 1000.0, 3),
                        "raw_out": raw_out,
                    }
                finally:
                    for b, m in [(b0, m0), (b1, m1), (b2, m2)]:
                        if m.value:
                            vk.vkUnmapMemory(logical_dev, m)
                        if b.value:
                            vk.vkDestroyBuffer(logical_dev, b, None)
                        if m.value:
                            vk.vkFreeMemory(logical_dev, m, None)
            finally:
                if logical_dev.value:
                    vk.vkDestroyDevice(logical_dev, None)
        finally:
            if instance.value:
                vk.vkDestroyInstance(instance, None)

    def batch_hamming_distances(
        self, query_u64: np.ndarray, candidates_u64: np.ndarray, prefer_gpu: bool = True
    ) -> Dict[str, Any]:
        """Compute exact 10,240-bit Hamming distances between query and N candidates."""
        t0 = time.perf_counter()
        q_u32 = np.ascontiguousarray(query_u64, dtype=np.uint64).view(np.uint32)
        c_u32 = np.ascontiguousarray(candidates_u64, dtype=np.uint64).view(np.uint32)
        n = c_u32.shape[0]

        if prefer_gpu and self.is_available and self.vsa_spv_path.exists():
            res = self._dispatch_3buffer_shader(
                self.vsa_spv_path,
                q_u32.tobytes(),
                c_u32.tobytes(),
                n * 4,
                n,
                320,
            )
            if res.get("gpu_executed"):
                dists = np.frombuffer(res["raw_out"], dtype=np.uint32).copy()
                return {
                    "backend": f"VULKAN_WAVE64 ({res['gpu_name']})",
                    "gpu_executed": True,
                    "distances": dists,
                    "gpu_queue_ms": res["gpu_queue_ms"],
                    "elapsed_ms": res["total_ms"],
                }

        # CPU deterministic fallback
        xored = np.bitwise_xor(candidates_u64, query_u64[None, :]).view(np.uint8)
        dists = np.unpackbits(xored, axis=1).sum(axis=1, dtype=np.uint32)
        return {
            "backend": "CPU_NUMPY_FALLBACK",
            "gpu_executed": False,
            "distances": dists,
            "gpu_queue_ms": 0.0,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    def batch_cosine_distances(
        self, query_f32: np.ndarray, candidates_f32: np.ndarray, prefer_gpu: bool = True
    ) -> Dict[str, Any]:
        """Compute dense float32 cosine distances (1 - dot(q, c)) for N candidates on RX 580."""
        t0 = time.perf_counter()
        q = np.ascontiguousarray(query_f32, dtype=np.float32)
        c = np.ascontiguousarray(candidates_f32, dtype=np.float32)
        n, dim = c.shape

        if prefer_gpu and self.is_available and self.cosine_spv_path.exists():
            res = self._dispatch_3buffer_shader(
                self.cosine_spv_path,
                q.tobytes(),
                c.tobytes(),
                n * 4,
                n,
                dim,
            )
            if res.get("gpu_executed"):
                dists = np.frombuffer(res["raw_out"], dtype=np.float32).copy()
                return {
                    "backend": f"VULKAN_WAVE64 ({res['gpu_name']})",
                    "gpu_executed": True,
                    "distances": dists,
                    "gpu_queue_ms": res["gpu_queue_ms"],
                    "elapsed_ms": res["total_ms"],
                }

        dists = np.maximum(0.0, 1.0 - (c @ q)).astype(np.float32)
        return {
            "backend": "CPU_NUMPY_FALLBACK",
            "gpu_executed": False,
            "distances": dists,
            "gpu_queue_ms": 0.0,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }

    def batch_permuted_xor_distances(
        self,
        query_u64: np.ndarray,
        a_candidates_u64: np.ndarray,
        b_candidates_u64: np.ndarray,
        shift_steps: int = 199,
        prefer_gpu: bool = True,
    ) -> Dict[str, Any]:
        """Compute Hamming(query, Permute(A_i, shift_steps) ^ B_i) for N candidate pairs on RX 580 Wave64."""
        t0 = time.perf_counter()
        q_u32 = np.ascontiguousarray(query_u64, dtype=np.uint64).view(np.uint32)
        a_u32 = np.ascontiguousarray(a_candidates_u64, dtype=np.uint64).view(np.uint32)
        b_u32 = np.ascontiguousarray(b_candidates_u64, dtype=np.uint64).view(np.uint32)
        n = a_u32.shape[0]
        if b_u32.shape[0] != n:
            raise ValueError("a_candidates_u64 and b_candidates_u64 must have equal batch size.")

        s = int(shift_steps) % 10240
        pairs_u32 = np.empty((n, 640), dtype=np.uint32)
        pairs_u32[:, :320] = a_u32
        pairs_u32[:, 320:] = b_u32

        if prefer_gpu and self.is_available and self.permuted_xor_spv_path.exists():
            res = self._dispatch_3buffer_shader(
                self.permuted_xor_spv_path,
                q_u32.tobytes(),
                pairs_u32.tobytes(),
                n * 4,
                n,
                s,
            )
            if res.get("gpu_executed"):
                dists = np.frombuffer(res["raw_out"], dtype=np.uint32).copy()
                return {
                    "backend": f"VULKAN_WAVE64 ({res['gpu_name']})",
                    "gpu_executed": True,
                    "distances": dists,
                    "gpu_queue_ms": res["gpu_queue_ms"],
                    "elapsed_ms": res["total_ms"],
                }

        # Exact CPU bit-rotation parity fallback
        a_arr = np.ascontiguousarray(a_candidates_u64, dtype=np.uint64)
        b_arr = np.ascontiguousarray(b_candidates_u64, dtype=np.uint64)
        w_sh = s // 64
        b_sh = s % 64
        if s == 0:
            perm_a = a_arr
        elif b_sh == 0:
            perm_a = np.roll(a_arr, shift=w_sh, axis=1)
        else:
            rolled = np.roll(a_arr, shift=w_sh, axis=1)
            prev = np.roll(rolled, shift=1, axis=1)
            perm_a = (rolled << np.uint64(b_sh)) | (prev >> np.uint64(64 - b_sh))
        xored = np.bitwise_xor(np.bitwise_xor(perm_a, b_arr), query_u64[None, :]).view(np.uint8)
        dists = np.unpackbits(xored, axis=1).sum(axis=1, dtype=np.uint32)
        return {
            "backend": "CPU_NUMPY_FALLBACK",
            "gpu_executed": False,
            "distances": dists,
            "gpu_queue_ms": 0.0,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }
