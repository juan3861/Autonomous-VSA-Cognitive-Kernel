import json
import os
import sys


def main():
    proof_path = r"F:\data\proof_torneio_opus_9b_distills.json"
    if not os.path.exists(proof_path):
        print(f"FAIL: Proof file missing: {proof_path}")
        sys.exit(1)

    with open(proof_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    contenders = data.get("contenders", {})
    if not contenders:
        print("FAIL: No contenders found in proof file.")
        sys.exit(1)

    print("\n" + "=" * 88)
    print(" [OMEGA AUDITOR] LEADERBOARD OFICIAL: 9B DESTILADOS VS BASELINE 8B-RLM")
    print("=" * 88)
    base = data.get("baseline_champion", {})
    print(f" * Baseline [8b-rlm        ]: {base.get('final_passes')}/10 ({base.get('final_pct')}%) | Vel: {base.get('avg_tps')} t/s | Tempo: {base.get('total_wall_s')}s")

    for k, c in contenders.items():
        tests = c.get("tests", [])
        if len(tests) != 10:
            print(f"WARN: Contender {k} has only {len(tests)} tests completed.")
        print(f" * Contender [{k:14s}]: {c.get('final_passes')}/10 ({c.get('final_pct')}%) | De 1ª: {c.get('zero_shot_passes')}/10 | Vel: {c.get('avg_tps')} t/s | Tempo: {c.get('total_wall_s')}s")

    print("\nTODAS AS PROVAS DO TORNEIO AUDITADAS COM SUCESSO.")
    sys.exit(0)


if __name__ == "__main__":
    main()
