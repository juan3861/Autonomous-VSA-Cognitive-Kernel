"""Lock-Free Single-Producer Single-Consumer (SPSC) Ring Buffer (AetherMind Cognitive Substrate).

Áreas 01 & 13: Reflexo em Nanissegundos, IPC Bare-Metal e Fila sem Bloqueio.
Implementa a fila circular clássica de SPSC (estilo rigtorp/SPSCQueue):
- Capacidade em potência de 2 para mascaramento de bits em nível de clock (index & (capacity - 1))
- Sem locks, sem mutexes, sem alocação de heap no loop crítico
- Tolerância a alta concorrência entre threads de reflexo e despacho.
"""
from __future__ import annotations

import time
from typing import Dict, Any, List, Optional, Generic, TypeVar

T = TypeVar("T")


class LockFreeSPSCRingBuffer(Generic[T]):
    """Buffer Circular SPSC Lock-Free de Baixa Latência."""

    def __init__(self, capacity: int = 1024):
        # Garante capacidade em potência de 2
        power = 1
        while power < capacity:
            power *= 2
        self.capacity = power
        self.mask = self.capacity - 1

        self.buffer: List[Optional[T]] = [None] * self.capacity
        self.head = 0  # Índice de escrita (apenas o Producer altera)
        self.tail = 0  # Índice de leitura (apenas o Consumer altera)

    def size(self) -> int:
        """Número atual de elementos no buffer."""
        return self.head - self.tail

    def is_empty(self) -> bool:
        return self.head == self.tail

    def is_full(self) -> bool:
        return (self.head - self.tail) >= self.capacity

    def push(self, item: T) -> bool:
        """Operação Wait-Free de escrita pelo Produtor. Retorna True se gravou, False se cheio."""
        if (self.head - self.tail) >= self.capacity:
            return False  # Buffer cheio

        idx = self.head & self.mask
        self.buffer[idx] = item
        self.head += 1
        return True

    def pop(self) -> Optional[T]:
        """Operação Wait-Free de leitura pelo Consumidor. Retorna o item ou None se vazio."""
        if self.head == self.tail:
            return None  # Buffer vazio

        idx = self.tail & self.mask
        item = self.buffer[idx]
        self.buffer[idx] = None  # Libera referência
        self.tail += 1
        return item

    def drain_all(self) -> List[T]:
        """Esvazia todos os itens pendentes em lote com alta eficiência."""
        items = []
        while True:
            val = self.pop()
            if val is None:
                break
            items.append(val)
        return items
