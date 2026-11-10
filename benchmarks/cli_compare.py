"""End-to-end CLI comparison: legacy vs optimized scripts.

Compares the legacy check.py (from git baseline) against the current optimized version
using subprocess calls to measure actual CLI performance.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median

REPO = Path(__file__).resolve().parents[1]
EXAMPLES = REPO / "examples"


@dataclass(frozen=True)
class Comparison:
    workload: str
    legacy_median: float
    optimized_median: float
    speedup: float
    samples: int
    files: int

    def __str__(self) -> str:
        if self.speedup >= 1.0:
            return f"{self.workload} ({self.files} files): legacy {self.legacy_median:.4f}s → optimized {self.optimized_median:.4f}s ({self.speedup:.2f}× faster, n={self.samples})"
        return f"{self.workload} ({self.files} files): legacy {self.legacy_median:.4f}s → optimized {self.optimized_median:.4f}s ({1.0/self.speedup:.2f}× slower, n={self.samples})"


def get_legacy_checker(baseline_ref: str = "f60e3e5") -> Path:
    tmp = Path(tempfile.mkdtemp())
    result = subprocess.run(
        ["git", "show", f"{baseline_ref}:src/simplified_python/check.py"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    )
    legacy_path = tmp / "legacy_check.py"
    legacy_path.write_text(result.stdout)
    return legacy_path


def time_cli(checker_path: Path, rules_path: Path, target: Path, restricted: bool = False) -> tuple[float, str, str, int]:
    args = [sys.executable, str(checker_path), "--rules", str(rules_path)]
    if restricted:
        args.append("--restricted")
    args.append(str(target))

    start = time.perf_counter()
    result = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    elapsed = time.perf_counter() - start

    if result.returncode not in (0, 1):
        raise RuntimeError(f"CLI failed: {result.stderr}")

    return elapsed, result.stdout, result.stderr, result.returncode


def compare_workload(workload_name: str, target: Path, samples: int, restricted: bool = False, file_count: int = 1) -> Comparison:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        legacy_checker = get_legacy_checker()
        optimized_checker = tmp / "optimized_check.py"
        rules_path = tmp / "rules.json"

        shutil.copy(REPO / "src" / "simplified_python" / "check.py", optimized_checker)
        shutil.copy(REPO / "skills" / "simplified-python" / "rules.json", rules_path)

        legacy_samples = []
        optimized_samples = []
        legacy_outputs = []
        optimized_outputs = []

        for _ in range(samples):
            elapsed, stdout, stderr, returncode = time_cli(legacy_checker, rules_path, target, restricted)
            legacy_samples.append(elapsed)
            legacy_outputs.append((stdout, stderr, returncode))

            elapsed, stdout, stderr, returncode = time_cli(optimized_checker, rules_path, target, restricted)
            optimized_samples.append(elapsed)
            optimized_outputs.append((stdout, stderr, returncode))

        legacy_median = median(legacy_samples)
        optimized_median = median(optimized_samples)
        speedup = legacy_median / optimized_median if optimized_median > 0 else 0

        for (l_out, l_err, l_ret), (o_out, o_err, o_ret) in zip(legacy_outputs, optimized_outputs):
            assert l_out == o_out, f"Output mismatch: legacy={l_out!r}, optimized={o_out!r}"
            assert l_err == o_err, f"Stderr mismatch: legacy={l_err!r}, optimized={o_err!r}"
            assert l_ret == o_ret, f"Returncode mismatch: legacy={l_ret}, optimized={o_ret}"

        return Comparison(workload_name, legacy_median, optimized_median, speedup, samples, file_count)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="End-to-end CLI comparison: legacy vs optimized")
    parser.add_argument("--samples", type=int, default=5, help="number of samples per workload (>=3)")
    parser.add_argument("--baseline-ref", type=str, default="f60e3e5", help="git ref for legacy baseline")
    args = parser.parse_args(argv)

    if args.samples < 3:
        print("Samples must be >= 3", file=sys.stderr)
        return 1

    skills_rules = REPO / "skills" / "simplified-python" / "rules.json"
    if not skills_rules.exists():
        print("Rules not found; run skill generation first", file=sys.stderr)
        return 1

    print("=== End-to-End CLI Comparison (legacy vs optimized) ===\n")

    comparisons = []

    small_file = EXAMPLES / "config_loader.py"
    comparisons.append(compare_workload("small_file_default", small_file, samples=args.samples, restricted=False, file_count=1))
    comparisons.append(compare_workload("small_file_restricted", small_file, samples=args.samples, restricted=True, file_count=1))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        large_file = tmp / "large.py"
        lines = []
        for i in range(1000):
            lines.append(f"x{i} = {i}\n")
            lines.append(f"y{i} = x{i} + 1\n")
            lines.append(f"def func{i}():\n")
            lines.append(f"    return x{i}\n")
            lines.append(f"class Class{i}:\n")
            lines.append(f"    pass\n")
        large_file.write_text("".join(lines))
        comparisons.append(compare_workload("large_synthetic_default", large_file, samples=args.samples, restricted=False, file_count=1))
        comparisons.append(compare_workload("large_synthetic_restricted", large_file, samples=args.samples, restricted=True, file_count=1))

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        config_source = (EXAMPLES / "config_loader.py").read_text(encoding="utf-8")
        for i in range(100):
            (tmp / f"file{i}.py").write_text(config_source)
        comparisons.append(compare_workload("many_files_default", tmp, samples=args.samples, restricted=False, file_count=100))
        comparisons.append(compare_workload("many_files_restricted", tmp, samples=args.samples, restricted=True, file_count=100))

    for comp in comparisons:
        print(comp)

    print("\n=== Methodology ===")
    print(f"- Legacy: check.py from git {args.baseline_ref} (walks AST once per rule)")
    print("- Optimized: current check.py (single walk, indexed rules)")
    print("- Both run as subprocess CLI with same rules.json")
    print("- Workloads: small file (~60 lines), large synthetic (6000 lines), 100 files (~60 lines each)")
    print("- Median reported over N samples to reduce outlier impact")
    print("- Output equality verified between legacy and optimized")
    print("- Includes full CLI overhead: Python startup, imports, file I/O, checking")
    print(f"- Samples: {args.samples} per workload (no halving)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
