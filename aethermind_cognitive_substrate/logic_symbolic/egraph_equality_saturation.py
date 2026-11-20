"""E-Graph Equality Saturation & Congruence Closure Algebraic Optimizer (egg / egglog Inspiration).

Organ 38 do Substrato Cognitivo Não-LLM (AetherCOS v4.3).
Resolve o Problema de Ordenação de Fases (Phase-Ordering Problem) da otimização simbólica:
- E-Nodes & E-Classes: Armazena simultaneamente milhões de programas/expressões
  algebricamente equivalentes sem destruição prematura da árvore original.
- Union-Find (Tarjan Disjoint-Set) com Compressão de Caminho + Fecho de Congruência:
    Se eclass(a) == eclass(b), então eclass(op(a)) == eclass(op(b)).
- Saturação de Igualdade (Equality Saturation):
    Aplica regras algébricas de reescrita não-destrutivas (identidades aditivas/multiplicativas,
    redução de força de operadores `x * 2 <-> x << 1`, cancelamento `(x * y) / y -> x`,
    idempotência e aniquilação `x - x -> 0`, `x * 0 -> 0`) até o ponto fixo.
- Extração de Custo Mínimo (Bottom-Up Dynamic Programming):
    Extrai a árvore sintática abstrata (AST) globalmente ótima segundo um modelo de
    custo de ciclos de hardware (ex.: shift/add = 1 ciclo, mul = 4 ciclos, div = 15 ciclos).
"""
from __future__ import annotations

import ast
import time
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Set, Optional


@dataclass(frozen=True)
class ENode:
    """Nó de operador canônico apontando para IDs de classes de equivalência filhas."""
    op: str
    children: Tuple[int, ...] = ()

    def canonicalize(self, find_fn) -> "ENode":
        return ENode(self.op, tuple(find_fn(c) for c in self.children))


class EGraphEqualitySaturationEngine:
    """
    Motor de Saturação de Igualdade em E-Graphs com Fecho de Congruência
    e Extração de Custo de Ciclos de Silício.
    """

    DEFAULT_OP_COSTS = {
        "/": 15,
        "*": 4,
        "<<": 1,
        ">>": 1,
        "+": 1,
        "-": 1,
        "&": 1,
        "^": 1,
        "|": 1,
    }

    def __init__(self):
        self.parent: List[int] = []
        self.memo: Dict[ENode, int] = {}
        self.eclasses: Dict[int, Set[ENode]] = {}

    def reset(self) -> None:
        self.parent.clear()
        self.memo.clear()
        self.eclasses.clear()

    def find(self, eclass_id: int) -> int:
        """Union-Find com compressão de caminho."""
        root = eclass_id
        while self.parent[root] != root:
            root = self.parent[root]
        curr = eclass_id
        while curr != root:
            nxt = self.parent[curr]
            self.parent[curr] = root
            curr = nxt
        return root

    def add_enode(self, node: ENode) -> int:
        """Adiciona um ENode canônico ao E-Graph ou retorna sua E-Class existente."""
        canon = node.canonicalize(self.find)
        if canon in self.memo:
            return self.find(self.memo[canon])

        new_id = len(self.parent)
        self.parent.append(new_id)
        self.memo[canon] = new_id
        self.eclasses[new_id] = {canon}
        return new_id

    def merge(self, id1: int, id2: int) -> int:
        """Funde duas E-Classes no Union-Find."""
        r1 = self.find(id1)
        r2 = self.find(id2)
        if r1 == r2:
            return r1
        self.parent[r2] = r1
        self.eclasses[r1].update(self.eclasses.pop(r2, set()))
        return r1

    def rebuild(self) -> None:
        """Restaura a invariante do Fecho de Congruência após fusões de E-Classes."""
        changed = True
        while changed:
            changed = False
            new_memo: Dict[ENode, int] = {}
            new_classes: Dict[int, Set[ENode]] = {}

            for cid, nodes in list(self.eclasses.items()):
                root_cid = self.find(cid)
                if root_cid not in new_classes:
                    new_classes[root_cid] = set()
                for n in nodes:
                    canon = n.canonicalize(self.find)
                    new_classes[root_cid].add(canon)
                    if canon in new_memo:
                        prev_cid = self.find(new_memo[canon])
                        if prev_cid != root_cid:
                            self.merge(prev_cid, root_cid)
                            changed = True
                    else:
                        new_memo[canon] = root_cid

            self.memo = new_memo
            # Reagrupa por raiz atualizada
            final_classes: Dict[int, Set[ENode]] = {}
            for cid, nodes in new_classes.items():
                r = self.find(cid)
                final_classes.setdefault(r, set()).update(nodes)
            self.eclasses = final_classes

    def _add_ast_node(self, node: ast.AST) -> int:
        if isinstance(node, ast.Constant):
            return self.add_enode(ENode(str(node.value)))
        if isinstance(node, ast.Name):
            return self.add_enode(ENode(node.id))
        if isinstance(node, ast.BinOp):
            left_id = self._add_ast_node(node.left)
            right_id = self._add_ast_node(node.right)
            op_map = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/",
                ast.FloorDiv: "/",
                ast.LShift: "<<",
                ast.RShift: ">>",
                ast.BitAnd: "&",
                ast.BitXor: "^",
                ast.BitOr: "|",
            }
            op_str = op_map.get(type(node.op), "?")
            return self.add_enode(ENode(op_str, (left_id, right_id)))
        raise ValueError(f"Nó AST não suportado no E-Graph: {type(node)}")

    def add_expression(self, expr_str: str) -> int:
        tree = ast.parse(expr_str.strip(), mode="eval")
        return self._add_ast_node(tree.body)

    def _has_const(self, cid: int, val: str) -> bool:
        root = self.find(cid)
        return ENode(val, ()) in self.eclasses.get(root, set())

    def apply_rewrite_iteration(self) -> int:
        """
        Aplica um passe completo de regras de reescrita algébrica não-destrutiva:
        1. Comutatividade: a + b == b + a, a * b == b * a
        2. Redução de força (Strength Reduction): a * 2 <-> a << 1, a * 4 <-> a << 2
        3. Cancelamento de Divisão (Phase-Ordering Classic): (a * b) / b -> a
        4. Identidades Aditivas e Multiplicativas: a + 0 -> a, a - 0 -> a, a * 1 -> a, a / 1 -> a
        5. Aniquilação: a * 0 -> 0, a - a -> 0, a ^ a -> 0
        6. Duplicação: a + a <-> a * 2
        """
        merges_to_do: List[Tuple[int, int]] = []

        # Snapshot das classes e nós atuais
        snapshot = [(cid, list(nodes)) for cid, nodes in self.eclasses.items()]

        for cid, nodes in snapshot:
            root_c = self.find(cid)
            for n in nodes:
                op = n.op
                ch = n.children
                if len(ch) != 2:
                    continue
                l, r = self.find(ch[0]), self.find(ch[1])

                # 1. Comutatividade para + e *
                if op in ("+", "*"):
                    comm_id = self.add_enode(ENode(op, (r, l)))
                    merges_to_do.append((root_c, comm_id))

                # 2. a + 0 -> a | 0 + a -> a
                if op == "+" and self._has_const(r, "0"):
                    merges_to_do.append((root_c, l))
                if op == "-" and self._has_const(r, "0"):
                    merges_to_do.append((root_c, l))

                # 3. a - a -> 0 | a ^ a -> 0
                if op in ("-", "^") and l == r:
                    zero_id = self.add_enode(ENode("0"))
                    merges_to_do.append((root_c, zero_id))

                # 4. a + a <-> a * 2
                if op == "+" and l == r:
                    two_id = self.add_enode(ENode("2"))
                    mul2_id = self.add_enode(ENode("*", (l, two_id)))
                    merges_to_do.append((root_c, mul2_id))

                # 5. a * 1 -> a | a * 0 -> 0
                if op == "*":
                    if self._has_const(r, "1"):
                        merges_to_do.append((root_c, l))
                    if self._has_const(r, "0"):
                        zero_id = self.add_enode(ENode("0"))
                        merges_to_do.append((root_c, zero_id))
                    # Strength reduction: a * 2 <-> a << 1
                    if self._has_const(r, "2"):
                        one_id = self.add_enode(ENode("1"))
                        shl_id = self.add_enode(ENode("<<", (l, one_id)))
                        merges_to_do.append((root_c, shl_id))
                    if self._has_const(r, "4"):
                        two_id = self.add_enode(ENode("2"))
                        shl2_id = self.add_enode(ENode("<<", (l, two_id)))
                        merges_to_do.append((root_c, shl2_id))

                # 6. Divisão: a / 1 -> a, a / a -> 1 (se a != 0), e (x * y) / z onde y == z -> x
                if op == "/":
                    if self._has_const(r, "1"):
                        merges_to_do.append((root_c, l))
                    # Inspeciona todos os nós de multiplicação dentro da E-Class numeradora `l`
                    for num_node in list(self.eclasses.get(l, set())):
                        if num_node.op == "*" and len(num_node.children) == 2:
                            nl, nr = self.find(num_node.children[0]), self.find(num_node.children[1])
                            if nr == r:
                                merges_to_do.append((root_c, nl))
                            elif nl == r:
                                merges_to_do.append((root_c, nr))

        merged_count = 0
        for a, b in merges_to_do:
            if self.find(a) != self.find(b):
                self.merge(a, b)
                merged_count += 1

        if merged_count > 0:
            self.rebuild()

        return merged_count

    def extract_optimal(self, root_eclass: int) -> Tuple[int, str]:
        """
        Extrai a expressão equivalente de menor custo de ciclos de hardware
        usando programação dinâmica bottom-up sobre o E-Graph saturado.
        """
        root = self.find(root_eclass)
        best_cost: Dict[int, int] = {}
        best_expr: Dict[int, str] = {}

        changed = True
        while changed:
            changed = False
            for cid, nodes in self.eclasses.items():
                r_cid = self.find(cid)
                for n in nodes:
                    if not n.children:
                        cost = 1
                        expr = n.op
                    else:
                        if not all(self.find(c) in best_cost for c in n.children):
                            continue
                        op_cost = self.DEFAULT_OP_COSTS.get(n.op, 2)
                        c0 = self.find(n.children[0])
                        c1 = self.find(n.children[1])
                        cost = op_cost + best_cost[c0] + best_cost[c1]
                        e0 = best_expr[c0]
                        e1 = best_expr[c1]
                        if " " in e0:
                            e0 = f"({e0})"
                        if " " in e1:
                            e1 = f"({e1})"
                        expr = f"{e0} {n.op} {e1}"

                    if r_cid not in best_cost or cost < best_cost[r_cid]:
                        best_cost[r_cid] = cost
                        best_expr[r_cid] = expr
                        changed = True

        return best_cost.get(root, 999), best_expr.get(root, "?")

    def saturate_and_optimize(self, expr_str: str, max_iters: int = 8) -> Dict[str, Any]:
        """
        Executa a Saturação de Igualdade completa em `expr_str` e extrai o programa ótimo.
        """
        t0 = time.perf_counter()
        self.reset()
        root_id = self.add_expression(expr_str)
        initial_cost, _ = self.extract_optimal(root_id)

        iters_run = 0
        for _ in range(max_iters):
            iters_run += 1
            merges = self.apply_rewrite_iteration()
            if merges == 0:
                break

        final_cost, optimal_expr = self.extract_optimal(root_id)
        total_enodes = sum(len(ns) for ns in self.eclasses.values())
        elapsed_us = (time.perf_counter() - t0) * 1e6

        return {
            "status": "EGRAPH_EQUALITY_SATURATED",
            "input_expression": expr_str,
            "optimal_expression": optimal_expr,
            "initial_hardware_cost": initial_cost,
            "optimal_hardware_cost": final_cost,
            "cost_reduction_ratio": round(initial_cost / max(1, final_cost), 2),
            "saturation_iterations": iters_run,
            "eclasses_count": len(self.eclasses),
            "enodes_count": total_enodes,
            "elapsed_us": round(elapsed_us, 2)
        }
