import ctypes
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

# ==============================================================================
# AETHERMIND VULKAN POLARIS 20 HEADLESS C-ABI DISPATCHER & SHADER PROVER
# Órgão 28 do Substrato Cognitivo Soberano (Bare-Metal vulkan-1.dll C-ABI)
# ==============================================================================
# Conecta-se diretamente ao driver proprietário AMD via C:\Windows\System32\vulkan-1.dll
# sem dependências externas (zero PyVulkan, zero wrappers pesados).
# Executa:
#   1. vkCreateInstance -> Instanciação Headless Vulkan 1.3
#   2. vkEnumeratePhysicalDevices & vkGetPhysicalDeviceProperties -> Leitura direta do silício (RX 580)
#   3. vkCreateDevice -> Criação de Logical Compute Device na fila nativa da GPU
#   4. vkCreateShaderModule -> Injeção e compilação em hardware do bytecode SPIR-V Wave64
#   5. Teardown atômico limpo (vkDestroyShaderModule, vkDestroyDevice, vkDestroyInstance)
# ==============================================================================

class VkApplicationInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),
        ("pNext", ctypes.c_void_p),
        ("pApplicationName", ctypes.c_char_p),
        ("applicationVersion", ctypes.c_uint32),
        ("pEngineName", ctypes.c_char_p),
        ("engineVersion", ctypes.c_uint32),
        ("apiVersion", ctypes.c_uint32),
    ]

class VkInstanceCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("pApplicationInfo", ctypes.POINTER(VkApplicationInfo)),
        ("enabledLayerCount", ctypes.c_uint32),
        ("ppEnabledLayerNames", ctypes.POINTER(ctypes.c_char_p)),
        ("enabledExtensionCount", ctypes.c_uint32),
        ("ppEnabledExtensionNames", ctypes.POINTER(ctypes.c_char_p)),
    ]

class VkPhysicalDeviceProperties(ctypes.Structure):
    _fields_ = [
        ("apiVersion", ctypes.c_uint32),
        ("driverVersion", ctypes.c_uint32),
        ("vendorID", ctypes.c_uint32),
        ("deviceID", ctypes.c_uint32),
        ("deviceType", ctypes.c_uint32),
        ("deviceName", ctypes.c_char * 256),
        ("pipelineCacheUUID", ctypes.c_uint8 * 16),
        ("padding", ctypes.c_uint8 * 600),
    ]

class VkDeviceQueueCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("queueFamilyIndex", ctypes.c_uint32),
        ("queueCount", ctypes.c_uint32),
        ("pQueuePriorities", ctypes.POINTER(ctypes.c_float)),
    ]

class VkDeviceCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("queueCreateInfoCount", ctypes.c_uint32),
        ("pQueueCreateInfos", ctypes.POINTER(VkDeviceQueueCreateInfo)),
        ("enabledLayerCount", ctypes.c_uint32),
        ("ppEnabledLayerNames", ctypes.POINTER(ctypes.c_char_p)),
        ("enabledExtensionCount", ctypes.c_uint32),
        ("ppEnabledExtensionNames", ctypes.POINTER(ctypes.c_char_p)),
        ("pEnabledFeatures", ctypes.c_void_p),
    ]

class VkShaderModuleCreateInfo(ctypes.Structure):
    _fields_ = [
        ("sType", ctypes.c_uint32),
        ("pNext", ctypes.c_void_p),
        ("flags", ctypes.c_uint32),
        ("codeSize", ctypes.c_size_t),
        ("pCode", ctypes.POINTER(ctypes.c_uint32)),
    ]


class VulkanPolarisHeadlessDispatcher:
    """
    Motor Headless C-ABI Vulkan para validação e carregamento de Shaders SPIR-V
    diretamente no silício da GPU AMD Radeon RX 580 (Polaris 20).
    """
    def __init__(self, default_spv_path: Optional[str] = None):
        self.vk_dll = None
        self.is_available = False
        if default_spv_path is None:
            base = Path(__file__).parent.parent
            self.default_spv_path = str(base / "logic_symbolic" / "shaders" / "ising_block_gibbs.spv")
        else:
            self.default_spv_path = default_spv_path

        try:
            self.vk_dll = ctypes.WinDLL("vulkan-1.dll")
            self.is_available = True
        except Exception:
            self.is_available = False

    def verify_and_load_spirv_on_silicon(self, spv_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Executa o ciclo completo C-ABI Headless na GPU física:
        Instância -> Enumeração Física -> Criação de Dispositivo Lógico -> Compilação de Shader SPIR-V no Driver -> Teardown.
        """
        t0 = time.perf_counter()
        target_spv = spv_path or self.default_spv_path

        if not self.is_available or self.vk_dll is None:
            return {"status": "VULKAN_DLL_UNAVAILABLE", "verified": False}

        if not os.path.exists(target_spv):
            return {"status": "SPIRV_FILE_NOT_FOUND", "path": target_spv, "verified": False}

        with open(target_spv, "rb") as f:
            spv_bytes = f.read()

        if len(spv_bytes) < 20 or len(spv_bytes) % 4 != 0:
            return {"status": "INVALID_SPIRV_ALIGNMENT", "size_bytes": len(spv_bytes), "verified": False}

        # Verifica Magic Number SPIR-V (0x07230203)
        magic = int.from_bytes(spv_bytes[:4], byteorder="little")
        if magic != 0x07230203:
            return {"status": "CORRUPTED_SPIRV_MAGIC", "magic_hex": hex(magic), "verified": False}

        vk = self.vk_dll
        # 1. vkCreateInstance
        app_info = VkApplicationInfo(0, None, b"AetherMind_Cortex", 1, b"AetherCOS_BareMetal", 1, (1 << 22) | (3 << 12))
        create_info = VkInstanceCreateInfo(1, None, 0, ctypes.pointer(app_info), 0, None, 0, None)
        instance = ctypes.c_void_p()
        res_inst = vk.vkCreateInstance(ctypes.byref(create_info), None, ctypes.byref(instance))
        if res_inst != 0 or not instance.value:
            return {"status": "VK_CREATE_INSTANCE_FAILED", "vk_result": res_inst, "verified": False}

        try:
            # 2. vkEnumeratePhysicalDevices
            dev_count = ctypes.c_uint32(0)
            vk.vkEnumeratePhysicalDevices(instance, ctypes.byref(dev_count), None)
            if dev_count.value == 0:
                return {"status": "NO_PHYSICAL_GPU_FOUND", "verified": False}

            devs = (ctypes.c_void_p * dev_count.value)()
            vk.vkEnumeratePhysicalDevices(instance, ctypes.byref(dev_count), devs)
            phys_dev = ctypes.c_void_p(devs[0])

            # 3. vkGetPhysicalDeviceProperties
            props = VkPhysicalDeviceProperties()
            vk.vkGetPhysicalDeviceProperties(phys_dev, ctypes.byref(props))
            gpu_name = props.deviceName.decode("utf-8", errors="replace").strip("\x00")
            vendor_hex = hex(props.vendorID)
            device_hex = hex(props.deviceID)
            api_major = (props.apiVersion >> 22) & 0x3FF
            api_minor = (props.apiVersion >> 12) & 0x3FF
            api_patch = props.apiVersion & 0xFFF

            # 4. vkCreateDevice (Queue Family 0 - Graphics/Compute Universal Queue on Polaris)
            prio = ctypes.c_float(1.0)
            q_info = VkDeviceQueueCreateInfo(2, None, 0, 0, 1, ctypes.pointer(prio))
            d_info = VkDeviceCreateInfo(3, None, 0, 1, ctypes.pointer(q_info), 0, None, 0, None, None)
            logical_dev = ctypes.c_void_p()
            res_dev = vk.vkCreateDevice(phys_dev, ctypes.byref(d_info), None, ctypes.byref(logical_dev))
            if res_dev != 0 or not logical_dev.value:
                return {
                    "status": "VK_CREATE_DEVICE_FAILED",
                    "vk_result": res_dev,
                    "gpu_name": gpu_name,
                    "verified": False
                }

            try:
                # 5. vkCreateShaderModule (Injeção física do bytecode SPIR-V no driver AMD)
                u32_count = len(spv_bytes) // 4
                code_arr = (ctypes.c_uint32 * u32_count).from_buffer_copy(spv_bytes)
                sm_info = VkShaderModuleCreateInfo(
                    16, None, 0, len(spv_bytes),
                    ctypes.cast(code_arr, ctypes.POINTER(ctypes.c_uint32))
                )
                shader_mod = ctypes.c_void_p()
                res_sm = vk.vkCreateShaderModule(logical_dev, ctypes.byref(sm_info), None, ctypes.byref(shader_mod))
                shader_handle_hex = hex(shader_mod.value or 0)

                if res_sm == 0 and shader_mod.value:
                    vk.vkDestroyShaderModule(logical_dev, shader_mod, None)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                    return {
                        "status": "VULKAN_SILICON_SHADER_VERIFIED",
                        "verified": True,
                        "vk_result": 0,
                        "gpu_name": gpu_name,
                        "vendor_id": vendor_hex,
                        "device_id": device_hex,
                        "vulkan_api": f"{api_major}.{api_minor}.{api_patch}",
                        "instance_handle": hex(instance.value),
                        "logical_device_handle": hex(logical_dev.value),
                        "shader_module_handle": shader_handle_hex,
                        "spirv_size_bytes": len(spv_bytes),
                        "spirv_magic_verified": "0x7230203",
                        "elapsed_ms": round(elapsed_ms, 3)
                    }
                else:
                    return {
                        "status": "VK_CREATE_SHADER_MODULE_FAILED",
                        "vk_result": res_sm,
                        "gpu_name": gpu_name,
                        "verified": False
                    }
            finally:
                vk.vkDestroyDevice(logical_dev, None)
        finally:
            vk.vkDestroyInstance(instance, None)
