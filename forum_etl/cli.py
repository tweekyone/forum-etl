"""Точка входа CLI."""

from __future__ import annotations

import sys
from pathlib import Path

from forum_etl.export_json import export_topic_to_json, resolve_output_path
from forum_etl.iter1 import build_posts_iter1
from forum_etl.iter2 import apply_iter2_to_posts
from forum_etl.iter3 import apply_quotes_out
from forum_etl.iter4 import apply_quotes_in
from forum_etl.topic_file import TopicFileError, format_topic_file_error, load_topic_bundle


def _export_topic_file(topic_txt: Path, out_base: Path) -> tuple[str, object, int, Path]:
    """
    Читает один topic_*.txt, прогоняет итерации 1–4 (quotes_out, quotes_in), пишет JSON.
    out_base — путь к .json или каталог, куда кладётся topic_<topic_id>.json.
    """
    bundle = load_topic_bundle(topic_txt)
    src = topic_txt.resolve()
    posts = build_posts_iter1(bundle, src)
    apply_iter2_to_posts(posts)
    apply_quotes_out(posts)
    apply_quotes_in(posts)
    tid = str(bundle.topic["topic_id"]).strip()
    out_path = resolve_output_path(out_base, tid)
    export_topic_to_json(bundle, posts, out_path, topic_source=src)
    return tid, bundle.topic.get("title"), len(posts), out_path.resolve()


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        print(
            "usage: forum-etl <path-to-topic.txt|DIR> [OUT]\n"
            "       forum-etl --help\n"
            "\n"
            "Один файл: OUT — .json или каталог (по умолчанию out/topic_<id>.json).\n"
            "Каталог: обрабатываются все topic_*.txt; OUT — каталог вывода (по умолчанию out/).\n"
            "Код выхода: 0 — ок, 1 — ошибка разбора/записи, 2 — неверные аргументы.",
            file=sys.stderr,
        )
        raise SystemExit(2)
    if argv[0] in ("-h", "--help"):
        print(
            "forum-etl — экспорт топика(ов) в JSON (итерации 1–4: разбор, нормализация, quotes_out, quotes_in).\n"
            "\n"
            "  forum-etl data/topic_2036930.txt\n"
            "  forum-etl data/topic_2036930.txt out/custom.json\n"
            "  forum-etl data/topic_2036930.txt out/\n"
            "  forum-etl data/\n"
            "  forum-etl data/ out/\n",
        )
        raise SystemExit(0)

    if len(argv) > 2:
        print("forum-etl: слишком много аргументов.", file=sys.stderr)
        raise SystemExit(2)

    in_path = Path(argv[0])
    out_arg = Path(argv[1]) if len(argv) == 2 else None

    if in_path.is_dir():
        out_dir = out_arg if out_arg is not None else Path("out")
        if out_dir.suffix.lower() == ".json":
            print(
                "forum-etl: если первый аргумент — каталог, второй должен быть каталогом вывода, "
                "а не файлом .json.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        files = sorted(in_path.glob("topic_*.txt"))
        if not files:
            print(
                f"forum-etl: в {in_path.resolve()} нет файлов topic_*.txt.",
                file=sys.stderr,
            )
            raise SystemExit(2)
        for topic_file in files:
            try:
                tid, title, n_posts, out_resolved = _export_topic_file(topic_file, out_dir)
            except TopicFileError as e:
                print(format_topic_file_error(e), file=sys.stderr)
                raise SystemExit(1) from e
            except OSError as e:
                print(f"не удалось записать результат для {topic_file}: {e}", file=sys.stderr)
                raise SystemExit(1) from e
            print(
                f"topic_id={tid!r} title={title!r} posts={n_posts} -> {out_resolved}",
            )
        raise SystemExit(0)

    out_base = out_arg if out_arg is not None else Path("out")
    try:
        tid, title, n_posts, out_resolved = _export_topic_file(in_path, out_base)
    except TopicFileError as e:
        print(format_topic_file_error(e), file=sys.stderr)
        raise SystemExit(1) from e
    except OSError as e:
        print(f"не удалось записать {out_base}: {e}", file=sys.stderr)
        raise SystemExit(1) from e

    print(
        f"topic_id={tid!r} title={title!r} posts={n_posts} -> {out_resolved}",
    )
    raise SystemExit(0)


if __name__ == "__main__":
    main()
