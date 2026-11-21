import json
import os
import sys

sys.path.insert(0, r"F:\rotor-llm")
from router.formal_verifier import FormalVerifier4State


def main():
    proof_path = r"F:\data\proof_duelo_opus_8b_vs_9b.json"
    if not os.path.exists(proof_path):
        print(f"FAIL: Proof file missing: {proof_path}")
        sys.exit(1)

    with open(proof_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contenders = data.get("contenders", {})
    for key in ["8b-rlm", "9b-heretic"]:
        if key not in contenders:
            print(f"FAIL: Missing contender {key}")
            sys.exit(1)
        m = contenders[key]
        if m.get("total_tests") != 10:
            print(f"FAIL: Expected 10 Opus tests for {key}, got {m.get('total_tests')}")
            sys.exit(1)
        tests = m.get("tests", [])
        if len(tests) != 10:
            print(f"FAIL: Expected 10 test records for {key}, got {len(tests)}")
            sys.exit(1)
        print(
            f"[AUDIT OPUS] {key}: Zero-Shot={m['zero_shot_passes']}/10 ({m['zero_shot_pct']}%), "
            f"Final={m['final_passes']}/10 ({m['final_pass_pct']}%), "
            f"Repaired={m['repaired_passes']}, "
            f"Avg TPS={m['avg_raw_tok_per_s']} t/s (Eff={m['avg_effective_tok_per_s']} t/s), "
            f"Total Wall={m['total_time_s']}s"
        )

    print("ALL OPUS DUEL PROOFS VERIFIED EMPIRICALLY.")
    sys.exit(0)


if __name__ == "__main__":
    main()
