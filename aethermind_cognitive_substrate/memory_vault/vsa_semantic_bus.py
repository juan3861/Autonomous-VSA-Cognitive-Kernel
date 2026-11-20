"""Autonomous VSA Hyperdimensional Semantic Bus (10,240-bit Cross-Organ Fabric).

Provides a decoupled, holographically-encoded communication and state-sharing bus
for the 82 mathematical organs of the Autonomous VSA Cognitive Kernel.

Mathematical Formulation:
- Space: Hyperdimensional bipolar vector space $\mathcal{H} = \{-1, +1\}^D$ with $D = 10,240$.
- Concentration of Measure: For independent random vectors $u, v \sim \mathcal{U}(\mathcal{H})$,
  $\mathbb{E}[\langle u, v \rangle / D] = 0$, $\mathrm{Var}(\langle u, v \rangle / D) = 1/D \approx 9.76 \times 10^{-5}$.
- Holographic Binding (Multiply / XOR): $z = u \odot v$, where $z \odot u = v$ (self-inverse).
- Holographic Bundling (Majority Vote Superposition):
  $S = \mathrm{sgn}\left(\sum_{k=1}^M v_k\right)$, preserving similarity to all constituents:
  $\langle S, v_k \rangle / D \approx \frac{1}{\sqrt{M}}$.
- Semantic Fact Encoding:
  $H_{\text{event}} = \mathrm{bundle}\left(\bigoplus_{i=1}^K (\text{Key}_i \odot \text{Value}_i)\right) \odot \text{Topic} \odot \text{Organ}$.
"""
from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from .kanerva_hdc_10000_vsa import KanervaHDC10000VSA


@dataclass
class VSAEvent:
    """Immutable semantic event transmitted over the hyperdimensional bus."""
    event_id: str
    topic: str
    organ_id: str
    timestamp: float
    hypervector: np.ndarray
    payload: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0


class VSAHyperdimensionalBus:
    """Decoupled 10,240-bit Hyperdimensional Semantic Bus for Multi-Organ Coordination."""

    def __init__(self, dimension: int = 10240, seed: int = 42, max_history: int = 1000):
        self.dimension = dimension
        self.max_history = max_history
        self.vsa = KanervaHDC10000VSA(dimension=dimension, seed=seed)
        self.event_log: List[VSAEvent] = []
        self._topic_subscriptions: Dict[str, List[str]] = {}
        self._scalar_quantizers: Dict[str, Tuple[float, float, int]] = {}

    def encode_scalar(self, name: str, value: float, min_val: float = -10.0, max_val: float = 10.0, bins: int = 64) -> np.ndarray:
        """Encode a continuous scalar value into a graded hypervector (thermometer code)."""
        clamped = max(min_val, min(max_val, float(value)))
        ratio = (clamped - min_val) / max(1e-9, (max_val - min_val))
        bin_idx = int(round(ratio * (bins - 1)))

        # Generates smooth continuous transition across levels
        base_low = self.vsa.register_symbol(f"scalar_{name}_low")
        base_high = self.vsa.register_symbol(f"scalar_{name}_high")

        # Fractional blend / flip proportion of bits
        cutoff = int(self.dimension * (bin_idx / float(bins)))
        vec = base_low.copy()
        vec[:cutoff] = base_high[:cutoff]
        return vec.astype(np.int8)

    def encode_dict(self, data: Dict[str, Any]) -> np.ndarray:
        """Encode a key-value dictionary into a composite bound-bundled hypervector."""
        bound_pairs = []
        for k, v in data.items():
            k_vec = self.vsa.register_symbol(f"key_{k}")
            if isinstance(v, (int, float)):
                v_vec = self.encode_scalar(k, float(v))
            elif isinstance(v, str):
                v_vec = self.vsa.register_symbol(f"val_{v}")
            elif isinstance(v, (list, tuple)) and all(isinstance(x, (int, float)) for x in v):
                # Small numeric vector encoding via positional permutation
                sub_vecs = []
                for idx, elem in enumerate(v[:16]):
                    pos_vec = self.vsa.permute(self.vsa.register_symbol(f"pos_{idx}"), shift=idx + 1)
                    val_vec = self.encode_scalar(f"{k}_{idx}", float(elem))
                    sub_vecs.append(self.vsa.bind(pos_vec, val_vec))
                v_vec = self.vsa.bundle(sub_vecs)
            else:
                v_vec = self.vsa.register_symbol(f"val_{str(v)[:32]}")

            bound_pairs.append(self.vsa.bind(k_vec, v_vec))

        if not bound_pairs:
            return self.vsa.register_symbol("empty_payload")

        return self.vsa.bundle(bound_pairs)

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        organ_id: str = "anonymous",
        confidence: float = 1.0
    ) -> VSAEvent:
        """Publish an event onto the semantic bus, encoding it as a 10,240-bit hypervector."""
        t_topic = self.vsa.register_symbol(f"topic_{topic}")
        t_organ = self.vsa.register_symbol(f"organ_{organ_id}")
        t_payload = self.encode_dict(payload)

        # Composite event: (Payload) * Topic * Organ
        composite_hv = self.vsa.bind(self.vsa.bind(t_payload, t_topic), t_organ)

        event = VSAEvent(
            event_id=f"evt_{len(self.event_log):06d}_{int(time.time()*1000)}",
            topic=topic,
            organ_id=organ_id,
            timestamp=time.time(),
            hypervector=composite_hv,
            payload=payload,
            confidence=confidence,
        )

        self.event_log.append(event)
        if len(self.event_log) > self.max_history:
            self.event_log.pop(0)

        return event

    def query_similarity(self, query_hv: np.ndarray, top_k: int = 5) -> List[Tuple[VSAEvent, float]]:
        """Find past events with highest holographic cosine similarity to query vector."""
        if not self.event_log:
            return []

        results = []
        for evt in self.event_log:
            sim = self.vsa.cosine_similarity(query_hv, evt.hypervector)
            results.append((evt, sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def query_by_topic(self, topic: str, limit: int = 10) -> List[VSAEvent]:
        """Retrieve recent events under a specific semantic topic."""
        matches = [e for e in reversed(self.event_log) if e.topic == topic]
        return matches[:limit]

    def extract_field(self, event: VSAEvent, field_key: str) -> Optional[np.ndarray]:
        """Unbind a specific field key from an event's hypervector."""
        k_vec = self.vsa.register_symbol(f"key_{field_key}")
        t_topic = self.vsa.register_symbol(f"topic_{event.topic}")
        t_organ = self.vsa.register_symbol(f"organ_{event.organ_id}")

        # Unbind topic and organ first
        payload_composite = self.vsa.bind(self.vsa.bind(event.hypervector, t_organ), t_topic)
        # Unbind key
        extracted_val_noisy = self.vsa.bind(payload_composite, k_vec)
        return extracted_val_noisy

    def get_bus_state_summary(self) -> Dict[str, Any]:
        """Telemetry diagnostics on active semantic bus activity."""
        topic_counts: Dict[str, int] = {}
        organ_counts: Dict[str, int] = {}
        for e in self.event_log:
            topic_counts[e.topic] = topic_counts.get(e.topic, 0) + 1
            organ_counts[e.organ_id] = organ_counts.get(e.organ_id, 0) + 1

        return {
            "total_events": len(self.event_log),
            "dimension": self.dimension,
            "unique_topics": len(topic_counts),
            "topics": topic_counts,
            "active_organs": organ_counts,
            "latest_timestamp": self.event_log[-1].timestamp if self.event_log else 0.0,
        }
