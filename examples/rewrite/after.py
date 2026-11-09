"""A grade report in the simplified Python subset.

This is before.py rewritten to conform to the subset. Both print the same output.
"""

from statistics import mean

PASS_MARK = 50
ROWS = ["ada,72,88,95", "brian,40,55,38", "chen,61,59,70", "dee,100,90,85", "eve,70,x"]


def grade_of(score: float) -> str:
    if score >= 70:
        return "A"
    if score >= 60:
        return "B"
    if score >= PASS_MARK:
        return "C"
    return "F"


def parse(rows: list[str]) -> dict[str, list[int]]:
    students = {}
    for row in rows:
        parts = row.split(",")
        name = parts[0]
        try:
            students[name] = [int(mark) for mark in parts[1:]]
        except ValueError:
            print(f"skipping {name}: bad mark")
    return students


def report(students: dict[str, list[int]]) -> int:
    failures = 0
    for name, marks in students.items():
        average = mean(marks)
        if average < PASS_MARK:
            failures += 1
        print(f"{name:<8} {average:5.1f} {grade_of(average)}")
    top = [name for name, marks in students.items() if max(marks) == 100]
    if top:
        print(f"top mark: {top[0]}")
    else:
        print("no top marks")
    return failures


def main() -> None:
    failures = report(parse(ROWS))
    print(f"{failures} below the pass mark")


if __name__ == "__main__":
    main()
