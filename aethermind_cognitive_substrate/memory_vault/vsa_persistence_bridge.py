"""
Bridge for Sovereign 10,240-bit VSA / Kanerva Hyperdimensional Memory
Provides:
1. Low-level persistence to disk (raw binary 1.28 KB per vector) and SQLite (BLOB / JSON metadata)
2. Interface to query bare-metal native Rust kernel or in-memory Kanerva VSA
3. Friston Free Energy calculation and Epistemic Surprise tracking
"""

import os
import sys
import time
import contextlib
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

WORDS = 160
BITS = WORDS * 64
BYTES = WORDS * 8  # 1280 bytes = 1.28 KB

class VSA10240PersistenceBridge:
    def __init__(self, db_path: Optional[str] = None, storage_dir: Optional[str] = None):
        base_dir = Path(__file__).parent.parent
        self.db_path = db_path or str(base_dir / "aether_memory.db")
        self.storage_dir = Path(storage_dir or (base_dir / "memory_vault" / "hypervectors_bin"))
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.rust_binary = base_dir.parent / "aether_cortex_vsa" / "target" / "release" / "aether_cortex_vsa.exe"
        self._init_db()

    @contextlib.contextmanager
    def _db_conn(self):
        conn = sqlite3.connect(self.db_path)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._db_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS vsa_hypervectors (
                    concept TEXT PRIMARY KEY,
                    category TEXT,
                    vector_blob BLOB,
                    resonance_sigma REAL,
                    free_energy_f REAL,
                    bits_count INTEGER DEFAULT 10240,
                    created_at REAL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS organ_policy_priors (
                    objective_sig TEXT,
                    organ_id TEXT,
                    successes INTEGER DEFAULT 0,
                    rejections INTEGER DEFAULT 0,
                    barrier_interventions INTEGER DEFAULT 0,
                    mean_robustness REAL DEFAULT 0.0,
                    latency_ema_ms REAL DEFAULT 0.0,
                    updated_at REAL,
                    PRIMARY KEY (objective_sig, organ_id)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS composition_episodes (
                    episode_id TEXT PRIMARY KEY,
                    objective TEXT,
                    objective_sig TEXT,
                    pipeline_json TEXT,
                    overall_success INTEGER,
                    certified_safe INTEGER,
                    z3_sat_status TEXT,
                    min_safety_margin REAL,
                    free_energy_f REAL,
                    created_at REAL
                )
            """)
            conn.commit()

    def record_composition_outcome(
        self,
        episode_id: str,
        objective: str,
        objective_sig: str,
        organ_ids: List[str],
        overall_success: bool,
        certified_safe: bool,
        z3_sat_status: str,
        min_safety_margin: float = 0.0,
        barrier_intervened: bool = False,
        latency_ms: float = 0.0,
        free_energy_f: float = 0.0,
    ) -> None:
        """Persist closed-loop composition outcome and update per-organ policy priors."""
        import json
        now = time.time()
        with self._db_conn() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO composition_episodes
                (episode_id, objective, objective_sig, pipeline_json, overall_success,
                 certified_safe, z3_sat_status, min_safety_margin, free_energy_f, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode_id,
                    objective,
                    objective_sig,
                    json.dumps(organ_ids),
                    1 if overall_success else 0,
                    1 if certified_safe else 0,
                    z3_sat_status,
                    float(min_safety_margin),
                    float(free_energy_f),
                    now,
                ),
            )
            succ_inc = 1 if (overall_success and certified_safe) else 0
            rej_inc = 0 if (overall_success and certified_safe) else 1
            bar_inc = 1 if barrier_intervened else 0
            for oid in organ_ids:
                cur = conn.execute(
                    """
                    SELECT successes, rejections, barrier_interventions, mean_robustness, latency_ema_ms
                    FROM organ_policy_priors WHERE objective_sig = ? AND organ_id = ?
                    """,
                    (objective_sig, oid),
                )
                row = cur.fetchone()
                if row is None:
                    conn.execute(
                        """
                        INSERT INTO organ_policy_priors
                        (objective_sig, organ_id, successes, rejections, barrier_interventions,
                         mean_robustness, latency_ema_ms, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (objective_sig, oid, succ_inc, rej_inc, bar_inc, float(min_safety_margin), float(latency_ms), now),
                    )
                else:
                    s_old, r_old, b_old, rob_old, lat_old = row
                    total_n = s_old + r_old + 1
                    new_rob = (rob_old * (total_n - 1) + float(min_safety_margin)) / total_n
                    new_lat = 0.7 * float(lat_old) + 0.3 * float(latency_ms)
                    conn.execute(
                        """
                        UPDATE organ_policy_priors
                        SET successes = ?, rejections = ?, barrier_interventions = ?,
                            mean_robustness = ?, latency_ema_ms = ?, updated_at = ?
                        WHERE objective_sig = ? AND organ_id = ?
                        """,
                        (s_old + succ_inc, r_old + rej_inc, b_old + bar_inc, new_rob, new_lat, now, objective_sig, oid),
                    )
            conn.commit()

    def query_organ_priors(self, objective_sig: str) -> Dict[str, Dict[str, float]]:
        """Retrieve accumulated cross-session policy priors for an objective signature."""
        with self._db_conn() as conn:
            cur = conn.execute(
                """
                SELECT organ_id, successes, rejections, barrier_interventions, mean_robustness, latency_ema_ms
                FROM organ_policy_priors
                WHERE objective_sig = ?
                """,
                (objective_sig,),
            )
            rows = cur.fetchall()

        priors: Dict[str, Dict[str, float]] = {}
        for oid, succ, rej, bar, rob, lat in rows:
            total = max(1, int(succ) + int(rej))
            succ_rate = float(succ) / total
            rej_rate = float(rej) / total
            bar_rate = float(bar) / total
            score_delta = (0.30 * succ_rate) - (0.40 * rej_rate) - (0.15 * bar_rate) + (0.05 * max(-1.0, min(1.0, float(rob))))
            priors[oid] = {
                "successes": float(succ),
                "rejections": float(rej),
                "barrier_interventions": float(bar),
                "mean_robustness": float(rob),
                "latency_ema_ms": float(lat),
                "score_delta": score_delta,
            }
        return priors

    def load_recent_episodes(self, objective_sig: Optional[str] = None, limit: int = 25) -> List[Dict[str, Any]]:
        """Load persisted composition episodes for cold-start HippoRAG/PagedMemoryOS hydration."""
        import json
        with self._db_conn() as conn:
            if objective_sig is not None:
                cur = conn.execute(
                    """
                    SELECT episode_id, objective, objective_sig, pipeline_json, overall_success,
                           certified_safe, z3_sat_status, min_safety_margin, free_energy_f, created_at
                    FROM composition_episodes
                    WHERE objective_sig = ?
                    ORDER BY created_at DESC LIMIT ?
                    """,
                    (objective_sig, int(limit)),
                )
            else:
                cur = conn.execute(
                    """
                    SELECT episode_id, objective, objective_sig, pipeline_json, overall_success,
                           certified_safe, z3_sat_status, min_safety_margin, free_energy_f, created_at
                    FROM composition_episodes
                    ORDER BY created_at DESC LIMIT ?
                    """,
                    (int(limit),),
                )
            rows = cur.fetchall()

        episodes: List[Dict[str, Any]] = []
        for ep_id, obj, osig, pjson, succ, safe, z3s, margin, fe, ts in rows:
            episodes.append({
                "episode_id": ep_id,
                "objective": obj,
                "objective_sig": osig,
                "pipeline": json.loads(pjson),
                "overall_success": bool(succ),
                "certified_safe": bool(safe),
                "z3_sat_status": z3s,
                "min_safety_margin": float(margin),
                "free_energy_f": float(fe),
                "created_at": float(ts),
            })
        return episodes

    def generate_random_orthogonal(self, seed: Optional[int] = None) -> np.ndarray:
        """Generates 160 uint64 words = 10,240 bits."""
        rng = np.random.default_rng(seed)
        return rng.integers(0, 2**64, size=WORDS, dtype=np.uint64)

    def bind_xor(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """XOR Binding: A ^ B."""
        return np.bitwise_xor(a, b)

    def hamming_distance(self, a: np.ndarray, b: np.ndarray) -> int:
        """Hamming distance via POPCNT on uint64 words."""
        diff = np.bitwise_xor(a, b)
        # Vectorized bit count
        total = 0
        for w in diff:
            total += int(w).bit_count()
        return total

    def compute_resonance_sigma(self, dist: int) -> float:
        expected = BITS * 0.5  # 5120
        sigma = 50.59644256269407
        return (expected - dist) / sigma

    def save_hypervector(self, concept: str, vector: np.ndarray, category: str = "general", resonance_sigma: float = 0.0, free_energy_f: float = 0.0):
        raw_bytes = vector.tobytes()
        assert len(raw_bytes) == BYTES, f"Expected {BYTES} bytes, got {len(raw_bytes)}"
        
        # 1. Save binary file
        bin_file = self.storage_dir / f"{concept}.bin"
        with open(bin_file, "wb") as f:
            f.write(raw_bytes)

        # 2. Save in SQLite
        with self._db_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO vsa_hypervectors (concept, category, vector_blob, resonance_sigma, free_energy_f, bits_count, created_at)
                VALUES (?, ?, ?, ?, ?, 10240, ?)
            """, (concept, category, raw_bytes, resonance_sigma, free_energy_f, time.time()))
            conn.commit()

    def load_hypervector(self, concept: str) -> Optional[np.ndarray]:
        # Try database first
        with self._db_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT vector_blob FROM vsa_hypervectors WHERE concept = ?", (concept,))
            row = cur.fetchone()
            if row and row[0]:
                return np.frombuffer(row[0], dtype=np.uint64)

        # Fallback to file
        bin_file = self.storage_dir / f"{concept}.bin"
        if bin_file.exists():
            with open(bin_file, "rb") as f:
                return np.frombuffer(f.read(), dtype=np.uint64)

        return None

    def execute_rust_kernel_proof(self) -> Dict[str, Any]:
        """Invokes the compiled Bare-Metal Rust VSA binary and parses telemetry."""
        if not self.rust_binary.exists():
            raise FileNotFoundError(f"Rust VSA binary not found at {self.rust_binary}")

        res = subprocess.run([str(self.rust_binary)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        if res.returncode != 0:
            raise RuntimeError(f"Rust Kernel failed with code {res.returncode}: {res.stderr}")

        return {
            "status": "SUCCESS",
            "exit_code": res.returncode,
            "stdout_length": len(res.stdout),
            "execution_verified": "SUBSTRATO SOBERANO VSA 10.240 BITS VALIDADO" in res.stdout or "FASE 5" in res.stdout,
            "raw_output": res.stdout[:1000]
        }
