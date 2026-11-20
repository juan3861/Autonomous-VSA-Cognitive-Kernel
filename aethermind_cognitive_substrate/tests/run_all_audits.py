import argparse
import os
import sys
import time
import threading
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

AUDITOR_PATH = r"F:\AetherMind_Apotheosis_Final\aethermind_apotheosis\AetherMind_Strict_Auditor.py"
TESTS_DIR = r"F:\AetherMind_Apotheosis_Final\aethermind_cognitive_substrate\tests"

GPU_EXCLUSIVE_TOKENS = ("vulkan", "apex_ceiling", "ising_polaris")


def _run_single_suite(idx: int, total: int, test_file: str, gpu_lock: threading.Lock, child_env: dict):
    test_path = os.path.join(TESTS_DIR, test_file)
    needs_gpu_lock = any(tok in test_file.lower() for tok in GPU_EXCLUSIVE_TOKENS)
    t0 = time.perf_counter()

    if needs_gpu_lock:
        with gpu_lock:
            proc = subprocess.run(
                [sys.executable, AUDITOR_PATH, test_path],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=child_env,
                timeout=240,
            )
    else:
        proc = subprocess.run(
            [sys.executable, AUDITOR_PATH, test_path],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=child_env,
            timeout=240,
        )

    elapsed = (time.perf_counter() - t0) * 1000.0
    passed = (proc.returncode == 0) and ("APROVADO" in proc.stdout)
    return {
        "index": idx,
        "test_file": test_file,
        "passed": passed,
        "returncode": proc.returncode,
        "elapsed_ms": elapsed,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def main():
    parser = argparse.ArgumentParser(description="AetherMind Empirical Audit Battery Runner")
    parser.add_argument("--workers", type=int, default=3, help="Parallel worker count (default: 3, GPU-safe)")
    args = parser.parse_args()
    workers = max(1, min(int(args.workers), 6))

    test_files = sorted([
        f for f in os.listdir(TESTS_DIR)
        if f.startswith("test_") and f.endswith(".py")
    ])

    print("=" * 90)
    print(f"AETHERMIND SOVEREIGN COGNITIVE SUBSTRATE — ALL {len(test_files)} TEST SUITES EMPIRICAL AUDIT BATTERY")
    print(f"Timestamp: {datetime.now().isoformat()} | Parallel Workers: {workers} (GPU-Locked)")
    print(f"Python: {sys.executable}")
    print(f"Auditor: {AUDITOR_PATH}")
    print("=" * 90)

    print(f"Discovered {len(test_files)} test suites in {TESTS_DIR}:")
    for idx, tf in enumerate(test_files, 1):
        print(f"  [{idx:02d}/{len(test_files):02d}] {tf}")
    print("=" * 90, flush=True)

    child_env = os.environ.copy()
    child_env["OPENBLAS_NUM_THREADS"] = "1"
    child_env["OMP_NUM_THREADS"] = "1"
    child_env["MKL_NUM_THREADS"] = "1"

    gpu_lock = threading.Lock()
    results = []
    total_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_run_single_suite, idx, len(test_files), tf, gpu_lock, child_env): (idx, tf)
            for idx, tf in enumerate(test_files, 1)
        }
        for fut in as_completed(futures):
            res = fut.result()
            results.append(res)
            status_str = "PASS (EXIT 0)" if res["passed"] else f"FAIL (EXIT {res['returncode']})"
            print(f">>> [{res['index']:02d}/{len(test_files):02d}] {res['test_file']}: {status_str} in {res['elapsed_ms']:.2f} ms", flush=True)
            if not res["passed"]:
                print("    --- STDOUT DUMP ---")
                print(res["stdout"])
                print("    --- STDERR DUMP ---")
                print(res["stderr"])

    results.sort(key=lambda r: r["index"])
    total_elapsed = time.perf_counter() - total_start
    all_passed = all(r["passed"] for r in results)

    print("\n" + "=" * 90)
    print(f"ALL {len(results)} TEST SUITES EMPIRICAL AUDIT SUMMARY REPORT")
    print("=" * 90)
    print(f"{'Idx':<4} | {'Test Suite':<45} | {'Status':<12} | {'Time (ms)':<10} | {'Auditor Verdict'}")
    print("-" * 90)
    for r in results:
        v_str = "APROVADO" if r["passed"] else "REPROVADO"
        print(f"{r['index']:<4} | {r['test_file']:<45} | {('PASS' if r['passed'] else 'FAIL'):<12} | {r['elapsed_ms']:<10.2f} | {v_str}")
    print("-" * 90)
    print(f"Total Suites: {len(results)} | Passed: {sum(1 for r in results if r['passed'])} | Failed: {sum(1 for r in results if not r['passed'])}")
    print(f"Total Duration: {total_elapsed:.2f} s (workers={workers})")
    print("=" * 90)

    if all_passed:
        print(f"\n[VEREDITO FINAL]: TODAS AS {len(results)} SUÍTES FORAM APROVADAS PELO GUARDIÃO OMEGA COM EXIT CODE 0.")
        sys.exit(0)
    else:
        print("\n[VEREDITO FINAL]: FALHA DETECTADA EM UMA OU MAIS SUÍTES. REPROVADO.")
        sys.exit(1)


if __name__ == "__main__":
    main()
