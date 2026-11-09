"""Generate the agent skill in skills/simplified-python/ from the rule registry.

The generated files are never edited by hand: change the registry under
subset/ (or the template in skills/SKILL.template.md) and run
``python -m simplified_python.skill`` to regenerate them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from simplified_python import check, reference
from simplified_python.registry import DEFAULT_ROOT, Registry, _validate, format_errors

COMMAND = "python -m simplified_python.skill"
REPO = DEFAULT_ROOT.parent
DEFAULT_TEMPLATE = REPO / "skills" / "SKILL.template.md"
DEFAULT_OUTPUT = REPO / "skills" / "simplified-python"
EXAMPLES = REPO / "examples" / "rewrite"


def all_rules(registry: Registry):
    return [rule for category in registry.categories for rule in registry.rules_in(category.name)]


def render_digest(registry: Registry) -> dict[str, str]:
    rules = all_rules(registry)

    def link(rule) -> str:
        return f"[{rule.id}](reference.md#{reference.anchor_id(rule.id)}) `{rule.slug}`"

    return {
        "PRINCIPLES": "\n".join(f"- **{p.id} {p.name}**: {p.statement}" for p in registry.principles),
        "BANNED": "\n".join(f"- {link(r)}: {r.construct} *Instead:* {r.replacement}" for r in rules if r.status == "banned"),
        "RESTRICTED": "\n".join(f"- {link(r)}: {r.construct} *Condition:* {r.condition}" for r in rules if r.status == "restricted"),
        "ALLOWED": ", ".join(f"`{r.slug}`" for r in rules if r.status == "allowed"),
        "PRERELEASE": "\n".join(reference.PRERELEASE_NOTICE),
        "RULESET_VERSION": str(registry.ruleset_version),
        "PYTHON_VERSION": registry.python_version,
    }


def render_skill(registry: Registry, template: str) -> str:
    text = template
    for name, value in render_digest(registry).items():
        text = text.replace("{{" + name + "}}", value)
    if "{{" in text:
        raise ValueError("the template contains a placeholder the generator does not know: " + text[text.index("{{") :].split("}}")[0] + "}}")
    return text


def render_rules(registry: Registry) -> str:
    rules = []
    for rule in all_rules(registry):
        if rule.status == "allowed":
            continue
        anchor = {"nodes": list(rule.anchor.nodes)}
        if rule.anchor.attribute is not None:
            anchor["attribute"] = rule.anchor.attribute
        if rule.anchor.value is not None:
            anchor["value"] = rule.anchor.value
        rules.append(
            {
                "id": rule.id,
                "slug": rule.slug,
                "status": rule.status,
                "construct": rule.construct,
                "condition": rule.condition,
                "replacement": rule.replacement,
                "anchor": anchor,
            }
        )
    data = {"ruleset_version": registry.ruleset_version, "python_version": registry.python_version, "rules": rules}
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def outputs(registry: Registry, template: str, output: Path) -> dict[Path, bytes]:
    texts = {
        "SKILL.md": render_skill(registry, template),
        "reference.md": reference.render(registry),
        check.RULES_NAME: render_rules(registry),
        "check.py": Path(check.__file__).read_text(encoding="utf-8"),
        "examples/before.py": (EXAMPLES / "before.py").read_text(encoding="utf-8"),
        "examples/after.py": (EXAMPLES / "after.py").read_text(encoding="utf-8"),
    }
    return {output / name: text.encode("utf-8") for name, text in texts.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=COMMAND, description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="registry directory (default: subset/)")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE, help="SKILL.md template (default: skills/SKILL.template.md)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="skill directory to write (default: skills/simplified-python/)")
    parser.add_argument("--check", action="store_true", help="fail if the skill is out of date instead of writing it")
    args = parser.parse_args(argv)
    registry, errors = _validate(args.root, None)
    if errors:
        print(f"{format_errors(errors)}\n\nThe registry is invalid; nothing was written.", file=sys.stderr)
        return 1
    try:
        files = outputs(registry, args.template.read_text(encoding="utf-8"), args.output)
    except (OSError, ValueError) as exc:
        print(f"{args.template}: {exc}", file=sys.stderr)
        return 1
    if args.check:
        stale = [path for path, data in files.items() if not path.exists() or path.read_bytes() != data]
        extra = sorted(p for p in args.output.rglob("*") if p.is_file() and p not in files) if args.output.exists() else []
        for path in stale:
            print(f"{path} is out of date with the registry. Run `{COMMAND}` and commit the result.", file=sys.stderr)
        for path in extra:
            print(f"{path} is not generated by `{COMMAND}`; remove it.", file=sys.stderr)
        if not (stale or extra):
            print("skill is up to date")
        return 1 if stale or extra else 0
    for path, data in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
