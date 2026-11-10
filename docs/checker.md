# How the checker works

The checker uses CPython's Python 3.14 AST and a generated rules snapshot. It does not execute or rewrite the input program. Its implementation is in `src/simplified_python/check.py`; skill generation copies that file into `skills/simplified-python/check.py` so the installed skill uses the same implementation without importing the package.

## From rules to findings

1. **Load the snapshot.** `rules.json` contains the registry's banned and restricted rules, including their AST anchors, replacement guidance and conditions. The CLI refuses to check files if its interpreter's Python minor version differs from the snapshot's version.
2. **Build an index once.** `_build_rule_index` selects banned rules by default, or banned and restricted rules with `--restricted`. It groups them by AST class name and prepares their diagnostic text. A rule covering several node types appears under each type. The CLI reuses this index across all files in the invocation.
3. **Parse each file once.** `ast.parse` builds the tree. Syntax and read errors are reported rather than treating the file as clean.
4. **Walk the tree once.** `_check_tree` uses an explicit stack of `(node, line, column)` entries. It visits every child, even when the parent has no applicable rule. At each node it looks up only rules indexed under that node's class name.
5. **Apply anchor predicates.** An unnarrowed anchor matches its node type directly. A narrowed anchor requires either equality with its declared `value`, or a truthy attribute when no value is declared. For example, the star-import rule matches an `alias` whose `name` equals `"*"`; it does not ban ordinary `from` imports.
6. **Collect diagnostics.** Findings are deduplicated in a set and sorted before returning, so traversal order does not determine diagnostic order. Each finding includes its path, position, rule identifier, slug, status and guidance.

The public `check_source` API parses a string and uses the same indexed tree checker. If no index is supplied, it builds one for that call. A supplied index determines which rules are considered, so callers reusing one must build it for the intended rules and restricted mode.

## Why it is faster

Previously, checking a file walked its entire AST separately for each applicable rule: nine traversals for the current banned rules, and more when restricted constructs were requested. Both implementations parse a file only once; the improvement is in matching, not parsing.

The new implementation replaces those repeated walks with a node-type lookup during one walk. Ignoring parsing and diagnostic collection, the old approach performs roughly `nodes × active rules` traversal work. The new approach performs `nodes + relevant rule checks`, plus index construction once per CLI invocation. It still checks every relevant predicate; it does not skip subtrees or weaken rules.

This particularly helps large inputs and runs over many files. For a small single file, Python startup and imports can cost much more than checking, so a faster matching loop may barely change elapsed CLI time. No Rust extension or additional runtime dependency is needed.

## Behaviour and limits

- Nodes with their own AST location use it. Nodes without one, such as operators and contexts, inherit the nearest enclosing location. Reported columns are CPython's UTF-8 byte offsets plus one, not Unicode display columns.
- The matcher retains the original equality/truthiness semantics. Regression tests compare the indexed checker with an independent legacy implementation on examples, registry snippets and position/narrowing cases.
- The CLI comparison benchmark also verifies identical stdout, stderr and exit status against the original checker.
- Exit status remains 0 for no banned findings, 1 for banned findings, and 2 for a checking error. Other readable files may still have been checked when one file fails.
- `--restricted` lists anchored constructs for manual review; it does not evaluate their prose conditions and does not make them failures. A clean run is not proof of full subset conformance.

## Reproducing the measurements

Run from the repository root after `uv sync`:

```sh
uv run python benchmarks/cli_compare.py --samples 5
uv run python benchmarks/compare.py --samples 20
uv run python -m benchmarks --samples 5 --profile
```

### End-to-end comparison

`cli_compare.py` extracts the original checker from Git revision `f60e3e5` by default, so that revision must be present in the clone. Use `--baseline-ref REV` to select another compatible baseline. Both scripts run in fresh Python subprocesses with the same current rules snapshot and identical input paths. Timings include interpreter startup, imports, file reading, parsing, matching and captured diagnostic output.

It measures a representative example file, a synthetic 6,000-line file, and 100 copies of the representative example, each in default and restricted modes. It reports medians, uses at least three samples per workload, and verifies output equality. Fresh processes measure process startup, not cold operating-system disk caches.

An illustrative local run with three samples per workload produced:

| Workload | Original | Indexed | Speedup |
|---|---:|---:|---:|
| Small file | 43 ms | 42 ms | 1.04× |
| Small file, restricted | 50 ms | 46 ms | 1.10× |
| Synthetic 6,000 lines | 144 ms | 70 ms | 2.07× |
| Synthetic 6,000 lines, restricted | 278 ms | 76 ms | 3.65× |
| 100 example copies | 257 ms | 89 ms | 2.87× |
| 100 example copies, restricted | 548 ms | 97 ms | 5.67× |

Times are rounded; speedups were calculated before rounding. These small local samples illustrate the effect, not a performance guarantee. Repeat on your machine and representative repositories before drawing capacity conclusions.

### API comparison and phase measurements

`compare.py` compares the legacy matching implementation in `benchmarks/legacy.py` with the public optimized API. Its timings exclude process startup and file reading but include parsing. These numbers must not be presented as end-to-end CLI speedups.

Despite its historical name, `benchmarks/baseline.py` (also run by `python -m benchmarks`) measures the **current** checker, not the original revision. Its many-file workload uses tiny assignment files, unlike the representative copies in `cli_compare.py`, so the two workloads are not interchangeable.

With `--profile`, it separately measures parsing, index construction, traversal without matching, checking a pre-parsed tree, string rendering and a full API call. These measurements overlap: checking a pre-parsed tree includes traversal, predicate matching, finding construction and sorting. Do not add the phase times together. Rendering on the clean default-mode example has almost no work; violation-heavy or restricted output may cost more. File writes and terminal display are not included in the isolated rendering measurement.
