.PHONY: install run upload-manifest test lint format typecheck help

help:
	@echo "使用可能なコマンド:"
	@echo "  make install                               依存関係をインストール (uv sync)"
	@echo "  make run                                   Streamlit アプリを起動"
	@echo "  make upload-manifest FILE=<path> [DEST=<subpath>]  pair_manifest.jsonl を S3 へアップロード"
	@echo "  make test                                  pytest でテストを実行"
	@echo "  make lint                                  ruff でコードをチェック"
	@echo "  make format                                ruff でコードを自動修正"
	@echo "  make typecheck                             mypy で型チェック"
	@echo ""
	@echo "例:"
	@echo "  make upload-manifest FILE=data/pair_manifest.jsonl"
	@echo "  make upload-manifest FILE=data/retry01/pair_manifest.jsonl DEST=retry01/pair_manifest.jsonl"

install:
	uv sync --group dev

run:
	uv run streamlit run app.py

upload-manifest:
ifndef FILE
	$(error FILE が未指定です。例: make upload-manifest FILE=data/sample/pair_manifest.jsonl)
endif
	uv run python scripts/upload_manifest.py $(FILE) $(if $(DEST),--dest $(DEST),)

test:
	uv run pytest -v

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .
	uv run ruff check --fix .

typecheck:
	uv run mypy annotation_app
