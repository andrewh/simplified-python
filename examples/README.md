# Examples

Small, runnable programs written in the simplified Python subset. Each one runs on stock Python 3.14 with `python examples/<file>.py`.

| Example | Shows |
|---|---|
| [`inventory.py`](inventory.py) | dataclasses, a custom exception, `try` / `except`, a single-clause comprehension, a lambda as a `key=` argument |
| [`log_summary.py`](log_summary.py) | `match` with sequence patterns and guards, a generator, `Counter`, f-string formatting |
| [`config_loader.py`](config_loader.py) | `@classmethod` and `@property`, `with`, `raise ... from ...`, a `type` alias, annotations |
| [`rewrite/before.py`](rewrite/before.py) | the same grade report in full Python: **does not conform**, and each violation is marked with its rule |
| [`rewrite/after.py`](rewrite/after.py) | that grade report rewritten in the subset, with identical output |

`tests/test_examples.py` checks that every example runs, and that the conforming examples contain no banned construct. It also checks that `before.py` and `after.py` print the same output. Conditions on restricted rules are still prose until a checker exists, so the examples are reviewed by hand against them.

Example files in this directory must conform to the subset. The exception is `rewrite/before.py`.
