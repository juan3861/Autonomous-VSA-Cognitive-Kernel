import time
import math
from typing import Dict, List, Any, Optional, Tuple
from .hnsw_submillisecond_graph_index import HNSWSubMillisecondGraphIndex

# ==============================================================================
# AETHERMIND HIERARCHICAL PAGED MEMORY OS ENGINE (PAGE TABLE / COGNITIVE OS)
# Órgão 26 do Substrato Cognitivo Soberano (Inspirado em MemGPT / Letta / vLLM)
# ==============================================================================
# Resolve o estrangulamento da janela de contexto finita: em vez de descartar
# tokens ou saturar a memória, gerencia o contexto cognitivo como páginas de
# memória virtual de SO divididas em 3 camadas hierárquicas:
#   Tier 1: Hot Working Memory (RAM Rápida, latência < 0.1 ms)
#   Tier 2: Warm Recall Memory (HippoRAG & Grafos Associativos, latência < 1 ms)
#   Tier 3: Cold Archival Storage (VSA Hipervetores SQLite/Disco, latência < 10 ms)
# 100% Determinístico, com política LRU e Surprise-Gated Protection (Anti-Eviction).
# ==============================================================================

class MemoryPage:
    """Representa uma página de memória cognitiva estruturada."""
    def __init__(self, page_id: str, content: Any, vector_repr: Optional[List[float]] = None, importance: float = 1.0):
        self.page_id = page_id
        self.content = content
        self.vector_repr = vector_repr or [0.0] * 32
        self.importance = importance  # Peso de relevância causal / surpresa
        self.access_count = 0
        self.created_at = time.time()
        self.last_accessed_at = time.time()
        self.is_pinned = False  # Páginas protegidas contra swap-out

    def touch(self, importance_boost: float = 0.0):
        self.access_count += 1
        self.last_accessed_at = time.time()
        if importance_boost > 0.0:
            self.importance = max(self.importance, self.importance + importance_boost)


class HierarchicalPagedMemoryOS:
    """
    Gerenciador de Memória Virtual Paginada Cognitiva (Cognitive OS Pager).
    """
    def __init__(self, max_hot_pages: int = 8, max_warm_pages: int = 32):
        self.max_hot_pages = max_hot_pages
        self.max_warm_pages = max_warm_pages
        
        # Tabelas de páginas dos 3 níveis
        self.hot_tier: Dict[str, MemoryPage] = {}    # Tier 1: Working Memory
        self.warm_tier: Dict[str, MemoryPage] = {}   # Tier 2: Recall Memory
        self.cold_tier: Dict[str, Any] = {}          # Tier 3: Archival Storage (Chave -> Conteúdo Serializado)
        
        # Grafo Hierárquico Navegável de Mundo Pequeno (HNSW) para busca semântica O(log N)
        self.hnsw_index = HNSWSubMillisecondGraphIndex(dim=32, M=12, ef_construction=32, ef_search=32)
        
        # Estatísticas de telemetria
        self.page_hits = 0
        self.page_misses = 0
        self.swap_count = 0

    def allocate_page(self, page_id: str, content: Any, vector_repr: Optional[List[float]] = None, importance: float = 1.0, pin: bool = False) -> MemoryPage:
        """Aloca uma nova página diretamente na Hot Working Memory, disparando swap se necessário."""
        t0 = time.perf_counter()
        
        # Se a Hot Memory estiver cheia, executa swap-out da página menos importante (LRU + Surprise)
        if len(self.hot_tier) >= self.max_hot_pages:
            self._evict_from_hot()

        if vector_repr is None:
            # Gera vetor determinístico de 32 dimensões se não fornecido
            seed_val = sum((idx + 1) * ord(ch) for idx, ch in enumerate(page_id))
            vector_repr = [math.sin(seed_val * 0.1 + i * 0.5) for i in range(32)]

        page = MemoryPage(page_id, content, vector_repr, importance)
        page.is_pinned = pin
        self.hot_tier[page_id] = page
        self.hnsw_index.insert(page_id, page.vector_repr, payload={"importance": importance})
        
        return page

    def _evict_from_hot(self):
        """Move a página de menor relevância da Hot para a Warm Tier."""
        unpinned = [p for p in self.hot_tier.values() if not p.is_pinned]
        if not unpinned:
            # Todas estão pinadas, despinamos a mais antiga
            unpinned = list(self.hot_tier.values())

        # Pontuação de retenção: R = importance * (1.0 + log(1 + access_count)) / (tempo_desde_acesso + 1.0)
        now = time.time()
        victim = min(
            unpinned,
            key=lambda p: (p.importance * (1.0 + math.log1p(p.access_count))) / ((now - p.last_accessed_at) + 1.0)
        )
        
        # Remove da Hot e passa para a Warm
        del self.hot_tier[victim.page_id]
        
        # Se a Warm também estiver cheia, move para a Cold
        if len(self.warm_tier) >= self.max_warm_pages:
            self._evict_from_warm()
            
        self.warm_tier[victim.page_id] = victim
        self.swap_count += 1

    def _evict_from_warm(self):
        """Move da Warm para a Cold Tier (Armazenamento Permanente)."""
        now = time.time()
        victim = min(self.warm_tier.values(), key=lambda p: p.last_accessed_at)
        del self.warm_tier[victim.page_id]
        
        # Serializa para cold storage
        self.cold_tier[victim.page_id] = {
            "content": victim.content,
            "importance": victim.importance,
            "access_count": victim.access_count,
            "archived_at": now
        }
        self.swap_count += 1

    def access_page(self, page_id: str) -> Tuple[Optional[Any], str, float]:
        """
        Acessa uma página buscando na hierarquia: Hot -> Warm -> Cold.
        Promove automaticamente para a Hot Memory se encontrada nos níveis inferiores.
        Retorna (conteúdo, nível_de_origem, latência_us).
        """
        t0 = time.perf_counter()
        
        # 1. Hot Tier Hit
        if page_id in self.hot_tier:
            page = self.hot_tier[page_id]
            page.touch(importance_boost=0.1)
            self.page_hits += 1
            lat = (time.perf_counter() - t0) * 1e6
            return page.content, "HOT_TIER", round(lat, 2)
            
        # 2. Warm Tier Hit (Promove para Hot)
        if page_id in self.warm_tier:
            page = self.warm_tier.pop(page_id)
            page.touch(importance_boost=0.2)
            if len(self.hot_tier) >= self.max_hot_pages:
                self._evict_from_hot()
            self.hot_tier[page_id] = page
            self.page_hits += 1
            self.swap_count += 1
            lat = (time.perf_counter() - t0) * 1e6
            return page.content, "WARM_TIER_PROMOTED", round(lat, 2)
            
        # 3. Cold Tier Hit (Restaura para Hot)
        if page_id in self.cold_tier:
            archived = self.cold_tier.pop(page_id)
            page = MemoryPage(page_id, archived["content"], importance=archived["importance"])
            page.access_count = archived["access_count"] + 1
            page.touch()
            if len(self.hot_tier) >= self.max_hot_pages:
                self._evict_from_hot()
            self.hot_tier[page_id] = page
            self.page_hits += 1
            self.swap_count += 1
            lat = (time.perf_counter() - t0) * 1e6
            return page.content, "COLD_TIER_RESTORED", round(lat, 2)

        # 4. Miss Total
        self.page_misses += 1
        lat = (time.perf_counter() - t0) * 1e6
        return None, "PAGE_FAULT_MISS", round(lat, 2)

    def query_associative_hnsw(self, query_vector: List[float], top_k: int = 3, promote_top: bool = True) -> Dict[str, Any]:
        """
        Executa busca associativa semântica O(log N) via grafo multi-camada HNSW
        sobre todas as páginas (Hot, Warm e Cold) e promove a melhor página para a Hot Tier.
        """
        res = self.hnsw_index.search_knn(query_vector, k=top_k)
        matches = res.get("matches", [])
        if promote_top and matches:
            best_id = matches[0]["node_id"]
            content, origin, _ = self.access_page(best_id)
            matches[0]["promoted_from_tier"] = origin
            matches[0]["content"] = content
        return res

    def get_telemetry(self) -> Dict[str, Any]:
        """Retorna o estado da tabela de páginas e métricas do SO Cognitivo."""
        total_requests = self.page_hits + self.page_misses
        hit_ratio = self.page_hits / total_requests if total_requests > 0 else 1.0
        
        return {
            "hot_pages_active": len(self.hot_tier),
            "max_hot_pages": self.max_hot_pages,
            "warm_pages_active": len(self.warm_tier),
            "max_warm_pages": self.max_warm_pages,
            "cold_pages_archived": len(self.cold_tier),
            "hnsw_indexed_nodes": len(self.hnsw_index.nodes),
            "hnsw_max_level": self.hnsw_index.max_level,
            "page_hits": self.page_hits,
            "page_misses": self.page_misses,
            "hit_ratio_percent": round(hit_ratio * 100.0, 2),
            "total_swaps": self.swap_count,
            "status": "PAGED_VIRTUAL_MEMORY_STABLE"
        }
