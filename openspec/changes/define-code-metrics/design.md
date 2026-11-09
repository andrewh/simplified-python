# Design: Review-Cost Code Metrics

## Context

`define-python-subset` establishes a registry that classifies all 109 concrete constructs of the CPython 3.14 grammar as `allowed`, `restricted`, or `banned`, with total coverage provable against the `ast` module. That model has a known blind spot, recorded as an open question in its design: it can only match constructs that *appear*. It cannot express a property of a region measured against a number, so it cannot say anything about a function that nests six levels deep or runs for 300 lines.

Metrics fill that gap and answer to the same principle the construct rules cite — bounded reading cost. They are, however, a different kind of object, and three differences drive this design:

1. **No provable completeness.** CPython enumerates the grammar, so construct coverage can be checked. There is no enumerable universe of metrics, so the set is curated and the reference must say so rather than implying parity.
2. **No agreed definitions.** `radon`, `mccabe`, ruff's `C901`, and Sonar disagree about `and`/`or`, `elif`, `except`, comprehension `if`s, and `match` cases, so they return different numbers for the same function. A threshold is only meaningful alongside an exact counting rule.
3. **Thresholds are empirical.** A number chosen by folklore is exactly the arbitrary taste the principles were introduced to eliminate.

The measurement corpus is settled by convenience of the best kind: the CPython standard library on the pinned interpreter provides 655 candidate files already on disk, with no network access and no vendoring.

## Prior Art

**Existing default thresholds to calibrate against, not in isolation.** Several widely deployed tools already gate on metrics this catalogue defines, and their defaults are a sanity check for task 5.3's calibration rather than a substitute for it:

| Metric | Tool | Documented default |
|---|---|---|
| Cyclomatic complexity | flake8 `C901` / [ruff `C901`](https://docs.astral.sh/ruff/rules/complex-structure/) | 10 |
| Too many branches | [ruff `PLR0912`](https://docs.astral.sh/ruff/rules/#pylint-pl) | 12 |
| Too many arguments | ruff `PLR0913` | 5 |
| Too many statements | ruff `PLR0915` | 50 |
| Too many nested blocks | ruff `PLR1702` | 5 |
| Too many return statements | ruff `PLR0911` | 6 |
| Cognitive complexity | [flake8-cognitive-complexity](https://github.com/Melevir/flake8-cognitive-complexity) | 7 |
| Function length / params / branches | [flake8-functions](https://github.com/best-doctor/flake8-functions) | ~50 lines, 5 params, 12 branches |
| Cyclomatic complexity risk bands | [NIST SP 500-235](https://nvlpubs.nist.gov/nistpubs/Legacy/SP/nistspecialpublication500-235.pdf) | 1–10 simple, 11–20 moderate, 21–50 high, 50+ untestable |

Notably, `PLR1702` already gates nesting depth with a default of 5 — task 5 should diff `SM01`'s counting rule against it explicitly (does `elif` add depth? does `match`?) rather than treat nesting depth as an unprecedented measure. [Radon](https://radon.readthedocs.io/) supplies the underlying cyclomatic-complexity computation for both `xenon` and `wily`, using letter grades `A` (1–5) through `F` (41+); `xenon`'s CI defaults require grade `A` project-wide, which is a considerably stricter posture than "generous, corpus-calibrated" thresholds and is not adopted here.

**Cognitive complexity is a deliberate citation, not a reimplementation.** `SM02`'s counting rules — increment per branch, additional increment per nesting level, a run of the same boolean operator counted once, `else` free — are drawn from [SonarSource's Cognitive Complexity whitepaper (Campbell, 2017)](https://www.sonarsource.com/docs/CognitiveComplexity.pdf). Sonar's own implementation is documented to vary by language, and `flake8-cognitive-complexity`'s counting behavior is independently plugin-specific, so no third-party implementation is authoritative enough to claim numerical equivalence with. `SM02`'s reference implementation and test vectors (Requirement: Counting rules are pinned by test vectors) are what make this project's definition exact; the whitepaper is cited for the principle, not treated as a specification this project implements.

**The no-suppression policy is a deliberate departure from every precedent found, not an oversight.** MISRA permits documented deviations, CERT documents exceptions, ESLint has `eslint-disable`, SonarQube has issue suppression, and Ruff has `# noqa` — every rule-based standard surveyed ships an escape hatch. This catalogue's Requirement: Catalogue defines no suppression affordance is therefore not "the industry norm"; it is a considered bet that a generous, corpus-calibrated threshold with zero escape hatch keeps every violation meaningful, at the cost of occasionally forcing a threshold renegotiation instead of a one-line waiver. Calibration (Section 5 of `tasks.md`) is what has to carry that bet — if thresholds are set too tight, the absence of an escape hatch will surface as real friction rather than as a theoretical risk.

**No published methodology fixes "the" correct percentile.** NIST's risk bands are guidance, not a calibration procedure, and Code Complete's routine-size heuristics are heuristic rather than a reproducible statistical method. The corpus-percentile-and-date approach in Requirement: Thresholds record their calibration is a defensible engineering method but not one this project can cite as externally validated; task 5.3's per-metric percentile choice should be treated as this project's own judgment call, recorded so it can be argued with, not as the application of an established standard.

## Goals / Non-Goals

**Goals:**

- Five metrics that map to distinct review costs, each with a threshold a reviewer can cite.
- Every metric defined by an executable reference implementation, with test vectors pinning the cases where established tools disagree.
- Thresholds derived from a measured distribution, with corpus, percentile, and date recorded so the number can be argued with.
- Metrics rendered into the same reference document as construct rules, sharing its staleness guarantee and citation affordance.

**Non-Goals:**

- Cyclomatic complexity as a gate (see the decision below). It may later be reported without a threshold; that is not this change.
- The checker that computes metrics over a real codebase. This change defines the measures it will call.
- Waivers, suppression comments, severities, advisory tiers, or per-project configuration.
- Halstead measures, maintainability indices, and coupling metrics such as fan-in and fan-out — these measure properties of a system, not the reading cost of a diff.
- Class-level and module-level metrics in the first release (see Open Questions).

## Decisions

### A separate catalogue with its own `SM` namespace

Metrics live in `subset/metrics.toml` with their own schema and identifiers of the form `SM01`. They are called metrics, never rules.

The distinct term is what keeps this change free of amendments to `subset-rules` and `subset-reference`: those specs govern rules under `subset/rules/` and the reference's rule entries, so every requirement stays true as written and nothing has to be renegotiated. The distinct prefix means a citation carries its kind — `SM01` in a review comment is visibly a threshold rather than a construct verdict.

- *Rejected: a `kind` discriminator inside the construct rule schema.* A discriminated union in TOML means fields that are required for one kind and forbidden for another, which is precisely the sort of conditional data structure that is hard to review — self-defeating in this project.
- *Rejected: sharing the `SP` namespace via a reserved `SP0xx` block.* Workable, but it requires editing the other change's manifest and hides the kind at the point of citation.

*Shared deliberately:* the principles file, the identifier ledger, the reference document, and the validation entry point. Those are the things a reviewer experiences as one system.

### Nesting depth carries the hard limit; cyclomatic complexity carries none

McCabe complexity is decision points plus one, so a flat twelve-case `match` scores 13 and twelve nested `if` statements also score 13. For a project whose construct rules mark flat `match` as exemplary, a metric that cannot tell those apart is measuring the wrong thing: it measures the number of independent test paths, which is a testing concern, not reading cost.

Nesting depth is chosen for the hard limit because it is unambiguous to compute and, unlike every other metric here, it **cannot be satisfied by relocation**. A length or complexity limit can be met by extracting code into helpers; nesting depth can only be met by flattening — guard clauses, early returns, inverted conditions. The metric therefore pushes toward the specific rewrite that genuinely helps a reviewer.

Cognitive complexity is the aggregate companion: it charges for each branch and charges more when that branch sits inside other branches, which is the shape of the cost nesting depth measures only at its peak.

- *Rejected: McCabe with a threshold.* Penalises the flat branching the subset encourages.
- *Deferred, not rejected: McCabe reported without a threshold.* Useful for comparison with other tools, but a reported number with no consequence is decoration until someone asks for it.

### Cognitive complexity is defined locally, not borrowed

The measure increments once per branch-introducing construct and adds one further increment per level of nesting. A run of the same boolean operator counts once, `else` is free, and `elif` adds one increment without deepening.

This is inspired by SonarSource's cognitive complexity, but the catalogue will **not** claim equivalence. Their specification is prose plus a proprietary implementation; asserting parity we do not test would be exactly the kind of unverified claim this repository is built to avoid. The implementation and its vectors are the definition, and the reference says values are not comparable across tools.

### Two length metrics, because there are two costs

Physical line span (`end_lineno - lineno + 1`) measures what a reviewer scrolls through. Statement count measures structural size and is immune to reformatting. A single statement spread over 40 lines costs 40 lines of scrolling and is one statement; both facts are true, and collapsing them into one number would misrepresent one of them.

The cost of two metrics is two thresholds to calibrate and the risk of a reviewer wondering which one matters. Mitigation: each rationale names the cost it measures, and both values are always reported together. The alternative — one metric — would have required choosing between honesty about formatting and honesty about scrolling.

*Note a tension worth stating:* line span depends on formatting, which `define-python-subset` deliberately placed out of scope for its AST-anchored rules. Line span is the one measure here that a formatter can move without changing code. It is included anyway because scrolling distance is a real cost, and the statement count metric exists precisely so that the format-independent view is also available.

### Reference implementations are the normative definition

`src/simplified_python/metrics.py` holds pure functions from an AST region to a non-negative integer, registered in a mapping keyed by metric identifier. Validation checks the mapping in both directions so a metric cannot exist without an implementation, nor an implementation without a threshold.

Binding the definition to code is what makes the counting rule exact. The prose `counting_rule` field remains, because a reviewer needs to read the intent, but where prose and implementation disagree the vectors decide — and a vector failure is a build failure.

### Vectors live in their own file

`subset/metric-vectors.toml`, keyed by metric identifier. Vectors are test data that will grow to perhaps twenty snippets per metric; inlining them would bury the eight fields a reviewer actually reads in the catalogue.

- *Rejected: vectors inline in the metric record.* Keeps the counting rule next to its examples, which is genuinely nicer at three vectors and unreadable at twenty.

The catalogue keeps one short worked example per metric for the reference document; the exhaustive vectors are test data.

### Calibration corpus: the standard library of the pinned interpreter

655 files, already on disk, fixed by the interpreter version, no network. Re-running the calibration on the pinned interpreter reproduces the distribution exactly, which is what makes the recorded provenance meaningful.

- *Rejected: a set of well-regarded third-party repositories.* Better stylistic role models, but they require vendoring or network access and they drift, which would make "the percentile we measured" unreproducible.

*Accepted limitation, stated plainly:* the standard library is not subset-conformant, contains decades-old code, and includes modules written under constraints that no longer apply. Calibrating against it risks importing its habits. It is therefore used as a **distribution reference** — to learn what values are ordinary and which are outliers — and not as a target. The honest follow-up is to re-calibrate once a meaningful body of subset-conformant code exists, and the recorded date exists so that re-calibration is visible.

### Thresholds are generous by construction

Because the catalogue defines no suppression affordance, a threshold set at the median would force contorted code with no escape. Thresholds are therefore set high enough that only genuine outliers trip — the calibration task reports the distribution and each threshold records the percentile it was set at.

This is a deliberate trade of strength for honesty. A tight threshold with a waiver mechanism becomes a rubber stamp; a generous threshold with no waiver keeps every violation meaningful. The follow-on risk is a threshold so generous it never fires, which the calibration report makes visible: if no file in the corpus would trip a threshold, it is decoration.

## Risks / Trade-offs

- **Every metric except nesting depth is gameable by extraction.** Ten fifteen-line functions that each call the next are worse to review than one linear 150-line function. → Thresholds are framed as tripwires that force a conversation, not as correctness properties, and the reference says so. Nesting depth is the limit that resists this, which is why it carries the hard gate.
- **Generous thresholds may never fire.** → The calibration report states, per metric, how much of the corpus would trip it. A threshold that flags nothing is reported as such and re-argued.
- **Calibrating on the standard library imports the standard library's habits.** → Used as a distribution reference only; the provenance record carries a date so staleness is visible, and re-calibration against subset-conformant code is the recorded follow-up.
- **A locally defined cognitive complexity is not comparable to any other tool's.** → The reference states this explicitly; the vectors are the specification; no parity is claimed.
- **Two length metrics can look like indecision.** → Each states the cost it measures, and both are always reported. A reviewer is never asked to pick.
- **The metric set is curated, so it has no completeness guarantee.** → Stated in the metrics section of the reference, directly contrasted with provable construct coverage, so readers do not transfer confidence from one to the other.
- **Region boundaries are where reproducibility usually breaks.** Whether a nested function's body counts toward its enclosing function changes values substantially. → Region definitions are a specified requirement with their own scenarios, and every metric declares its region.

## Migration Plan

This change is additive and depends on `define-python-subset` being implemented. Sequencing matters in one respect: thresholds should be calibrated **after** the construct rules are authored, because bans on nested definitions and limits on comprehensions already remove some of the complexity a metric would otherwise catch. Calibrating first would set thresholds against a distribution the subset itself makes unreachable.

Rollback is a file deletion plus a regeneration of the reference; no construct rule or identifier depends on a metric.

## Open Questions

- **What percentile?** p95 and p99 imply very different regimes — p99 on the standard library may be so permissive that nothing in normal code ever trips. The calibration report should be produced before this is settled, per metric rather than globally.
- **Does a nested function's body count toward its enclosing function's span and statement count?** It interacts directly with `define-python-subset`'s restriction on nested definitions, and the answer changes both length metrics materially. Needs a verdict before the implementations are written.
- **Are class-level and module-level metrics wanted?** Method count per class and statement count per module are the obvious candidates, and module length in particular is a real review cost. Deferred to keep the first release to regions with one unambiguous definition.
- **Should parameter count distinguish keyword-only parameters?** A function with eight keyword-only parameters reads very differently from one with eight positional ones, and `define-python-subset` may already restrict `*args` and `**kwargs` in a way that changes the calculus.
- **Is line span measured before or after formatting?** The repository has no formatter and no line-length rule, so line span is currently measured on whatever the author wrote. If a formatter arrives later, this threshold's calibration is invalidated.
