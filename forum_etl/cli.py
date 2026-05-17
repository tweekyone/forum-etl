"""Точка входа CLI; полный разбор топиков — этапы 3–5."""

import sys


def main() -> None:
    print(
        "forum-etl: пайплайн в разработке. Этап 2 — зависимости установлены.\n"
        "Дальше: см. docs/tasks.md (этапы 3–5).",
        file=sys.stderr,
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()
