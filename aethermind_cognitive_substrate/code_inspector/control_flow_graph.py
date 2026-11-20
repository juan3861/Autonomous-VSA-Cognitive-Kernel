"""Control Flow Graph (CFG) & Dominance Engine (AetherMind Cognitive Substrate).

Área 02: Engenharia de Código, Otimização de Compilador e Análise de Grafos.
Constrói o Grafo de Fluxo de Controle (CFG) a partir do AST de uma função,
identifica blocos básicos, arestas de ramificação, loops e código morto inalcançável.
"""
from __future__ import annotations

import ast
import time
from typing import Dict, Any, List, Set, Optional, Tuple
import networkx as nx


class BasicBlock:
    def __init__(self, block_id: int, label: str):
        self.block_id = block_id
        self.label = label
        self.statements: List[str] = []

    def __repr__(self):
        return f"Block_{self.block_id}({self.label})"


class ControlFlowGraphBuilder:
    """Construtor de CFG em nível de Blocos Básicos."""

    def __init__(self):
        self.cfg = nx.DiGraph()
        self.blocks: Dict[int, BasicBlock] = {}
        self._counter = 0

    def _new_block(self, label: str) -> int:
        bid = self._counter
        self._counter += 1
        block = BasicBlock(bid, label)
        self.blocks[bid] = block
        self.cfg.add_node(bid, block=block)
        return bid

    def build_cfg_for_function(self, func_code: str) -> Dict[str, Any]:
        """Gera o CFG para a primeira função encontrada no código."""
        start = time.perf_counter()
        tree = ast.parse(func_code)

        func_node = None
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_node = node
                break

        if not func_node:
            raise ValueError("Nenhuma definição de função encontrada no código.")

        self.cfg.clear()
        self.blocks.clear()
        self._counter = 0

        entry_id = self._new_block("ENTRY")
        exit_id = self._new_block("EXIT")

        # Processamento sequencial simples de declarações
        current_id = entry_id
        for stmt in func_node.body:
            stmt_label = type(stmt).__name__
            if isinstance(stmt, ast.If):
                # Cria bloco de condição
                cond_id = self._new_block(f"IF_COND (line {stmt.lineno})")
                self.cfg.add_edge(current_id, cond_id)

                then_id = self._new_block("THEN_BRANCH")
                else_id = self._new_block("ELSE_BRANCH") if stmt.orelse else None
                merge_id = self._new_block("IF_MERGE")

                self.cfg.add_edge(cond_id, then_id, label="True")
                self.cfg.add_edge(then_id, merge_id)

                if else_id is not None:
                    self.cfg.add_edge(cond_id, else_id, label="False")
                    self.cfg.add_edge(else_id, merge_id)
                else:
                    self.cfg.add_edge(cond_id, merge_id, label="False")

                current_id = merge_id
            elif isinstance(stmt, ast.Return):
                ret_id = self._new_block(f"RETURN (line {stmt.lineno})")
                if current_id is not None:
                    self.cfg.add_edge(current_id, ret_id)
                self.cfg.add_edge(ret_id, exit_id)
                current_id = None  # Execução após return incondicional termina este ramo
            else:
                stmt_id = self._new_block(f"{stmt_label} (line {stmt.lineno})")
                if current_id is not None:
                    self.cfg.add_edge(current_id, stmt_id)
                current_id = stmt_id

        if current_id is not None and current_id != exit_id:
            if not nx.has_path(self.cfg, current_id, exit_id):
                self.cfg.add_edge(current_id, exit_id)

        # Análise de Código Morto (Inalcançável a partir de ENTRY)
        reachable_nodes = nx.descendants(self.cfg, entry_id) | {entry_id}
        unreachable_nodes = set(self.cfg.nodes()) - reachable_nodes

        # Análise de Ciclos no Grafo (Loops)
        has_cycles = not nx.is_directed_acyclic_graph(self.cfg)
        cycles = list(nx.simple_cycles(self.cfg)) if has_cycles else []

        elapsed_ms = (time.perf_counter() - start) * 1000.0

        return {
            "function_name": func_node.name,
            "total_blocks": len(self.blocks),
            "entry_block_id": entry_id,
            "exit_block_id": exit_id,
            "edges_count": self.cfg.number_of_edges(),
            "has_loops": has_cycles,
            "loops_count": len(cycles),
            "unreachable_blocks_count": len(unreachable_nodes),
            "unreachable_blocks": [str(self.blocks[bid]) for bid in unreachable_nodes],
            "elapsed_ms": round(elapsed_ms, 3)
        }
