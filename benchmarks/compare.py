"""Compare baseline vs optimized checker performance."""

from __future__ import annotations

import argparse
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, stdev

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from simplified_python.check import Rules, check_source, load_rules
from benchmarks.legacy import check_source as check_source_legacy

EXAMPLES = REPO / "examples"
RULES_PATH = REPO / "skills" / "simplified-python" / "rules.json"


@dataclass(frozen=True)
class Comparison:
    name: str
    baseline_mean: float
    optimized_mean: float
    speedup: float
    baseline_samples: int
    optimized_samples: int

    def __str__(self) -> str:
        if self.speedup >= 1.0:
            return f"{self.name}: baseline {self.baseline_mean:.4f}s → optimized {self.optimized_mean:.4f}s ({self.speedup:.2f}× faster)"
        return f"{self.name}: baseline {self.baseline_mean:.4f}s → optimized {self.optimized_mean:.4f}s ({1.0/self.speedup:.2f}× slower)"


def time_check(
    func: Callable[[str, Rules, str], list], source: str, rules: Rules, path: str, samples: int, warmup: int = 2
) -> tuple[float, int]:
    for _ in range(warmup):
        func(source, rules, path)

    elapsed_samples = []
    for _ in range(samples):
        start = time.perf_counter()
        func(source, rules, path)
        elapsed_samples.append(time.perf_counter() - start)

    return mean(elapsed_samples), samples


def compare_small_file(samples: int = 20) -> Comparison:
    rules = load_rules(RULES_PATH)
    source = (EXAMPLES / "config_loader.py").read_text(encoding="utf-8")

    baseline_mean, baseline_samples = time_check(check_source_legacy, source, rules, "config_loader.py", samples)
    optimized_mean, optimized_samples = time_check(check_source, source, rules, "config_loader.py", samples)

    speedup = baseline_mean / optimized_mean if optimized_mean > 0 else 0
    return Comparison("small_file", baseline_mean, optimized_mean, speedup, baseline_samples, optimized_samples)


def compare_large_synthetic(samples: int = 10) -> Comparison:
    rules = load_rules(RULES_PATH)

    lines = []
    for i in range(1000):
        lines.append(f"x{i} = {i}\n")
        lines.append(f"y{i} = x{i} + 1\n")
        lines.append(f"def func{i}():\n")
        lines.append(f"    return x{i}\n")
        lines.append(f"class Class{i}:\n")
        lines.append(f"    pass\n")
    source = "".join(lines)

    baseline_mean, baseline_samples = time_check(check_source_legacy, source, rules, "large.py", samples)
    optimized_mean, optimized_samples = time_check(check_source, source, rules, "large.py", samples)

    speedup = baseline_mean / optimized_mean if optimized_mean > 0 else 0
    return Comparison("large_synthetic", baseline_mean, optimized_mean, speedup, baseline_samples, optimized_samples)


def compare_restricted_mode(samples: int = 20) -> Comparison:
    rules = load_rules(RULES_PATH)
    source = (EXAMPLES / "config_loader.py").read_text(encoding="utf-8")

    def baseline(source: str, rules: Rules, path: str) -> list:
        return check_source_legacy(source, rules, path, restricted=True)

    def optimized(source: str, rules: Rules, path: str) -> list:
        return check_source(source, rules, path, restricted=True)

    baseline_mean, baseline_samples = time_check(baseline, source, rules, "config_loader.py", samples)
    optimized_mean, optimized_samples = time_check(optimized, source, rules, "config_loader.py", samples)

    speedup = baseline_mean / optimized_mean if optimized_mean > 0 else 0
    return Comparison("restricted_mode", baseline_mean, optimized_mean, speedup, baseline_samples, optimized_samples)


def compare_before_example(samples: int = 20) -> Comparison:
    rules = load_rules(RULES_PATH)
    source = (EXAMPLES / "rewrite" / "before.py").read_text(encoding="utf-8")

    baseline_mean, baseline_samples = time_check(check_source_legacy, source, rules, "before.py", samples)
    optimized_mean, optimized_samples = time_check(check_source, source, rules, "before.py", samples)

    speedup = baseline_mean / optimized_mean if optimized_mean > 0 else 0
    return Comparison("before_example", baseline_mean, optimized_mean, speedup, baseline_samples, optimized_samples)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare baseline vs optimized checker performance")
    parser.add_argument("--samples", type=int, default=20, help="number of samples for each benchmark")
    args = parser.parse_args(argv)

    if not RULES_PATH.exists():
        print(f"Rules not found at {RULES_PATH}; run skill generation first", file=sys.stderr)
        return 1

    print("=== API-Level Comparison (legacy vs optimized) ===\n")

    comparisons = [
        compare_small_file(samples=args.samples),
        compare_large_synthetic(samples=args.samples),
        compare_restricted_mode(samples=args.samples),
        compare_before_example(samples=args.samples),
    ]

    for comp in comparisons:
        print(comp)

    print("\n=== Methodology ===")
    print("- Both implementations parse the source once (ast.parse)")
    print("- Legacy: walks the AST once per rule (O(rules × nodes))")
    print("- Optimized: walks the AST once, checks only relevant rules per node (O(nodes × avg_rules_per_node))")
    print("- Timings exclude CLI overhead and file I/O, measuring only checking logic")
    print("- Warmup runs excluded from timing to account for Python interpreter warmup")
    print(f"- Each benchmark uses {args.samples} samples")

    return 0


if __name__ == "__main__":
    sys.exit(main())
