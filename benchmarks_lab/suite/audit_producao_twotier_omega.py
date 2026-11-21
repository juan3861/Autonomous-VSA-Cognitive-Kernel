import json
import os
import sys


def main():
    proof_path = r"F:\data\proof_producao_twotier_fechado.json"
    if not os.path.exists(proof_path):
        print(f"FAIL: Proof file missing: {proof_path}")
        sys.exit(1)

    with open(proof_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("final_status") != "ALL_TIERS_OPERATIONAL_AND_VERIFIED":
        print(f"FAIL: Unexpected final status: {data.get('final_status')}")
        sys.exit(1)

    steps = data.get("steps", [])
    if len(steps) != 3:
        print(f"FAIL: Expected 3 steps, got {len(steps)}")
        sys.exit(1)

    for s in steps:
        if s.get("status") != "PASS":
            print(f"FAIL: Step {s.get('step')} failed with status {s.get('status')}")
            sys.exit(1)
        print(f"[AUDIT STEP] {s['step']}: Tier {s['tier']} ({s['model']}) -> {s['status']} ({s['latency_ms']} ms)")

    print("ALL TWO-TIER PRODUCTION INVARIANTS VERIFIED EMPIRICALLY.")
    sys.exit(0)


if __name__ == "__main__":
    main()
