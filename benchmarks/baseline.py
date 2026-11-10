"""Baseline benchmark for the checker.

Measures:
- Cold CLI startup
- Small file checking
- Large synthetic file checking
- Many files (default and --restricted modes)
- Separate profiling: parsing, traversal-only, matching, output
"""

from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from statistics import mean, median, stdev

REPO = Path(__file__).resolve().parents[1]
CHECKER = REPO / "src" / "simplified_python" / "check.py"
EXAMPLES = REPO / "examples"


@dataclass(frozen=True)
class Timing:
    name: str
    seconds: float
    samples: int

    def __str__(self) -> str:
        if self.samples > 1:
            return f"{self.name}: {self.seconds:.4f}s (n={self.samples})"
        return f"{self.name}: {self.seconds:.4f}s"


def time_it(func: Callable[[], float], samples: int = 1, warmup: int = 0, name: str | None = None) -> Timing:
    for _ in range(warmup):
        func()

    if samples == 1:
        elapsed = func()
        return Timing(name or func.__name__, elapsed, 1)

    elapsed_samples = []
    for _ in range(samples):
        elapsed_samples.append(func())

    return Timing(name or func.__name__, mean(elapsed_samples), samples)


def cold_cli_startup(samples: int = 5) -> Timing:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rules_path = tmp / "rules.json"
        test_file = tmp / "test.py"

        skills_rules = REPO / "skills" / "simplified-python" / "rules.json"
        if skills_rules.exists():
            shutil.copy(skills_rules, rules_path)
        else:
            result = subprocess.run(
                [sys.executable, "-m", "simplified_python.skill"],
                cwd=REPO,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to generate rules: {result.stderr}")
            shutil.copy(skills_rules, rules_path)

        test_file.write_text("x = 1\n")

        def run() -> float:
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, str(CHECKER), "--rules", str(rules_path), str(test_file)],
                cwd=REPO,
                capture_output=True,
                text=True,
            )
            elapsed = time.perf_counter() - start
            if result.returncode not in (0, 1):
                raise RuntimeError(f"CLI failed: {result.stderr}")
            return elapsed

        return time_it(run, samples=samples, name="cold_cli_startup")


def small_file_check(samples: int = 10) -> Timing:
    from simplified_python.check import check_source, load_rules

    rules_path = REPO / "skills" / "simplified-python" / "rules.json"
    if not rules_path.exists():
        raise RuntimeError("Rules not found; run skill generation first")

    rules = load_rules(rules_path)
    source = (EXAMPLES / "config_loader.py").read_text(encoding="utf-8")

    def run() -> float:
        start = time.perf_counter()
        check_source(source, rules, "config_loader.py")
        elapsed = time.perf_counter() - start
        return elapsed

    return time_it(run, samples=samples, name="small_file_check")


def large_synthetic_file(samples: int = 5) -> Timing:
    from simplified_python.check import check_source, load_rules

    rules_path = REPO / "skills" / "simplified-python" / "rules.json"
    if not rules_path.exists():
        raise RuntimeError("Rules not found; run skill generation first")

    rules = load_rules(rules_path)

    lines = []
    for i in range(1000):
        lines.append(f"x{i} = {i}\n")
        lines.append(f"y{i} = x{i} + 1\n")
        lines.append(f"def func{i}():\n")
        lines.append(f"    return x{i}\n")
        lines.append(f"class Class{i}:\n")
        lines.append(f"    pass\n")
    source = "".join(lines)

    def run() -> float:
        start = time.perf_counter()
        check_source(source, rules, "large.py")
        elapsed = time.perf_counter() - start
        return elapsed

    return time_it(run, samples=samples, name="large_synthetic_file")


def many_files_default(samples: int = 3) -> Timing:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rules_path = tmp / "rules.json"

        skills_rules = REPO / "skills" / "simplified-python" / "rules.json"
        if not skills_rules.exists():
            raise RuntimeError("Rules not found; run skill generation first")
        shutil.copy(skills_rules, rules_path)

        for i in range(100):
            (tmp / f"file{i}.py").write_text(f"x{i} = {i}\n")

        def run() -> float:
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, str(CHECKER), "--rules", str(rules_path), str(tmp)],
                cwd=REPO,
                capture_output=True,
                text=True,
            )
            elapsed = time.perf_counter() - start
            if result.returncode not in (0, 1):
                raise RuntimeError(f"CLI failed: {result.stderr}")
            return elapsed

        return time_it(run, samples=samples, name="many_files_default")


def many_files_restricted(samples: int = 3) -> Timing:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        rules_path = tmp / "rules.json"

        skills_rules = REPO / "skills" / "simplified-python" / "rules.json"
        if not skills_rules.exists():
            raise RuntimeError("Rules not found; run skill generation first")
        shutil.copy(skills_rules, rules_path)

        for i in range(100):
            (tmp / f"file{i}.py").write_text(f"x{i} = {i}\n")

        def run() -> float:
            start = time.perf_counter()
            result = subprocess.run(
                [sys.executable, str(CHECKER), "--rules", str(rules_path), "--restricted", str(tmp)],
                cwd=REPO,
                capture_output=True,
                text=True,
            )
            elapsed = time.perf_counter() - start
            if result.returncode not in (0, 1):
                raise RuntimeError(f"CLI failed: {result.stderr}")
            return elapsed

        return time_it(run, samples=samples, name="many_files_restricted")


def profile_phases(samples: int = 20) -> dict[str, dict[str, float]]:
    from simplified_python.check import _build_rule_index, _check_tree, load_rules

    rules_path = REPO / "skills" / "simplified-python" / "rules.json"
    if not rules_path.exists():
        raise RuntimeError("Rules not found; run skill generation first")

    rules = load_rules(rules_path)
    source = (EXAMPLES / "config_loader.py").read_text(encoding="utf-8")

    def profile_parse() -> float:
        start = time.perf_counter()
        ast.parse(source, filename="config_loader.py")
        return time.perf_counter() - start

    def profile_index() -> float:
        start = time.perf_counter()
        _build_rule_index(rules, False)
        return time.perf_counter() - start

    def profile_traversal_only() -> float:
        tree = ast.parse(source, filename="config_loader.py")
        rule_index = _build_rule_index(rules, False)
        start = time.perf_counter()
        stack = [(tree, 1, 1)]
        nodes_visited = 0
        while stack:
            node, line, column = stack.pop()
            nodes_visited += 1
            if hasattr(node, "lineno"):
                line, column = node.lineno, node.col_offset + 1
            stack.extend((child, line, column) for child in ast.iter_child_nodes(node))
        return time.perf_counter() - start

    def profile_matching_on_parsed() -> float:
        tree = ast.parse(source, filename="config_loader.py")
        rule_index = _build_rule_index(rules, False)
        start = time.perf_counter()
        _check_tree(tree, "config_loader.py", rule_index)
        return time.perf_counter() - start

    def profile_rendering() -> float:
        tree = ast.parse(source, filename="config_loader.py")
        rule_index = _build_rule_index(rules, False)
        findings = _check_tree(tree, "config_loader.py", rule_index)
        start = time.perf_counter()
        _ = [str(f) for f in findings]
        return time.perf_counter() - start

    def profile_full() -> float:
        from simplified_python.check import check_source
        start = time.perf_counter()
        check_source(source, rules, "config_loader.py")
        return time.perf_counter() - start

    for _ in range(3):
        profile_parse()
        profile_index()
        profile_traversal_only()
        profile_matching_on_parsed()
        profile_rendering()
        profile_full()

    parse_samples = [profile_parse() for _ in range(samples)]
    index_samples = [profile_index() for _ in range(samples)]
    traversal_samples = [profile_traversal_only() for _ in range(samples)]
    matching_samples = [profile_matching_on_parsed() for _ in range(samples)]
    rendering_samples = [profile_rendering() for _ in range(samples)]
    full_samples = [profile_full() for _ in range(samples)]

    return {
        "parse": {"mean": mean(parse_samples), "median": median(parse_samples), "samples": samples},
        "index": {"mean": mean(index_samples), "median": median(index_samples), "samples": samples},
        "traversal_only": {"mean": mean(traversal_samples), "median": median(traversal_samples), "samples": samples},
        "matching_on_parsed": {"mean": mean(matching_samples), "median": median(matching_samples), "samples": samples},
        "rendering": {"mean": mean(rendering_samples), "median": median(rendering_samples), "samples": samples},
        "full": {"mean": mean(full_samples), "median": median(full_samples), "samples": samples},
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Baseline benchmark for simplified-Python checker")
    parser.add_argument("--samples", type=int, default=5, help="number of samples for each benchmark")
    parser.add_argument("--profile", action="store_true", help="include detailed profiling")
    args = parser.parse_args(argv)

    print("=== Baseline Benchmark ===\n")

    timings = [
        cold_cli_startup(samples=args.samples),
        small_file_check(samples=args.samples),
        large_synthetic_file(samples=args.samples),
        many_files_default(samples=args.samples),
        many_files_restricted(samples=args.samples),
    ]

    for timing in timings:
        print(timing)

    if args.profile:
        print("\n=== Phase Profiling (config_loader.py, 20 samples) ===")
        profile = profile_phases(samples=20)
        for phase, stats in profile.items():
            print(f"{phase}: mean {stats['mean']:.6f}s, median {stats['median']:.6f}s (n={stats['samples']})")

        print("\n=== Profiling Notes ===")
        print("- parse: ast.parse only")
        print("- index: rule index construction")
        print("- traversal_only: walk AST without matching")
        print("- matching_on_parsed: check pre-parsed tree with matching")
        print("- rendering: convert findings to strings")
        print("- full: complete check_source call")
        print("- Phases measured independently, not additive")
        print("- CLI overhead includes Python interpreter startup and module imports")

    return 0


if __name__ == "__main__":
    sys.exit(main())
