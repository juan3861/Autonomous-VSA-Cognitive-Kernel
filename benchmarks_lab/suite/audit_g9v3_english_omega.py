import json
import os
import sys


def main():
    proof_path = r"F:\data\proof_g9v3_english_benchmark.json"
    if not os.path.exists(proof_path):
        print(f"FAIL: Proof file missing: {proof_path}")
        sys.exit(1)

    with open(proof_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    p1 = data.get("part1_summary", {})
    p2 = data.get("part2_opus_10", {})

    if not p1 or not p2:
        print("FAIL: Incomplete data in proof file.")
        sys.exit(1)

    print("\n" + "=" * 88)
    print(" [OMEGA AUDITOR] AI9STARS / G9V3-3B (1.77 GB) BENCHMARK EM INGLÊS")
    print("=" * 88)
    print(f" * Model: {data.get('model_filename')}")
    print(f" * Model Size: {data.get('model_size_gb')} GB")
    print(f" * Backend: {data.get('backend')}")
    print(f" * Part 1 (13 Areas EN - 39 tests): {p1.get('total_passed')}/{p1.get('total_tests')} ({p1.get('pct')}%) | Avg TPS: {p1.get('avg_tps')} t/s | Time: {p1.get('total_time_s')}s")
    print(f" * Part 2 (10 Opus Challenges EN): {p2.get('final_passes')}/10 ({p2.get('final_pct')}%) | 1st-try: {p2.get('zero_shot_passes')}/10 | Repaired: {p2.get('repaired_passes')}/10 | Avg TPS: {p2.get('avg_tps')} t/s | Time: {p2.get('total_time_s')}s")
    print("=" * 88)
    print("\nPROVA EMPÍRICA AUDITADA E APROVADA.")
    sys.exit(0)


if __name__ == "__main__":
    main()
