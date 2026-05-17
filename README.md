# forum-etl

ETL экспорта топиков форума из `data/` в структурированный JSON и далее в эмбеддинги / Qdrant (RAG).

Техническое описание и контракт данных: [docs/vision.md](docs/vision.md). План работ по этапам: [docs/tasks.md](docs/tasks.md).

## Окружение Python (этап 2)

Нужен [uv](https://docs.astral.sh/uv/). В корне репозитория:

```bash
uv sync
```

Проверка зависимостей:

```bash
uv run python -c "import yaml; import rapidfuzz; print('ok')"
```

Справка CLI:

```bash
uv run forum-etl --help
```

В элементах **`posts[].quotes`** в JSON **не попадает** служебная первая строка «`<автор> писал(а):`» (в том числе шаблон **`%username% писал(а):`**); полный контракт — [docs/vision.md](docs/vision.md).

Этап 5 — **JSON на топик** (UTF-8): `topic_id`, `title`, `posts[]` в порядке `post_index`. По умолчанию файл создаётся как `out/topic_<id>.json` (каталог `out/` создаётся при необходимости).

```bash
uv run forum-etl data/topic_2036930.txt
uv run forum-etl data/topic_2036930.txt out/custom.json
uv run forum-etl data/topic_2036930.txt out
```

В stdout — краткая сводка и **абсолютный путь** к записанному JSON. При ошибке разбора YAML/постов — код **1**, отчёт в stderr; ошибка записи — **1** и сообщение в stderr.

## Репозиторий (этап 1)

Если каталога `.git` ещё нет:

```bash
cd /path/to/forum-etl
git init -b main
git add .gitignore docs/ README.md
git status
```

Дальше — добавьте остальные файлы проекта по желанию (каталог `data/` может быть тяжёлым; при необходимости оформите его отдельно или через Git LFS).

### GitHub

1. Создайте пустой репозиторий на GitHub (без README/license, если вы уже инициализировали локально).
2. Привяжите `origin` и отправьте ветку:

```bash
git remote add origin git@github.com:<USER>/<REPO>.git
git push -u origin main
```

Либо: `gh repo create forum-etl --private --source=. --remote=origin --push` (при настроенном GitHub CLI).
