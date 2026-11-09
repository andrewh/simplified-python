"""Summarise a web server access log by status class, bytes sent, and busiest paths."""

from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass

SAMPLE_LOG = """\
2026-11-09T10:00:01 GET /index.html 200 512
2026-11-09T10:00:02 GET /about.html 200 1024
2026-11-09T10:00:04 GET /old-page 301 0
2026-11-09T10:00:05 POST /login 401 64
this line is not a log entry
2026-11-09T10:00:07 GET /index.html 200 512
2026-11-09T10:00:09 GET /report 500 128
2026-11-09T10:00:10 GET /index.html 304 0
"""


@dataclass(frozen=True)
class Request:
    method: str
    path: str
    status: int
    size: int


def parse_line(line: str) -> Request | None:
    match line.split():
        case [_, method, path, status, size] if status.isdigit() and size.isdigit():
            return Request(method, path, int(status), int(size))
        case _:
            return None


def parse_log(text: str) -> Iterator[Request]:
    for line in text.splitlines():
        request = parse_line(line)
        if request is not None:
            yield request


def status_class(status: int) -> str:
    match status // 100:
        case 2:
            return "success"
        case 3:
            return "redirect"
        case 4:
            return "client error"
        case 5:
            return "server error"
        case _:
            return "unknown"


def summarise(requests: list[Request]) -> dict[str, int]:
    return dict(Counter(status_class(request.status) for request in requests))


def busiest_paths(requests: list[Request], limit: int) -> list[tuple[str, int]]:
    counts = Counter(request.path for request in requests)
    return counts.most_common(limit)


def main() -> None:
    requests = list(parse_log(SAMPLE_LOG))
    total = sum(request.size for request in requests)
    print(f"{len(requests)} requests, {total} bytes")
    for name, count in sorted(summarise(requests).items()):
        print(f"  {name:<13} {count}")
    print("busiest paths:")
    for path, count in busiest_paths(requests, 2):
        print(f"  {count:>3}  {path}")


if __name__ == "__main__":
    main()
