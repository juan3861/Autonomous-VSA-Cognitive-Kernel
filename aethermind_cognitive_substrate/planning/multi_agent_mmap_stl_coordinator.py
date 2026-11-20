"""Multi-Agent Lock-Free Shared Memory (mmap) + Formal STL Temporal Logic Swarm Coordinator.

Organ 52 do Substrato Cognitivo Não-LLM (AetherCOS v5.1).
Funde os Órgãos 48 e 49 em um coordenador multi-agente lock-free de alta frequência:
- Cada worker (in-process ou subprocesso OS real) escreve frames numéricos [rho_local, drift, latency_ms, ...]
  em um anel SPSC `SharedMemoryMMapSPSCBridge` zero-copy com validação CRC32;
- O coordenador lê os fluxos em rajada lock-free e aciona `STLTemporalLogicMonitor` para auditar
  invariantes temporais em tempo real:
    G(metric_t <= safety_ceiling)  e  G((metric_t > trigger) => F_[0, H](metric_t <= recovery))
- Detecta violações temporais individuais por worker ou sistêmicas (swarms com deriva/contenção)
  antes que ocorram falhas catastróficas.
"""
from __future__ import annotations

import os
import tempfile
import time
from typing import Dict, Any, List, Optional
import numpy as np

from aethermind_cognitive_substrate.physical_bridge.shared_memory_mmap_ipc import (
    SharedMemoryMMapSPSCBridge,
)
from aethermind_cognitive_substrate.metacognition.ltl_temporal_logic_monitor import (
    STLTemporalLogicMonitor,
)


class MultiAgentMMapSTLCoordinator:
    """
    Coordenador Multi-Agente Lock-Free que agrega telemetria de N canais `mmap` SPSC
    e certifica robustez quantitativa STL global e por agente.
    """

    def __init__(self, slot_capacity: int = 128):
        self.slot_capacity = int(slot_capacity)
        self.stl_monitor = STLTemporalLogicMonitor()

    def coordinate_worker_traces(
        self,
        worker_traces: Dict[str, List[List[float]]] | None = None,
        safety_ceiling: float = 0.95,
        trigger_threshold: float = 0.80,
        recovery_target: float = 0.65,
        response_deadline_steps: int = 4,
    ) -> Dict[str, Any]:
        """
        Orquestra múltiplos workers escrevendo via canais `SharedMemoryMMapSPSCBridge` isolados,
        drena todos os frames com verificação CRC32 e avalia garantias STL formais por agente e global.
        """
        t0 = time.perf_counter()
        if worker_traces is None:
            worker_traces = {
                "worker_planner": [[0.42], [0.58], [0.84], [0.69], [0.51], [0.44]],
                "worker_physics": [[0.35], [0.49], [0.62], [0.58], [0.46], [0.39]],
                "worker_memory":  [[0.40], [0.76], [0.88], [0.74], [0.60], [0.48]],
            }

        per_worker_reports: Dict[str, Dict[str, Any]] = {}
        global_max_series: List[float] = []
        total_frames_pushed = 0
        total_frames_popped = 0

        tmp_dir = tempfile.mkdtemp(prefix="aethermind_swarm_mmap_")
        bridges: List[SharedMemoryMMapSPSCBridge] = []

        try:
            # 1. Aloca um anel SPSC mmap dedicado por agente e publica os frames
            agent_bridges: Dict[str, SharedMemoryMMapSPSCBridge] = {}
            for idx, (agent_id, frames) in enumerate(worker_traces.items()):
                backing = os.path.join(tmp_dir, f"{agent_id}_{idx}.mmap")
                bridge = SharedMemoryMMapSPSCBridge(
                    capacity_slots=max(self.slot_capacity, len(frames) + 8),
                    backing_path=backing,
                    create=True,
                )
                bridges.append(bridge)
                agent_bridges[agent_id] = bridge

                for frame in frames:
                    if bridge.push_frame(frame):
                        total_frames_pushed += 1

            # 2. Coordenador lê em rajada com integridade CRC32 e avalia invariantes STL
            aligned_scalars: List[List[float]] = []
            for agent_id, bridge in agent_bridges.items():
                scalars: List[float] = []
                while True:
                    rec = bridge.pop_frame()
                    if rec is None:
                        break
                    total_frames_popped += 1
                    scalars.append(float(rec["values"][0]))

                stl_res = self.stl_monitor.verify_response_guarantee(
                    trace=scalars,
                    safety_ceiling=safety_ceiling,
                    trigger_threshold=trigger_threshold,
                    recovery_target=recovery_target,
                    response_deadline_steps=response_deadline_steps,
                )
                per_worker_reports[agent_id] = {
                    "frames_received": len(scalars),
                    "peak_metric": round(max(scalars), 5) if scalars else 0.0,
                    "overall_stl_robustness": stl_res["overall_stl_robustness"],
                    "safety_robustness": stl_res["safety_invariance_robustness"],
                    "response_robustness": stl_res["bounded_response_robustness"],
                    "contract_satisfied": stl_res["satisfied"],
                }
                aligned_scalars.append(scalars)

            # 3. Agregação STL Sistêmica: envelope de pico por instante t entre todos os workers
            if aligned_scalars:
                max_len = max(len(s) for s in aligned_scalars)
                for t_idx in range(max_len):
                    step_vals = [s[t_idx] for s in aligned_scalars if t_idx < len(s)]
                    global_max_series.append(max(step_vals))

            global_stl = self.stl_monitor.verify_response_guarantee(
                trace=global_max_series,
                safety_ceiling=safety_ceiling,
                trigger_threshold=trigger_threshold,
                recovery_target=recovery_target,
                response_deadline_steps=response_deadline_steps,
            )
        finally:
            for b in bridges:
                b.close(unlink=True)
            try:
                os.rmdir(tmp_dir)
            except OSError:
                pass

        all_satisfied = all(r["contract_satisfied"] for r in per_worker_reports.values()) and global_stl["satisfied"]
        violating_agents = [aid for aid, r in per_worker_reports.items() if not r["contract_satisfied"]]
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        return {
            "status": "SWARM_MMAP_STL_CERTIFIED" if all_satisfied else "SWARM_STL_VIOLATION_DETECTED",
            "agents_monitored": len(worker_traces),
            "total_frames_pushed": total_frames_pushed,
            "total_frames_popped_crc_ok": total_frames_popped,
            "crc_zero_loss": (total_frames_pushed == total_frames_popped),
            "all_agents_satisfied": all_satisfied,
            "violating_agents": violating_agents,
            "global_envelope_contract_satisfied": global_stl["satisfied"],
            "global_overall_stl_robustness": global_stl["overall_stl_robustness"],
            "global_safety_robustness": global_stl["safety_invariance_robustness"],
            "global_response_robustness": global_stl["bounded_response_robustness"],
            "per_worker": per_worker_reports,
            "elapsed_ms": round(elapsed_ms, 3),
        }

    def drain_external_channels(
        self,
        backing_paths: Dict[str, str],
        safety_ceiling: float = 0.95,
        trigger_threshold: float = 0.80,
        recovery_target: float = 0.65,
        response_deadline_steps: int = 4,
    ) -> Dict[str, Any]:
        """
        Anexa-se como consumidor a canais `mmap` já criados por processos workers externos no OS,
        lê todos os frames pendentes com CRC32 e certifica robustez STL.
        """
        t0 = time.perf_counter()
        per_worker: Dict[str, Dict[str, Any]] = {}
        total_popped = 0

        for agent_id, path in backing_paths.items():
            bridge = SharedMemoryMMapSPSCBridge(
                capacity_slots=self.slot_capacity,
                backing_path=path,
                create=False,
            )
            try:
                scalars: List[float] = []
                while True:
                    rec = bridge.pop_frame()
                    if rec is None:
                        break
                    total_popped += 1
                    scalars.append(float(rec["values"][0]))
            finally:
                bridge.close(unlink=False)

            if scalars:
                stl_res = self.stl_monitor.verify_response_guarantee(
                    trace=scalars,
                    safety_ceiling=safety_ceiling,
                    trigger_threshold=trigger_threshold,
                    recovery_target=recovery_target,
                    response_deadline_steps=response_deadline_steps,
                )
                per_worker[agent_id] = {
                    "frames_received": len(scalars),
                    "contract_satisfied": stl_res["satisfied"],
                    "safety_robustness": stl_res["safety_invariance_robustness"],
                    "response_robustness": stl_res["bounded_response_robustness"],
                }
            else:
                per_worker[agent_id] = {
                    "frames_received": 0,
                    "contract_satisfied": False,
                    "safety_robustness": -1e9,
                    "response_robustness": -1e9,
                }

        all_ok = len(per_worker) > 0 and all(w["contract_satisfied"] for w in per_worker.values())
        return {
            "status": "EXTERNAL_SWARM_CERTIFIED" if all_ok else "EXTERNAL_SWARM_VIOLATION_OR_EMPTY",
            "total_frames_popped_crc_ok": total_popped,
            "all_agents_satisfied": all_ok,
            "per_worker": per_worker,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000.0, 3),
        }
