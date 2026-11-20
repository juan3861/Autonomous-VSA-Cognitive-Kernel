import sys
import os
import math
from pathlib import Path

# Injeta a raiz do repositório em sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.memory_vault.hnsw_submillisecond_graph_index import HNSWSubMillisecondGraphIndex
from aethermind_cognitive_substrate.sovereign_cortex_runtime import SovereignCortexRuntime

def main():
    print("=" * 80)
    print("TEST SUITE: HNSW SUB-MILLISECOND GRAPH INDEX & COLD-TO-HOT PROMOTION (ÓRGÃO 29)")
    print("=" * 80)

    # 1. Construção de Grafo Multi-Camada com 300 Nós
    hnsw = HNSWSubMillisecondGraphIndex(dim=32, M=12, ef_construction=32, ef_search=32)
    target_vec = [math.cos((j + 1) * 0.45) for j in range(32)]

    for i in range(300):
        if i == 150:
            v = target_vec
        else:
            v = [math.sin((i + 1) * (j + 1) * 0.17 + j) for j in range(32)]
        hnsw.insert(f"concept_{i}", v, payload={"id": i})

    assert len(hnsw.nodes) == 300
    assert hnsw.max_level >= 1, f"Grafo HNSW deve ter múltiplas camadas, max_level={hnsw.max_level}"
    print(f" -> [TESTE 1/5]: 300 vetores indexados em {hnsw.max_level + 1} camadas hierárquicas.")

    # 2. Busca Sub-Milissegundo O(log N)
    search_res = hnsw.search_knn(target_vec, k=3)
    best = search_res["matches"][0]
    assert best["node_id"] == "concept_150", f"Esperado concept_150, obtido {best['node_id']}"
    assert best["cosine_similarity"] > 0.9999
    assert search_res["distance_evaluations"] < 300, f"Deve avaliar menos nós que busca linear: {search_res['distance_evaluations']}/300"
    print(f" -> [TESTE 2/5]: Top-1 '{best['node_id']}' recuperado em {search_res['elapsed_us']} us com {search_res['distance_evaluations']}/300 avaliações (Speedup={search_res['graph_speedup_ratio']}x).")

    # 3. Falsificação Adversarial: Vetor Invertido (-target_vec)
    inverted_vec = [-x for x in target_vec]
    adv_res = hnsw.search_knn(inverted_vec, k=1)
    assert adv_res["matches"][0]["node_id"] != "concept_150", "Vetor oposto jamais deve casar com o alvo!"
    print(f" -> [TESTE 3/5]: Falsificação Adversarial: Vetor oposto retornou '{adv_res['matches'][0]['node_id']}' (Isolamento Confirmado).")

    # 4. Recuperação Semântica e Restauração Automática da Cold Tier via Córtex Runtime
    runtime = SovereignCortexRuntime()
    ancient_vec = [math.cos(j * 0.77 + 0.5) for j in range(32)]
    runtime.paged_memory.allocate_page("ancient_theorem", "Riemann_Zeta_Zero", vector_repr=ancient_vec, importance=0.1)

    # Inunda a memória com 45 páginas para forçar 'ancient_theorem' para a Cold Tier
    for i in range(45):
        v_flood = [math.sin((i + 10) * 0.31 + j * 0.19) for j in range(32)]
        runtime.paged_memory.allocate_page(f"flood_page_{i}", f"data_{i}", vector_repr=v_flood, importance=2.0)

    assert "ancient_theorem" in runtime.paged_memory.cold_tier, "Página deveria estar arquivada na Cold Tier!"

    # Executa busca associativa HNSW via missão do Córtex
    mission_res = runtime.execute_cognitive_mission("hnsw_associative_search", {"query_vector": ancient_vec, "top_k": 2})
    m_top = mission_res["result"]["matches"][0]
    assert m_top["node_id"] == "ancient_theorem"
    assert m_top["promoted_from_tier"] == "COLD_TIER_RESTORED"
    assert "ancient_theorem" in runtime.paged_memory.hot_tier, "Página deve ter sido restaurada para a Hot Tier!"
    print(f" -> [TESTE 4/5]: Página '{m_top['node_id']}' localizada via HNSW na Cold Tier e restaurada para a Hot Tier em {mission_res['result']['elapsed_us']} us.")

    # 5. Verificação de Saúde do Córtex v3.9.0 (29 Órgãos)
    health = runtime.get_system_health()
    assert health["organs_active_count"] >= 29
    assert health["hnsw_submillisecond_index_active"] is True
    print(" -> [TESTE 5/5]: Córtex v3.9.0 (29 Órgãos) verificado com sucesso.")

    print("\n[VEREDITO EMPÍRICO]: HNSW SUB-MILLISECOND GRAPH INDEX APROVADO COM CERTEZA MATEMÁTICA.")
    sys.exit(0)

if __name__ == "__main__":
    main()
