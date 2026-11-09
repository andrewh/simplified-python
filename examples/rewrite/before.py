"""A grade report in full Python. This file does NOT conform to the subset.

after.py is the same program rewritten in the subset, with identical output.
Each comment names the rule that the line breaks; see docs/subset.md.
"""

from statistics import *  # SP601 no-star-import

PASS_MARK = 50
ROWS = ["ada,72,88,95", "brian,40,55,38", "chen,61,59,70", "dee,100,90,85", "eve,70,x"]
failures = 0

grade_of = lambda score: "A" if score >= 70 else "B" if score >= 60 else "C" if score >= PASS_MARK else "F"  # SP116, SP114


def parse(rows):
    students = {}
    for row in rows:
        name, *marks = row.split(",")  # SP115 starred-unpacking
        try:
            students[name] = [int(mark) for mark in marks]
        except:  # SP702 typed-except-handlers
            print(f"skipping {name}: bad mark")
    return students


def count_failure():
    global failures  # SP208 no-global-or-nonlocal
    failures += 1


def report(students):
    for name, marks in students.items():
        if 0 <= (average := mean(marks)) < PASS_MARK:  # SP110 single-comparison, SP118 no-walrus
            count_failure()
        print(f"{name:<8} {average:5.1f} {grade_of(average)}")
    for name, marks in students.items():
        if max(marks) == 100:
            print(f"top mark: {name}")
            break
    else:  # SP304 no-loop-else
        print("no top marks")


if __name__ == "__main__":
    report(parse(ROWS))
    print(f"{failures} below the pass mark")
