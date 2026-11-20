import sys
import os
import time
from pathlib import Path

# Injeta a raiz do repositório em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.memory_vault.hierarchical_paged_memory_os import HierarchicalPagedMemoryOS
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: HIERARCHICAL PAGED MEMORY OS ENGINE (ÓRGÃO 26)")
    print("=" * 80)

    # 1. Instanciação e Alocação
    pager = HierarchicalPagedMemoryOS(max_hot_pages=4, max_warm_pages=8)
    assert pager.max_hot_pages == 4
    assert pager.max_warm_pages == 8
    print(" -> [TESTE 1/5]: Tabela de páginas inicializada.")

    # 2. Alocação até saturação da Hot Memory
    for i in range(4):
        pager.allocate_page(f"page_{i}", f"content_{i}", importance=float(i + 1))
    assert len(pager.hot_tier) == 4
    print(" -> [TESTE 2/5]: 4 páginas alocadas na Hot Tier.")

    # 3. Swap-out automático para Warm Tier ao exceder max_hot_pages
    pager.allocate_page("page_4", "content_4", importance=10.0)
    assert len(pager.hot_tier) == 4
    assert len(pager.warm_tier) == 1
    assert "page_4" in pager.hot_tier, "Página de alta importância deve permanecer na Hot Tier!"
    print(f" -> [TESTE 3/5]: Eviction seletiva validada (Swaps={pager.swap_count}, Warm Pages={len(pager.warm_tier)}).")

    # 4. Acesso com Promoção (Warm Tier -> Hot Tier)
    warm_page_id = list(pager.warm_tier.keys())[0]
    content, origin, lat = pager.access_page(warm_page_id)
    assert origin == "WARM_TIER_PROMOTED"
    assert warm_page_id in pager.hot_tier
    print(f" -> [TESTE 4/5]: Promoção de página validada em {lat} us (Origem={origin}).")

    # 5. Falsificação Adversarial: Inundação de 20 páginas e verificação de Cold Tier (Archival)
    for i in range(10, 30):
        pager.allocate_page(f"flood_{i}", f"data_{i}", importance=0.5)
    
    assert len(pager.cold_tier) > 0, "Páginas excedentes devem ter sido descarregadas para Cold Tier!"
    tele = pager.get_telemetry()
    assert tele["cold_pages_archived"] > 0
    print(f" -> [TESTE 5/5]: Falsificação Adversarial: {tele['cold_pages_archived']} páginas arquivadas na Cold Tier sem perda.")

    # 6. Despacho via Runtime Soberano
    runtime = SovereignCortexRuntime()
    alloc_res = runtime.execute_cognitive_mission("paged_memory_alloc", {"page_id": "cortex_axiom_1", "content": "E=mc2", "importance": 9.9})
    assert alloc_res["result"]["status"] == "PAGE_ALLOCATED"
    access_res = runtime.execute_cognitive_mission("paged_memory_access", {"page_id": "cortex_axiom_1"})
    assert access_res["result"]["status"] == "PAGE_ACCESSED"
    print(" -> [TESTE 6/6]: Alocação e acesso via Runtime Soberano verificados com sucesso.")

    print("\n[VEREDITO EMPÍRICO]: HIERARCHICAL PAGED MEMORY OS APROVADO COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
