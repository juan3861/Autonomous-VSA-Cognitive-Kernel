"""Perception-to-VSA Semantic Bridge (AST/CFG & Closed-Loop Desktop Vision -> 10,240-bit Bus).

Encodes deterministic structural code metrics (AST symbols, cyclomatic complexity, CFG
basic blocks/edges) and Win32 closed-loop desktop geometry onto the 10,240-bit
`VSAHyperdimensionalBus` so downstream planning and formal verification organs can query
perceptual events directly via holographic similarity without brittle string glue.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..code_inspector.ast_code_analyzer import ASTCodeAnalyzer
from ..code_inspector.control_flow_graph import ControlFlowGraphBuilder
from ..memory_vault.vsa_semantic_bus import VSAEvent, VSAHyperdimensionalBus
from .closed_loop_vision_eye import ClosedLoopVisionEye


class PerceptionVSABridge:
    """Bridges structural code inspection and desktop window vision onto 10,240-bit VSA events."""

    def __init__(self, bus: Optional[VSAHyperdimensionalBus] = None):
        self.bus = bus or VSAHyperdimensionalBus(dimension=10240, seed=1337)
        self.ast_analyzer = ASTCodeAnalyzer()
        self.cfg_builder = ControlFlowGraphBuilder()
        self.vision_eye = ClosedLoopVisionEye()

    def encode_code_ast(
        self,
        source_code: str,
        organ_id: str = "ast_analyzer",
        include_cfg: bool = True,
    ) -> Dict[str, Any]:
        """Inspect Python source via AST/CFG and publish a 10,240-bit structural event."""
        ast_res = self.ast_analyzer.analyze_source(source_code)
        cfg_summary: Dict[str, Any] = {}
        if include_cfg and ast_res.get("is_valid_syntax") and ast_res.get("symbols", {}).get("functions"):
            try:
                cfg_res = self.cfg_builder.build_cfg_for_function(source_code)
                cfg_summary = {
                    "cfg_function": cfg_res.get("function_name"),
                    "cfg_blocks": cfg_res.get("total_blocks", 0),
                    "cfg_edges": cfg_res.get("edges_count", 0),
                    "cfg_unreachable": cfg_res.get("unreachable_blocks_count", 0),
                }
            except Exception:
                cfg_summary = {}

        syms = ast_res.get("symbols", {})
        payload: Dict[str, Any] = {
            "is_valid_syntax": bool(ast_res.get("is_valid_syntax", False)),
            "security_clean": bool(ast_res.get("security_clean", False)),
            "cyclomatic_complexity": int(ast_res.get("cyclomatic_complexity", 1)),
            "functions_count": len(syms.get("functions", [])),
            "classes_count": len(syms.get("classes", [])),
            "violations_count": len(ast_res.get("violations", [])),
            "lines_of_code": int(ast_res.get("lines_of_code", 0)),
        }
        payload.update(cfg_summary)

        evt: VSAEvent = self.bus.publish(
            topic="perception.code_ast",
            payload=payload,
            organ_id=organ_id,
            confidence=1.0 if payload["security_clean"] and payload["is_valid_syntax"] else 0.2,
        )
        return {
            "event": evt,
            "ast_telemetry": ast_res,
            "cfg_telemetry": cfg_summary,
            "payload": payload,
        }

    def encode_desktop_state(
        self,
        query_title: Optional[str] = None,
        max_windows: int = 25,
        organ_id: str = "vision_eye",
    ) -> Dict[str, Any]:
        """Inspect live Win32 desktop windows closed-loop and publish onto the 10,240-bit bus."""
        if query_title:
            vis_res = self.vision_eye.verify_window_exists(query_title)
            matched = vis_res.get("matched_windows", [])
            top_w = matched[0] if matched else {}
            payload: Dict[str, Any] = {
                "query_title": query_title,
                "exists": bool(vis_res.get("exists", False)),
                "matches_count": int(vis_res.get("matches_count", 0)),
                "top_width": int(top_w.get("width", 0)),
                "top_height": int(top_w.get("height", 0)),
            }
            conf = 1.0 if payload["exists"] else 0.5
        else:
            vis_res = self.vision_eye.inspect_visible_windows(max_windows=max_windows)
            windows: List[Dict[str, Any]] = vis_res.get("windows", [])
            top_w = windows[0] if windows else {}
            payload = {
                "status": str(vis_res.get("status", "UNKNOWN")),
                "total_visible_windows": int(vis_res.get("total_visible_windows", len(windows))),
                "top_width": int(top_w.get("width", 0)),
                "top_height": int(top_w.get("height", 0)),
            }
            conf = 1.0 if vis_res.get("status") == "SUCCESS" else 0.5

        evt: VSAEvent = self.bus.publish(
            topic="perception.desktop_vision",
            payload=payload,
            organ_id=organ_id,
            confidence=conf,
        )
        return {
            "event": evt,
            "vision_telemetry": vis_res,
            "payload": payload,
        }
