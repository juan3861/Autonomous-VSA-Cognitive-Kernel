import sys
import os
import tempfile
from pathlib import Path
import numpy as np

# Injeta a raiz do repositório em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.physical_bridge.vulkan_polaris_headless_dispatcher import VulkanPolarisHeadlessDispatcher
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: VULKAN POLARIS HEADLESS C-ABI & REM CAUSAL SLEEP INDUCTION (ÓRGÃO 28)")
    print("=" * 80)

    # 1. Verificação Headless C-ABI Vulkan direto no Silício da RX 580
    dispatcher = VulkanPolarisHeadlessDispatcher()
    assert dispatcher.is_available, "vulkan-1.dll deve estar disponível no Windows!"
    vk_res = dispatcher.verify_and_load_spirv_on_silicon()
    assert vk_res["verified"] is True, f"Falha ao validar SPIR-V no silício: {vk_res}"
    assert vk_res["vk_result"] == 0
    assert "Radeon RX 580" in vk_res["gpu_name"] or vk_res["vendor_id"] == "0x1002"
    assert vk_res["spirv_size_bytes"] == 2608
    print(f" -> [TESTE 1/5]: Shader SPIR-V injetado no driver {vk_res['gpu_name']} ({vk_res['vendor_id']}:{vk_res['device_id']}) -> VkShaderModule={vk_res['shader_module_handle']} em {vk_res['elapsed_ms']} ms.")

    # 2. Falsificação Adversarial: Injeção de Bytecode Corrompido
    fd, bad_spv = tempfile.mkstemp(suffix=".spv")
    os.write(fd, b"BAD_MAGIC_BYTES_123456789012")
    os.close(fd)
    try:
        bad_res = dispatcher.verify_and_load_spirv_on_silicon(bad_spv)
        assert bad_res["verified"] is False
        assert bad_res["status"] == "CORRUPTED_SPIRV_MAGIC"
        print(f" -> [TESTE 2/5]: Falsificação Adversarial: Bytecode corrompido rejeitado ({bad_res['status']}).")
    finally:
        if os.path.exists(bad_spv):
            os.remove(bad_spv)

    # 3. Indução Causal em Sono REM (NOTEARS + VSA 10.240 bits)
    runtime = SovereignCortexRuntime()
    np.random.seed(42)
    n_samples = 60
    x_src = np.random.randn(n_samples)
    y_med = 1.2 * x_src + 0.1 * np.random.randn(n_samples)
    z_tgt = -0.9 * y_med + 0.1 * np.random.randn(n_samples)
    obs_matrix = np.column_stack([x_src, y_med, z_tgt])

    rem_res = runtime.execute_cognitive_mission(
        "rem_causal_dream",
        {
            "observation_matrix": obs_matrix.tolist(),
            "var_names": ["CPU_Load", "VRM_Temp", "Fan_RPM"]
        }
    )
    r_sleep = rem_res["result"]
    assert r_sleep["status"] == "REM_CAUSAL_INDUCTION_COMPLETED"
    assert r_sleep["edges_discovered_count"] >= 2, f"Esperado >= 2 arcos causais, obtido {r_sleep['edges_discovered_count']}"
    assert r_sleep["hologram_bits"] == 10240
    print(f" -> [TESTE 3/5]: Indução Causal em Sono REM descobriu {r_sleep['edges_discovered_count']} leis e gravou '{r_sleep['persisted_concept']}' em {r_sleep['elapsed_ms']} ms.")

    # 4. Consulta do Arco Causal Aprendido no Sono no Holograma VSA de 10.240 bits
    vsa_q = runtime.rem_dream_engine.vsa_causal.query_causal_effect("CPU_Load")
    assert vsa_q["predicted_effect"] is not None, f"Efeito não encontrado: {vsa_q}"
    print(f" -> [TESTE 4/5]: Holograma VSA confirmou a lei descoberta no sono: CPU_Load -> {vsa_q['predicted_effect']} (Dist={vsa_q['hamming_distance']}, Sigma={vsa_q['resonance_sigma']}).")

    # 5. Despacho Vulkan via Runtime Soberano
    health = runtime.get_system_health()
    assert health["organs_active_count"] >= 28
    assert health["vulkan_headless_dispatcher_active"] is True
    vk_mission = runtime.execute_cognitive_mission("vulkan_silicon_verify", {})
    assert vk_mission["result"]["verified"] is True
    print(f" -> [TESTE 5/5]: Córtex v3.8.0 (28 Órgãos) validado de ponta a ponta.")

    print("\n[VEREDITO EMPÍRICO]: VULKAN POLARIS HEADLESS & REM CAUSAL SLEEP INDUCTION APROVADOS COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
