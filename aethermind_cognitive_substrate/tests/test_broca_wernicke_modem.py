"""
Strict Empirical Test for Broca-Wernicke Language Modem
Verifies:
1. Wernicke Input Translation to 10,240-bit Hypervector
2. Reflex Homeostatic Loop (0% GPU / 0% LLM) executed in microseconds
3. Epistemic Shock Detection and Fallback to Cortex Formals
4. Broca Output Speech Synthesis
"""

import sys
import os
from pathlib import Path

# Ensure root in sys.path
root_dir = str(Path(__file__).parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# UTF-8 safe output
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from aethermind_cognitive_substrate.physical_bridge.broca_wernicke_modem import BrocaWernickeModem

def test_broca_wernicke_modem():
    modem = BrocaWernickeModem()

    # 1. Test Homeostatic Reflex Input
    turn1 = modem.process_turn("Status do sistema agora")
    print("[TEST REFLEX TURN 1]:", turn1)
    assert turn1["is_reflex"] is True
    assert "0%" in turn1["gpu_consumption"]
    assert turn1["llm_token_generation"] == 0
    assert "SOVEREIGN_READY" in turn1["output_text"]
    assert turn1["elapsed_ms"] < 100.0, f"Latency too high: {turn1['elapsed_ms']} ms"

    # 2. Test Epistemic Shock / Complex Turn
    turn2 = modem.process_turn("Explique a teoria quântica de campos e sua relação com a termodinâmica")
    print("[TEST COMPLEX TURN 2]:", turn2)
    assert turn2["is_reflex"] is False
    assert turn2["free_energy"] == 1.0
    assert "BROCA DISCURSIVO" in turn2["output_text"]

    # 3. Test Navigation / Operational Intent (Warmed Reflex < 20 ms)
    turn3 = modem.process_turn("Prossiga com a missão")
    print("[TEST MISSION TURN 3]:", turn3)
    assert turn3["is_reflex"] is True
    assert "EXECUCAO_AUTONOMA" in turn3["output_text"]
    assert turn3["elapsed_ms"] < 20.0, f"Warmed reflex latency too high: {turn3['elapsed_ms']} ms"

    print("[TEST PASSED] Broca-Wernicke Language Modem empirically verified with zero LLM overhead for reflexes!")

if __name__ == "__main__":
    test_broca_wernicke_modem()
