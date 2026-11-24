"""Vulkan 1.3 Batch VSA Hamming & Cosine GPU Compute Engine (AMD Radeon RX 580 Wave64).

Dispatches thousands of 10,240-bit hypervector Hamming distance comparisons and dense
float32 cosine similarity computations across the 2,304 Wave64 cores of the AMD RX 580
via `vulkan-1.dll` HOST_VISIBLE | HOST_COHERENT zero-copy VRAM buffers and SPIR-V shaders.
Falls back deterministically to NumPy/CPU if Vulkan hardware is unavailable (e.g., CI).
"""
from __future__ import annotations

import atexit
import ctypes
import threading
import time
import weakref
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
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
        self.dag_vm_spv_path = self.shaders_dir / "vsa_batch_dag_vm.spv"
        self.vk_dll: Optional[ctypes.CDLL] = None
        self.is_available: bool = False
        self._lock = threading.RLock()
        # Resident Vulkan resources (v8.5.0: eliminates ~275ms per-call VkInstance/Device/Pipeline churn)
        self._vk_instance: Optional[ctypes.c_void_p] = None
        self._phys_dev: Optional[ctypes.c_void_p] = None
        self._logical_dev: Optional[ctypes.c_void_p] = None
        self._queue: Optional[ctypes.c_void_p] = None
        self._gpu_name: str = ""
        self._mem_type_idx: int = 0
        self._desc_layout: Optional[ctypes.c_void_p] = None
        self._desc_pool: Optional[ctypes.c_void_p] = None
        self._desc_set: Optional[ctypes.c_void_p] = None
        self._pipeline_layout: Optional[ctypes.c_void_p] = None
        self._cmd_pool: Optional[ctypes.c_void_p] = None
        self._cmd_buf: Optional[ctypes.c_void_p] = None
        self._pipelines: Dict[Path, Tuple[ctypes.c_void_p, ctypes.c_void_p]] = {}
        self._buf_slots: List[Optional[Tuple[ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, int]]] = [None, None, None]
        self._descriptors_dirty: bool = True
        self._probe_vulkan()
        eng_ref = weakref.ref(self)
        atexit.register(lambda: eng_ref().close() if eng_ref() is not None else None)

    def __enter__(self) -> "VulkanBatchVSAEngine":
        return self

    def __exit__(self, *_args: Any) -> None:
        self.close()

    def close(self) -> None:
        """Deterministically release resident Vulkan buffers, pipelines, device, and instance."""
        with self._lock:
            vk = self.vk_dll
            dev = self._logical_dev
            if vk is not None and dev is not None and dev.value:
                try:
                    if self._queue is not None and self._queue.value:
                        vk.vkQueueWaitIdle(self._queue)
                    for idx, slot in enumerate(self._buf_slots):
                        if slot is not None:
                            bh, mh, _ptr, _cap = slot
                            if mh.value:
                                vk.vkUnmapMemory(dev, mh)
                            if bh.value:
                                vk.vkDestroyBuffer(dev, bh, None)
                            if mh.value:
                                vk.vkFreeMemory(dev, mh, None)
                            self._buf_slots[idx] = None
                    for _path, (smod, pipe) in list(self._pipelines.items()):
                        if pipe.value:
                            vk.vkDestroyPipeline(dev, pipe, None)
                        if smod.value:
                            vk.vkDestroyShaderModule(dev, smod, None)
                    self._pipelines.clear()
                    if self._cmd_pool is not None and self._cmd_pool.value:
                        vk.vkDestroyCommandPool(dev, self._cmd_pool, None)
                        self._cmd_pool = None
                        self._cmd_buf = None
                    if self._pipeline_layout is not None and self._pipeline_layout.value:
                        vk.vkDestroyPipelineLayout(dev, self._pipeline_layout, None)
                        self._pipeline_layout = None
                    if self._desc_pool is not None and self._desc_pool.value:
                        vk.vkDestroyDescriptorPool(dev, self._desc_pool, None)
                        self._desc_pool = None
                        self._desc_set = None
                    if self._desc_layout is not None and self._desc_layout.value:
                        vk.vkDestroyDescriptorSetLayout(dev, self._desc_layout, None)
                        self._desc_layout = None
                    vk.vkDestroyDevice(dev, None)
                except Exception:
                    pass
                self._logical_dev = None
                self._queue = None
            if vk is not None and self._vk_instance is not None and self._vk_instance.value:
                try:
                    vk.vkDestroyInstance(self._vk_instance, None)
                except Exception:
                    pass
                self._vk_instance = None
                self._phys_dev = None
            self._descriptors_dirty = True

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
        vk.vkResetCommandBuffer.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        vk.vkResetCommandBuffer.restype = ctypes.c_int32

    def _ensure_resident_device(self) -> bool:
        """Initialize VkInstance, VkDevice, DescriptorSet, PipelineLayout & CommandBuffer once."""
        if self._logical_dev is not None and self._logical_dev.value:
            return True
        vk = self.vk_dll
        if not self.is_available or vk is None:
            return False

        app_info = VkApplicationInfo(0, None, b"Aether_Batch_GPU", 1, b"AetherCOS_v8_5", 1, (1 << 22) | (3 << 12))
        inst_info = VkInstanceCreateInfo(1, None, 0, ctypes.pointer(app_info), 0, None, 0, None)
        instance = ctypes.c_void_p()
        if vk.vkCreateInstance(ctypes.byref(inst_info), None, ctypes.byref(instance)) != 0:
            return False

        dev_cnt = ctypes.c_uint32(0)
        vk.vkEnumeratePhysicalDevices(instance, ctypes.byref(dev_cnt), None)
        if dev_cnt.value == 0:
            vk.vkDestroyInstance(instance, None)
            return False
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
        if vk.vkCreateDevice(phys_dev, ctypes.byref(d_info), None, ctypes.byref(logical_dev)) != 0:
            vk.vkDestroyInstance(instance, None)
            return False

        queue = ctypes.c_void_p()
        vk.vkGetDeviceQueue(logical_dev, 0, 0, ctypes.byref(queue))

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

        push_range = VkPushConstantRange(0x20, 0, 8)
        pl_info = VkPipelineLayoutCreateInfo(30, None, 0, 1, layouts_arr, 1, ctypes.pointer(push_range))
        pipeline_layout = ctypes.c_void_p()
        vk.vkCreatePipelineLayout(logical_dev, ctypes.byref(pl_info), None, ctypes.byref(pipeline_layout))

        cp_pool_info = VkCommandPoolCreateInfo(39, None, 2, 0)
        cmd_pool = ctypes.c_void_p()
        vk.vkCreateCommandPool(logical_dev, ctypes.byref(cp_pool_info), None, ctypes.byref(cmd_pool))

        cmd_alloc = VkCommandBufferAllocateInfo(40, None, cmd_pool.value, 0, 1)
        cmd_buf = ctypes.c_void_p()
        vk.vkAllocateCommandBuffers(logical_dev, ctypes.byref(cmd_alloc), ctypes.byref(cmd_buf))

        self._vk_instance = instance
        self._phys_dev = phys_dev
        self._logical_dev = logical_dev
        self._queue = queue
        self._gpu_name = gpu_name
        self._mem_type_idx = mem_type_idx
        self._desc_layout = desc_layout
        self._desc_pool = desc_pool
        self._desc_set = desc_set
        self._pipeline_layout = pipeline_layout
        self._cmd_pool = cmd_pool
        self._cmd_buf = cmd_buf
        self._descriptors_dirty = True
        return True

    def _ensure_buffer_slot(self, slot_idx: int, required_bytes: int) -> ctypes.c_void_p:
        """Ensure resident host-coherent mapped buffer slot has at least `required_bytes` capacity."""
        slot = self._buf_slots[slot_idx]
        if slot is not None and slot[3] >= required_bytes:
            return slot[2]

        vk = self.vk_dll
        dev = self._logical_dev
        if slot is not None:
            old_b, old_m, _old_p, old_cap = slot
            if old_m.value:
                vk.vkUnmapMemory(dev, old_m)
            if old_b.value:
                vk.vkDestroyBuffer(dev, old_b, None)
            if old_m.value:
                vk.vkFreeMemory(dev, old_m, None)
            new_cap = max(required_bytes, old_cap * 2)
        else:
            new_cap = max(required_bytes, 4096)

        b_info = VkBufferCreateInfo(12, None, 0, new_cap, 0x20, 0, 0, None)
        bh = ctypes.c_void_p()
        vk.vkCreateBuffer(dev, ctypes.byref(b_info), None, ctypes.byref(bh))
        req = VkMemoryRequirements()
        vk.vkGetBufferMemoryRequirements(dev, bh, ctypes.byref(req))
        m_info = VkMemoryAllocateInfo(5, None, max(new_cap, req.size), self._mem_type_idx)
        mh = ctypes.c_void_p()
        vk.vkAllocateMemory(dev, ctypes.byref(m_info), None, ctypes.byref(mh))
        vk.vkBindBufferMemory(dev, bh, mh, 0)
        ptr = ctypes.c_void_p()
        vk.vkMapMemory(dev, mh, 0, new_cap, 0, ctypes.byref(ptr))
        self._buf_slots[slot_idx] = (bh, mh, ptr, new_cap)
        self._descriptors_dirty = True
        return ptr

    def _get_or_compile_pipeline(self, spv_path: Path) -> ctypes.c_void_p:
        cached = self._pipelines.get(spv_path)
        if cached is not None:
            return cached[1]
        vk = self.vk_dll
        dev = self._logical_dev
        spv_bytes = spv_path.read_bytes()
        code_arr = (ctypes.c_uint32 * (len(spv_bytes) // 4)).from_buffer_copy(spv_bytes)
        sm_info = VkShaderModuleCreateInfo(16, None, 0, len(spv_bytes), ctypes.cast(code_arr, ctypes.POINTER(ctypes.c_uint32)))
        shader_mod = ctypes.c_void_p()
        vk.vkCreateShaderModule(dev, ctypes.byref(sm_info), None, ctypes.byref(shader_mod))

        stage_info = VkPipelineShaderStageCreateInfo(18, None, 0, 0x20, shader_mod.value, b"main", None)
        cp_info = VkComputePipelineCreateInfo(29, None, 0, stage_info, self._pipeline_layout.value, None, -1)
        pipeline = ctypes.c_void_p()
        vk.vkCreateComputePipelines(dev, None, 1, ctypes.byref(cp_info), None, ctypes.byref(pipeline))
        self._pipelines[spv_path] = (shader_mod, pipeline)
        return pipeline

    def _dispatch_3buffer_shader(
        self,
        spv_path: Path,
        buf0_bytes: bytes,
        buf1_bytes: bytes,
        out_byte_size: int,
        num_candidates: int,
        stride_words: int,
        groups_x: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute a 3-storage-buffer Wave64 SPIR-V shader via persistent Vulkan pipelines."""
        t0 = time.perf_counter()
        vk = self.vk_dll
        if not self.is_available or vk is None or not spv_path.exists():
            return {"gpu_executed": False, "status": "VULKAN_UNAVAILABLE"}

        with self._lock:
            if not self._ensure_resident_device():
                return {"gpu_executed": False, "status": "VK_RESIDENT_INIT_FAILED"}

            p0 = self._ensure_buffer_slot(0, len(buf0_bytes))
            p1 = self._ensure_buffer_slot(1, len(buf1_bytes))
            p2 = self._ensure_buffer_slot(2, out_byte_size)
            ctypes.memmove(p0.value, buf0_bytes, len(buf0_bytes))
            ctypes.memmove(p1.value, buf1_bytes, len(buf1_bytes))

            if self._descriptors_dirty:
                bi0 = VkDescriptorBufferInfo(self._buf_slots[0][0].value, 0, self._buf_slots[0][3])
                bi1 = VkDescriptorBufferInfo(self._buf_slots[1][0].value, 0, self._buf_slots[1][3])
                bi2 = VkDescriptorBufferInfo(self._buf_slots[2][0].value, 0, self._buf_slots[2][3])
                writes = (VkWriteDescriptorSet * 3)(
                    VkWriteDescriptorSet(35, None, self._desc_set.value, 0, 0, 1, 7, None, ctypes.pointer(bi0), None),
                    VkWriteDescriptorSet(35, None, self._desc_set.value, 1, 0, 1, 7, None, ctypes.pointer(bi1), None),
                    VkWriteDescriptorSet(35, None, self._desc_set.value, 2, 0, 1, 7, None, ctypes.pointer(bi2), None),
                )
                vk.vkUpdateDescriptorSets(self._logical_dev, 3, writes, 0, None)
                self._descriptors_dirty = False

            pipeline = self._get_or_compile_pipeline(spv_path)
            vk.vkResetCommandBuffer(self._cmd_buf, 0)
            begin_info = VkCommandBufferBeginInfo(42, None, 1, None)
            vk.vkBeginCommandBuffer(self._cmd_buf, ctypes.byref(begin_info))
            vk.vkCmdBindPipeline(self._cmd_buf, 1, pipeline)
            ds_arr = (ctypes.c_void_p * 1)(self._desc_set.value)
            vk.vkCmdBindDescriptorSets(self._cmd_buf, 1, self._pipeline_layout, 0, 1, ds_arr, 0, None)

            pc = BatchPushConstants(num_candidates, stride_words)
            vk.vkCmdPushConstants(self._cmd_buf, self._pipeline_layout, 0x20, 0, 8, ctypes.byref(pc))
            dispatch_groups = int(groups_x) if groups_x is not None else (num_candidates + 63) // 64
            vk.vkCmdDispatch(self._cmd_buf, dispatch_groups, 1, 1)
            vk.vkEndCommandBuffer(self._cmd_buf)

            cmd_bufs_arr = (ctypes.c_void_p * 1)(self._cmd_buf.value)
            sub_info = VkSubmitInfo(4, None, 0, None, None, 1, cmd_bufs_arr, 0, None)

            t_gpu = time.perf_counter()
            res_sub = vk.vkQueueSubmit(self._queue, 1, ctypes.byref(sub_info), None)
            res_wait = vk.vkQueueWaitIdle(self._queue)
            gpu_ms = (time.perf_counter() - t_gpu) * 1000.0

            raw_out = ctypes.string_at(p2.value, out_byte_size)
            return {
                "gpu_executed": (res_sub == 0 and res_wait == 0),
                "gpu_name": self._gpu_name,
                "gpu_queue_ms": round(gpu_ms, 3),
                "total_ms": round((time.perf_counter() - t0) * 1000.0, 3),
                "raw_out": raw_out,
            }

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

    def batch_execute_dag_program(
        self,
        query_u64: np.ndarray,
        a_candidates_u64: np.ndarray,
        b_candidates_u64: np.ndarray,
        program_ops: List[Tuple[Any, ...]],
        compare_regs: Tuple[int, int] = (0, 3),
        prefer_gpu: bool = True,
    ) -> Dict[str, Any]:
        """Execute an arbitrary multi-op VSA DAG bytecode program in RX 580 Wave64 on-chip LDS."""
        t0 = time.perf_counter()
        op_codes = {
            "LOAD_Q": 1,
            "LOAD_A": 2,
            "LOAD_B": 3,
            "XOR": 4,
            "AND": 5,
            "OR": 6,
            "NOT": 7,
            "PERMUTE": 8,
            "UNPERMUTE": 9,
        }
        if not (1 <= len(program_ops) <= 64):
            raise ValueError("GPU DAG VM expects 1..64 bytecode instructions.")

        q_u64 = np.ascontiguousarray(query_u64, dtype=np.uint64)
        a_u64 = np.ascontiguousarray(a_candidates_u64, dtype=np.uint64)
        b_u64 = np.ascontiguousarray(b_candidates_u64, dtype=np.uint64)
        n = int(a_u64.shape[0])
        if b_u64.shape[0] != n:
            raise ValueError("a_candidates_u64 and b_candidates_u64 must have equal batch size.")

        cmp_a = int(compare_regs[0]) & 0x3
        cmp_b = int(compare_regs[1]) & 0x3

        # Serialize [query(320), num_ops, (instr, imm) * num_ops] cleanly into uint32 buffer 0
        prog_header = [len(program_ops)]
        for step in program_ops:
            mnemonic = str(step[0]).upper()
            if mnemonic not in op_codes:
                raise ValueError(f"Unsupported GPU DAG opcode: {mnemonic}")
            op_id = op_codes[mnemonic]
            dst = int(step[1]) & 0x3
            s1 = 0
            s2 = 0
            imm = 0
            if mnemonic in ("XOR", "AND", "OR"):
                s1 = int(step[2]) & 0x3
                s2 = int(step[3]) & 0x3
            elif mnemonic == "NOT":
                s1 = int(step[2]) & 0x3
            elif mnemonic in ("PERMUTE", "UNPERMUTE"):
                s1 = int(step[2]) & 0x3
                imm = int(step[3]) % 10240
            instr_u32 = op_id | (dst << 8) | (s1 << 16) | (s2 << 24)
            prog_header.extend((instr_u32, imm))

        q_prog_u32 = np.concatenate([
            q_u64.view(np.uint32),
            np.asarray(prog_header, dtype=np.uint32),
        ])
        pairs_u32 = np.empty((n, 640), dtype=np.uint32)
        pairs_u32[:, :320] = a_u64.view(np.uint32)
        pairs_u32[:, 320:] = b_u64.view(np.uint32)

        compare_packed = cmp_a | (cmp_b << 8)
        if prefer_gpu and self.is_available and self.dag_vm_spv_path.exists():
            res = self._dispatch_3buffer_shader(
                self.dag_vm_spv_path,
                q_prog_u32.tobytes(),
                pairs_u32.tobytes(),
                n * 4,
                n,
                compare_packed,
                groups_x=n,
            )
            if res.get("gpu_executed"):
                dists = np.frombuffer(res["raw_out"], dtype=np.uint32).copy()
                return {
                    "backend": f"VULKAN_WAVE64_LDS_VM ({res['gpu_name']})",
                    "gpu_executed": True,
                    "op_count": len(program_ops),
                    "distances": dists,
                    "gpu_queue_ms": res["gpu_queue_ms"],
                    "elapsed_ms": res["total_ms"],
                }

        # Exact CPU bit-parity VM interpreter fallback
        regs = [np.zeros((n, 160), dtype=np.uint64) for _ in range(4)]

        def _perm_batch(arr: np.ndarray, s_val: int, inv: bool = False) -> np.ndarray:
            raw_s = int(s_val) % 10240
            eff_s = (10240 - raw_s) if (inv and raw_s > 0) else raw_s
            if eff_s == 0:
                return arr.copy()
            w_sh = eff_s // 64
            b_sh = eff_s % 64
            rolled = np.roll(arr, shift=w_sh, axis=1)
            if b_sh == 0:
                return rolled
            prev = np.roll(rolled, shift=1, axis=1)
            return (rolled << np.uint64(b_sh)) | (prev >> np.uint64(64 - b_sh))

        for step in program_ops:
            mnemonic = str(step[0]).upper()
            dst = int(step[1]) & 0x3
            if mnemonic == "LOAD_Q":
                regs[dst][:] = q_u64[None, :]
            elif mnemonic == "LOAD_A":
                regs[dst][:] = a_u64
            elif mnemonic == "LOAD_B":
                regs[dst][:] = b_u64
            elif mnemonic == "XOR":
                regs[dst] = np.bitwise_xor(regs[int(step[2]) & 0x3], regs[int(step[3]) & 0x3])
            elif mnemonic == "AND":
                regs[dst] = np.bitwise_and(regs[int(step[2]) & 0x3], regs[int(step[3]) & 0x3])
            elif mnemonic == "OR":
                regs[dst] = np.bitwise_or(regs[int(step[2]) & 0x3], regs[int(step[3]) & 0x3])
            elif mnemonic == "NOT":
                regs[dst] = np.bitwise_not(regs[int(step[2]) & 0x3])
            elif mnemonic == "PERMUTE":
                regs[dst] = _perm_batch(regs[int(step[2]) & 0x3], int(step[3]), inv=False)
            elif mnemonic == "UNPERMUTE":
                regs[dst] = _perm_batch(regs[int(step[2]) & 0x3], int(step[3]), inv=True)

        xored = np.bitwise_xor(regs[cmp_a], regs[cmp_b]).view(np.uint8)
        dists = np.unpackbits(xored, axis=1).sum(axis=1, dtype=np.uint32)
        return {
            "backend": "CPU_NUMPY_VM_FALLBACK",
            "gpu_executed": False,
            "op_count": len(program_ops),
            "distances": dists,
            "gpu_queue_ms": 0.0,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }
