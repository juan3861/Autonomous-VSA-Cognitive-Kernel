"""Vulkan 1.3 Zero-Copy VRAM Buffer & Descriptor Set Silicon Compute Engine (Polaris 20 / RX 580).

Organ 35 do Substrato Cognitivo Não-LLM (AetherCOS v4.3).
Implementa o ciclo completo de alocação de memória física de vídeo (VRAM),
mapeamento Zero-Copy DMA (HOST_VISIBLE | HOST_COHERENT), vinculação de
Descriptor Sets (vkUpdateDescriptorSets), injeção de Push Constants e
execução real do shader Ising Block Gibbs (ising_block_gibbs.spv) nos 2.304
núcleos Wave64 da GPU AMD Radeon RX 580 com leitura de retorno dos spins relaxados:
- vkGetPhysicalDeviceMemoryProperties -> Localiza Heap HOST_VISIBLE | HOST_COHERENT (Type 1)
- vkCreateBuffer & vkGetBufferMemoryRequirements -> Cria 3 Storage Buffers (J, h, spins)
- vkAllocateMemory & vkBindBufferMemory -> Aloca e vincula memória física compartilhada CPU/GPU
- vkMapMemory & ctypes.memmove -> Escreve matriz de acoplamento J, bias h e spins iniciais
- vkCreateDescriptorPool, vkAllocateDescriptorSets & vkUpdateDescriptorSets -> Vincula buffers aos bindings 0, 1, 2
- vkCmdBindPipeline, vkCmdBindDescriptorSets, vkCmdPushConstants & vkCmdDispatch -> Executa passos de Gibbs Bipartido
- vkQueueSubmit & vkQueueWaitIdle -> Sincroniza fila de hardware da RX 580
- Readback Zero-Copy -> Lê o vetor de spins relaxados diretamente da memória mapeada e calcula a queda de energia ΔE.
"""
from __future__ import annotations

import ctypes
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

from .vulkan_polaris_compute_pipeline import (
    VkApplicationInfo, VkInstanceCreateInfo, VkPhysicalDeviceProperties,
    VkDeviceQueueCreateInfo, VkDeviceCreateInfo, VkShaderModuleCreateInfo,
    VkDescriptorSetLayoutBinding, VkDescriptorSetLayoutCreateInfo,
    VkPushConstantRange, VkPipelineLayoutCreateInfo,
    VkPipelineShaderStageCreateInfo, VkComputePipelineCreateInfo,
    VkCommandPoolCreateInfo, VkCommandBufferAllocateInfo,
    VkCommandBufferBeginInfo, VkSubmitInfo
)


class VkMemoryType(ctypes.Structure):
    _fields_ = [
        ("propertyFlags", ctypes.c_uint32),
        ("heapIndex", ctypes.c_uint32),
    ]


class VkMemoryHeap(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_uint64),
        ("flags", ctypes.c_uint32),
        ("padding", ctypes.c_uint32),
    ]


class VkPhysicalDeviceMemoryProperties(ctypes.Structure):
    _fields_ = [
        ("memoryTypeCount", ctypes.c_uint32),
        ("memoryTypes", VkMemoryType * 32),
        ("memoryHeapCount", ctypes.c_uint32),
        ("padding", ctypes.c_uint32),
        ("memoryHeaps", VkMemoryHeap * 16),
    ]


class VkBufferCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),  # 12 = VK_STRUCTURE_TYPE_BUFFER_CREATE_INFO
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("size", ctypes.c_uint64),
        ("usage", ctypes.c_uint32),  # 0x20 = VK_BUFFER_USAGE_STORAGE_BUFFER_BIT
        ("sharingMode", ctypes.c_uint32),  # 0 = VK_SHARING_MODE_EXCLUSIVE
        ("queueFamilyIndexCount", ctypes.c_uint32),
        ("pQueueFamilyIndices", ctypes.c_void_p),
    ]


class VkMemoryRequirements(ctypes.Structure):
    _fields_ = [
        ("size", ctypes.c_uint64),
        ("alignment", ctypes.c_uint64),
        ("memoryTypeBits", ctypes.c_uint32),
        ("padding", ctypes.c_uint32),
    ]


class VkMemoryAllocateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),  # 5 = VK_STRUCTURE_TYPE_MEMORY_ALLOCATE_INFO
        ("pNext", ctypes.c_void_p),
        ("allocationSize", ctypes.c_uint64),
        ("memoryTypeIndex", ctypes.c_uint32),
    ]


class VkDescriptorPoolSize(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_uint32),  # 7 = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER
        ("descriptorCount", ctypes.c_uint32),
    ]


class VkDescriptorPoolCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),  # 33 = VK_STRUCTURE_TYPE_DESCRIPTOR_POOL_CREATE_INFO
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("maxSets", ctypes.c_uint32),
        ("poolSizeCount", ctypes.c_uint32),
        ("pPoolSizes", ctypes.POINTER(VkDescriptorPoolSize)),
    ]


class VkDescriptorSetAllocateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),  # 34 = VK_STRUCTURE_TYPE_DESCRIPTOR_SET_ALLOCATE_INFO
        ("pNext", ctypes.c_void_p),
        ("descriptorPool", ctypes.c_void_p),
        ("descriptorSetCount", ctypes.c_uint32),
        ("pSetLayouts", ctypes.POINTER(ctypes.c_void_p)),
    ]


class VkDescriptorBufferInfo(ctypes.Structure):
    _fields_ = [
        ("buffer", ctypes.c_void_p),
        ("offset", ctypes.c_uint64),
        ("range", ctypes.c_uint64),
    ]


class VkWriteDescriptorSet(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),  # 35 = VK_STRUCTURE_TYPE_WRITE_DESCRIPTOR_SET
        ("pNext", ctypes.c_void_p),
        ("dstSet", ctypes.c_void_p),
        ("dstBinding", ctypes.c_uint32),
        ("dstArrayElement", ctypes.c_uint32),
        ("descriptorCount", ctypes.c_uint32),
        ("descriptorType", ctypes.c_uint32),  # 7 = VK_DESCRIPTOR_TYPE_STORAGE_BUFFER
        ("pImageInfo", ctypes.c_void_p),
        ("pBufferInfo", ctypes.POINTER(VkDescriptorBufferInfo)),
        ("pTexelBufferView", ctypes.c_void_p),
    ]


class IsingPushConstants(ctypes.Structure):
    _fields_ = [
        ("num_spins", ctypes.c_uint32),
        ("block_parity", ctypes.c_uint32),
        ("beta", ctypes.c_float),
        ("seed", ctypes.c_uint32),
    ]


class VulkanZeroCopyVRAMBufferEngine:
    """
    Motor Zero-Copy de Buffers de Vídeo (VRAM) e Execução Real de Shaders na Radeon RX 580.
    Aloca buffers reais na GPU, transfere matrizes de acoplamento termodinâmico sem cópias
    intermediárias e lê o estado fundamental relaxado diretamente do silício.
    """

    def __init__(self, default_spv_path: Optional[str] = None):
        self.vk_dll = None
        self.is_available = False
        self.default_spv_path = default_spv_path or str(
            Path(__file__).parent.parent / "logic_symbolic" / "shaders" / "ising_block_gibbs.spv"
        )
        try:
            self.vk_dll = ctypes.WinDLL("vulkan-1.dll")
            self._setup_prototypes()
            self.is_available = True
        except Exception:
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

    @staticmethod
    def compute_ising_energy(J: np.ndarray, h: np.ndarray, spins: np.ndarray) -> float:
        s = spins.astype(np.float64)
        return float(-0.5 * np.dot(s, np.dot(J, s)) - np.dot(h, s))

    def execute_zero_copy_ising_relaxation(
        self,
        num_spins: int = 128,
        sweeps: int = 25,
        initial_temp: float = 4.0,
        final_temp: float = 0.05,
        coupling_matrix: Optional[np.ndarray] = None,
        bias_vector: Optional[np.ndarray] = None
    ) -> Dict[str, Any]:
        """
        Executa o relaxamento termodinâmico de Ising diretamente na VRAM da Radeon RX 580
        com buffers mapeados Zero-Copy e Descriptor Sets vinculados.
        """
        t0 = time.perf_counter()

        rng = np.random.RandomState(42)
        if coupling_matrix is not None:
            J = np.array(coupling_matrix, dtype=np.float32)
            num_spins = J.shape[0]
        else:
            # Matriz ferromagnética / frustrada estruturada com acoplamento forte
            J = (rng.randn(num_spins, num_spins) * 0.25 + 0.15).astype(np.float32)
            J = 0.5 * (J + J.T)
            np.fill_diagonal(J, 0.0)

        if bias_vector is not None:
            h = np.array(bias_vector, dtype=np.float32).reshape(num_spins)
        else:
            h = (rng.randn(num_spins) * 0.3).astype(np.float32)

        # Estado inicial alternado de alta energia
        spins_init = np.array([1 if i % 2 == 0 else -1 for i in range(num_spins)], dtype=np.int32)
        initial_energy = self.compute_ising_energy(J, h, spins_init)

        if not self.is_available or self.vk_dll is None or not os.path.exists(self.default_spv_path):
            return {
                "status": "VULKAN_UNAVAILABLE_FALLBACK",
                "zero_copy_executed": False,
                "initial_energy": round(initial_energy, 4)
            }

        spv_bytes = Path(self.default_spv_path).read_bytes()
        vk = self.vk_dll

        # 1. vkCreateInstance
        app_info = VkApplicationInfo(
            0, None, b"Aether_ZeroCopy_VRAM", 1, b"AetherCOS_v4_3", 1, (1 << 22) | (3 << 12)
        )
        inst_info = VkInstanceCreateInfo(1, None, 0, ctypes.pointer(app_info), 0, None, 0, None)
        instance = ctypes.c_void_p()
        if vk.vkCreateInstance(ctypes.byref(inst_info), None, ctypes.byref(instance)) != 0:
            return {"status": "VK_CREATE_INSTANCE_FAILED", "zero_copy_executed": False}

        try:
            # 2. Physical Device & Memory Properties
            dev_cnt = ctypes.c_uint32(0)
            vk.vkEnumeratePhysicalDevices(instance, ctypes.byref(dev_cnt), None)
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

            # 3. Logical Device
            prio = ctypes.c_float(1.0)
            q_info = VkDeviceQueueCreateInfo(2, None, 0, 0, 1, ctypes.pointer(prio))
            d_info = VkDeviceCreateInfo(3, None, 0, 1, ctypes.pointer(q_info), 0, None, 0, None, None)
            logical_dev = ctypes.c_void_p()
            vk.vkCreateDevice(phys_dev, ctypes.byref(d_info), None, ctypes.byref(logical_dev))

            try:
                # 4. Cria e Mapeia os 3 Storage Buffers (J, h, spins) em Bloco Unificado Coerente
                j_bytes = J.tobytes()
                h_bytes = h.tobytes()
                s_bytes = spins_init.tobytes()

                def _create_mapped_buffer(raw_bytes: bytes):
                    b_size = len(raw_bytes)
                    b_info = VkBufferCreateInfo(12, None, 0, b_size, 0x20, 0, 0, None)
                    buf_handle = ctypes.c_void_p()
                    vk.vkCreateBuffer(logical_dev, ctypes.byref(b_info), None, ctypes.byref(buf_handle))

                    req = VkMemoryRequirements()
                    vk.vkGetBufferMemoryRequirements(logical_dev, buf_handle, ctypes.byref(req))

                    alloc_size = max(b_size, req.size)
                    m_info = VkMemoryAllocateInfo(5, None, alloc_size, mem_type_idx)
                    mem_handle = ctypes.c_void_p()
                    vk.vkAllocateMemory(logical_dev, ctypes.byref(m_info), None, ctypes.byref(mem_handle))
                    vk.vkBindBufferMemory(logical_dev, buf_handle, mem_handle, 0)

                    mapped_ptr = ctypes.c_void_p()
                    vk.vkMapMemory(logical_dev, mem_handle, 0, b_size, 0, ctypes.byref(mapped_ptr))
                    ctypes.memmove(mapped_ptr.value, raw_bytes, b_size)
                    return buf_handle, mem_handle, mapped_ptr, b_size

                buf_J, mem_J, ptr_J, size_J = _create_mapped_buffer(j_bytes)
                buf_h, mem_h, ptr_h, size_h = _create_mapped_buffer(h_bytes)
                buf_s, mem_s, ptr_s, size_s = _create_mapped_buffer(s_bytes)

                try:
                    # 5. Shader Module
                    code_arr = (ctypes.c_uint32 * (len(spv_bytes) // 4)).from_buffer_copy(spv_bytes)
                    sm_info = VkShaderModuleCreateInfo(
                        16, None, 0, len(spv_bytes), ctypes.cast(code_arr, ctypes.POINTER(ctypes.c_uint32))
                    )
                    shader_mod = ctypes.c_void_p()
                    vk.vkCreateShaderModule(logical_dev, ctypes.byref(sm_info), None, ctypes.byref(shader_mod))

                    # 6. Descriptor Set Layout, Pool, Set & UpdateDescriptorSets
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

                    b_info_J = VkDescriptorBufferInfo(buf_J.value, 0, size_J)
                    b_info_h = VkDescriptorBufferInfo(buf_h.value, 0, size_h)
                    b_info_s = VkDescriptorBufferInfo(buf_s.value, 0, size_s)

                    writes = (VkWriteDescriptorSet * 3)(
                        VkWriteDescriptorSet(35, None, desc_set.value, 0, 0, 1, 7, None, ctypes.pointer(b_info_J), None),
                        VkWriteDescriptorSet(35, None, desc_set.value, 1, 0, 1, 7, None, ctypes.pointer(b_info_h), None),
                        VkWriteDescriptorSet(35, None, desc_set.value, 2, 0, 1, 7, None, ctypes.pointer(b_info_s), None),
                    )
                    vk.vkUpdateDescriptorSets(logical_dev, 3, writes, 0, None)

                    # 7. Pipeline Layout & Compute Pipeline
                    push_range = VkPushConstantRange(0x20, 0, 16)
                    pl_info = VkPipelineLayoutCreateInfo(30, None, 0, 1, layouts_arr, 1, ctypes.pointer(push_range))
                    pipeline_layout = ctypes.c_void_p()
                    vk.vkCreatePipelineLayout(logical_dev, ctypes.byref(pl_info), None, ctypes.byref(pipeline_layout))

                    stage_info = VkPipelineShaderStageCreateInfo(18, None, 0, 0x20, shader_mod.value, b"main", None)
                    cp_info = VkComputePipelineCreateInfo(29, None, 0, stage_info, pipeline_layout.value, None, -1)
                    pipeline = ctypes.c_void_p()
                    vk.vkCreateComputePipelines(logical_dev, None, 1, ctypes.byref(cp_info), None, ctypes.byref(pipeline))

                    # 8. Command Pool & Command Buffer Recording
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

                    groups_x = (num_spins + 63) // 64
                    temps = np.geomspace(initial_temp, final_temp, sweeps)

                    for step_idx, temp in enumerate(temps):
                        beta_val = float(1.0 / max(temp, 1e-4))
                        # Passo Bipartido A (pares) e B (ímpares)
                        for parity in (0, 1):
                            pc = IsingPushConstants(
                                num_spins,
                                parity,
                                beta_val,
                                int(1337 + step_idx * 31 + parity * 7)
                            )
                            vk.vkCmdPushConstants(
                                cmd_buf, pipeline_layout, 0x20, 0, 16, ctypes.byref(pc)
                            )
                            vk.vkCmdDispatch(cmd_buf, groups_x, 1, 1)

                    vk.vkEndCommandBuffer(cmd_buf)

                    # 9. Queue Submit & Hardware Wait
                    queue = ctypes.c_void_p()
                    vk.vkGetDeviceQueue(logical_dev, 0, 0, ctypes.byref(queue))
                    cmd_bufs_arr = (ctypes.c_void_p * 1)(cmd_buf.value)
                    sub_info = VkSubmitInfo(4, None, 0, None, None, 1, cmd_bufs_arr, 0, None)

                    t_gpu = time.perf_counter()
                    res_sub = vk.vkQueueSubmit(queue, 1, ctypes.byref(sub_info), None)
                    res_wait = vk.vkQueueWaitIdle(queue)
                    gpu_exec_ms = (time.perf_counter() - t_gpu) * 1000.0

                    # 10. Readback Zero-Copy da Memória Mapeada da RX 580
                    out_bytes = ctypes.string_at(ptr_s.value, size_s)
                    spins_final = np.frombuffer(out_bytes, dtype=np.int32).copy()
                    final_energy = self.compute_ising_energy(J, h, spins_final)
                    energy_drop = initial_energy - final_energy

                    # Cleanup intermediário
                    vk.vkDestroyCommandPool(logical_dev, cmd_pool, None)
                    vk.vkDestroyPipeline(logical_dev, pipeline, None)
                    vk.vkDestroyPipelineLayout(logical_dev, pipeline_layout, None)
                    vk.vkDestroyDescriptorPool(logical_dev, desc_pool, None)
                    vk.vkDestroyDescriptorSetLayout(logical_dev, desc_layout, None)
                    vk.vkDestroyShaderModule(logical_dev, shader_mod, None)

                    total_ms = (time.perf_counter() - t0) * 1000.0
                    return {
                        "status": "ZERO_COPY_VRAM_ISING_RELAXED",
                        "zero_copy_executed": True,
                        "gpu_name": gpu_name,
                        "memory_type_index": mem_type_idx,
                        "num_spins": num_spins,
                        "sweeps_executed": sweeps,
                        "total_dispatches_in_cmdbuf": sweeps * 2,
                        "vram_bytes_mapped": size_J + size_h + size_s,
                        "initial_energy": round(initial_energy, 4),
                        "final_ground_energy": round(final_energy, 4),
                        "energy_drop": round(energy_drop, 4),
                        "magnetization": round(float(np.mean(spins_final)), 4),
                        "vk_queue_submit": res_sub,
                        "vk_queue_wait": res_wait,
                        "gpu_queue_latency_ms": round(gpu_exec_ms, 3),
                        "total_elapsed_ms": round(total_ms, 3),
                    }
                finally:
                    for b, m in [(buf_J, mem_J), (buf_h, mem_h), (buf_s, mem_s)]:
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
