"""Deterministic AST Code Analyzer & Safety Verifier (AetherMind Cognitive Substrate).

Área 02: Engenharia de Código, Sintaxe, Patches e Análise de Segurança.
Analisa código Python determinística e formalmente via Abstract Syntax Tree (AST):
audita chamadas proibidas, calcula complexidade ciclomática, extrai símbolos e
detecta anomalias de escopo sem precisar de LLM.
"""
from __future__ import annotations

import ast
import time
from typing import Dict, Any, List, Set, Optional, Tuple


class CodeSecurityVisitor(ast.NodeVisitor):
    """Audita a árvore sintática em busca de operações perigosas e chamadas inseguras."""

    def __init__(self, blocked_modules: Optional[Set[str]] = None, blocked_calls: Optional[Set[str]] = None):
        self.blocked_modules = blocked_modules or {"os.system", "subprocess.Popen", "shutil.rmtree"}
        self.blocked_calls = blocked_calls or {"eval", "exec", "__import__"}
        self.violations: List[Dict[str, Any]] = []
        self.functions_defined: List[str] = []
        self.classes_defined: List[str] = []
        self.imports: List[str] = []
        self.decision_points: int = 0

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(alias.name)
            if alias.name in self.blocked_modules:
                self.violations.append({
                    "type": "BLOCKED_IMPORT",
                    "target": alias.name,
                    "line": node.lineno
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        mod = node.module or ""
        self.imports.append(mod)
        if mod in self.blocked_modules:
            self.violations.append({
                "type": "BLOCKED_IMPORT_FROM",
                "target": mod,
                "line": node.lineno
            })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Checagem de chamadas diretas como eval(), exec()
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
            if func_name in self.blocked_calls:
                self.violations.append({
                    "type": "BLOCKED_CALL",
                    "target": func_name,
                    "line": node.lineno
                })
        # Checagem de chamadas de atributo como os.system()
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                full_call = f"{node.func.value.id}.{node.func.attr}"
                if full_call in self.blocked_modules:
                    self.violations.append({
                        "type": "BLOCKED_CALL_ATTRIBUTE",
                        "target": full_call,
                        "line": node.lineno
                    })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.functions_defined.append(node.name)
        self.decision_points += 1
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        self.classes_defined.append(node.name)
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self.decision_points += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For):
        self.decision_points += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While):
        self.decision_points += 1
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.decision_points += 1
        self.generic_visit(node)


class ASTCodeAnalyzer:
    """Analisador estático determinístico de código Python."""

    def __init__(self):
        pass

    def analyze_source(self, code_str: str) -> Dict[str, Any]:
        """Realiza análise sintática completa, complexidade ciclomática e auditoria de segurança."""
        start = time.perf_counter()

        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            return {
                "is_valid_syntax": False,
                "syntax_error": {
                    "msg": e.msg,
                    "line": e.lineno,
                    "offset": e.offset,
                    "text": e.text
                },
                "elapsed_ms": round(elapsed_ms, 3)
            }

        visitor = CodeSecurityVisitor()
        visitor.visit(tree)

        # Complexidade Ciclomática aproximada M = E - N + 2P (ou pontos de decisão + 1)
        cyclomatic_complexity = visitor.decision_points + 1

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {
            "is_valid_syntax": True,
            "security_clean": len(visitor.violations) == 0,
            "violations": visitor.violations,
            "symbols": {
                "functions": visitor.functions_defined,
                "classes": visitor.classes_defined,
                "imports": visitor.imports
            },
            "cyclomatic_complexity": cyclomatic_complexity,
            "lines_of_code": len(code_str.splitlines()),
            "elapsed_ms": round(elapsed_ms, 3)
        }
