SHELL=/bin/bash

venv:
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt

install:
	unset CONDA_PREFIX && \
	source .venv/bin/activate && maturin develop

install-release:
	unset CONDA_PREFIX && \
	source .venv/bin/activate && maturin develop --release

pre-commit:
	cargo +nightly fmt --all && cargo clippy --all-features
	.venv/bin/python -m ruff check . --fix --exit-non-zero-on-fix
	.venv/bin/python -m ruff format witt_strutil tests
	.venv/bin/mypy witt_strutil tests

test:
	.venv/bin/python -m pytest tests