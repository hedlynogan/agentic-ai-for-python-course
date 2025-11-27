# Junie Rules for PyCharm

Last Updated: November 27, 2025

Goal: Apply and operationalize the guidance from `junies-cursor-rules.md` specifically for teams using PyCharm. This document lists concrete PyCharm settings and light project tweaks to ensure the rules are consistently enforced.

## TL;DR

- Python: Use 3.14+ interpreter; point PyCharm to the project `.venv` or `venv` you created (prefer `uv venv`).
- Formatting/Linting: Install the Ruff plugin; enable Ruff as formatter and linter, and run on-save.
- Testing: Set default test runner to `pytest` and configure `pytest.ini` (preferred over `pyproject.toml`).
- Imports: Use PyCharm import settings to keep `import module` style preferred; avoid auto-collapsing to `from module import name` unless for classes/exceptions.
- VCS: Enable pre-commit checks or at least run `ruff format` and `ruff check --fix` before commits; always `git pull` at session start.
- Web apps: Use ports ≥ 10000 in Run Configurations.
- Templates: Remove shebang from new Python file templates.

---

## 1) Interpreter and Environment

What to add/modify:
- Ensure Python 3.14 is installed and available at `/opt/homebrew/bin/python3.14` (macOS Apple Silicon/Intel via Homebrew):
  - Verify: `/opt/homebrew/bin/python3.14 -V` (expect `Python 3.14.x`).
  - If missing, install: `brew install python@3.14`.
  - If the binary is only at `$(brew --prefix)/opt/python@3.14/bin/python3.14`, either use that full path with uv or create a symlink: `ln -s /opt/homebrew/opt/python@3.14/bin/python3.14 /opt/homebrew/bin/python3.14`.
- Recreate the virtual environment with uv (outside PyCharm), targeting Python 3.14 explicitly:
  - Remove/backup the old venv if present: `rm -rf .venv` (ensure you’re in the project root).
  - Create: `uv venv --python /opt/homebrew/bin/python3.14 .venv` (or use the `.../opt/python@3.14/bin/python3.14` path).
  - Install deps:
    - Using requirements.txt: `uv pip install -r requirements.txt`
    - Or with piptools: `uv pip-compile requirements.piptools -o requirements.txt && uv pip install -r requirements.txt`
- In PyCharm:
  - Settings/Preferences → Project → Python Interpreter → Add → Existing environment → point to `.venv/bin/python` (macOS/Linux) or `.venv\Scripts\python.exe` (Windows).
  - Set Python language level to 3.14 for inspections: Settings → Editor → Inspections → Python → “Python version” and “Code compatibility”.

What to avoid/delete:
- Do not rely on system interpreter.
- Do not add shebangs; run via the venv or `uv run`.

## 2) Ruff (formatter + linter)

What to add/modify:
- Install the “Ruff” plugin for PyCharm (by Astral).
- Settings → Tools → Ruff:
  - Enable “Run Ruff on save”.
  - Enable “Use Ruff as formatter” (so “Reformat Code” uses Ruff).
  - Point configuration to project `ruff.toml` if present (otherwise plugin will auto-detect).
- Add a pre-commit step (optional but recommended):
  - `pipx install pre-commit` or add to dev deps via `uv pip install pre-commit`
  - Create `.pre-commit-config.yaml` with `ruff` and `ruff-format` hooks and enable with `pre-commit install`.

What to avoid/delete:
- Disable Black/autopep8 if previously configured as formatter to avoid conflicts with Ruff.

## 3) Imports behavior (align with Junie’s Import Style Rule)

Constraints from `junies-cursor-rules.md`:
- Functions: use namespace imports (e.g., `from pkg import module` then `module.func()`)
- Classes/Exceptions: direct imports (e.g., `from pkg.module import TheClass`)

What to add/modify in PyCharm:
- Settings → Editor → Code Style → Python → Imports:
  - Set “Prefer absolute imports”.
  - Uncheck any options that aggressively optimize imports into `from module import name` when not necessary.
  - Keep “from ... import *” disallowed (Inspection: Python → “Wildcard import” severity at least Warning).
- Enable Inspection: Python → “Unresolved references” to catch broken namespaces after refactors.

Notes:
- PyCharm cannot perfectly enforce the “functions via namespace” vs “classes direct import” rule. Treat this as a code review convention backed by Ruff import rules if you choose to enable them in `ruff.toml` (e.g., `I`/`isort`-compatible sorting only). Avoid auto-fixes that contradict the convention.

## 4) Testing with pytest

What to add/modify:
- Settings → Tools → Python Integrated Tools → Testing → Default test runner: `pytest`.
- Place configuration in `pytest.ini` at the project (preferred over `pyproject.toml`).
- Add a Run Configuration “pytest” with Working Directory = project root, and environment using the project venv.

What to avoid/delete:
- Remove/avoid legacy `unittest` run configs if pytest is standard here.

## 5) Project structure conventions

What to add/modify:
- Keep `pytest.ini` in repo root.
- Maintain `requirements.piptools` and `requirements-development.piptools` when present. Use `uv pip-compile` to regenerate lock/output files and keep them in sync with `pyproject.toml` if both exist.
- Prefer modules with functions over heavy OOP unless clearly justified.

What to avoid/delete:
- Duplicated config across `pyproject.toml` and `pytest.ini` (prefer `pytest.ini`).

## 6) Running web apps (ports and reload)

What to add/modify:
- Create Run Configuration(s) for Flask/Quart/FastAPI, set port to ≥ 10000 (e.g., 10080).
- Enable auto-reload where appropriate (e.g., Flask `--reload`). Assume server may already be running; avoid starting duplicate instances.

What to avoid/delete:
- Low-numbered ports (< 10000) that may collide or require elevated permissions.

## 7) Git/VCS practices in PyCharm

What to add/modify:
- At session start, use VCS → Git → Pull… (or terminal: `git pull`).
- Before committing: run `ruff format` and `ruff check --fix`. You can wire this via pre-commit, or a PyCharm “Before Commit” hook:
  - Settings → Version Control → Commit → Before Commit: Run External Tool → configure a tool that runs `ruff format && ruff check --fix`.
- Enable “Reformat code” (with Ruff) on commit if you have that integrated via the Ruff plugin.

What to avoid/delete:
- Do not auto-commit large refactors without running Ruff and tests.

## 8) Editor behavior and templates

What to add/modify:
- File and Code Templates → Python Script: remove any shebang (`#!/usr/bin/env python3`).
- Editor → General → On Save: enable “Reformat code” and “Optimize imports” only if it respects Ruff-as-formatter; otherwise rely on Ruff on-save.
- Editor → Code Style → Python: follow PEP8 defaults; prefer guard clauses and early returns (not a checked rule, but a convention).

What to avoid/delete:
- Conflicting formatters (Black/autopep8) when Ruff is the single source.

## 9) Terminals and tools

What to add/modify:
- Use the built-in Terminal for `uv` commands:
  - `uv pip install ...`
  - `uv pip-compile requirements.piptools -o requirements.txt`
- If your shell aliases `ls` to an enhanced version, use `/bin/ls` when exact behavior matters in scripts.

## 10) Change log

What to add/modify:
- If `change-log.md` exists, use it to summarize notable changes (feature additions, significant refactors). Keep entries concise and reference primary files/dirs.

---

## Summary: Add / Modify / Delete

Add
- Ruff plugin; enable Ruff formatter and on-save checks.
- PyCharm Run Configs with ports ≥ 10000 for web apps.
- pytest as the default test runner and a top-level `pytest.ini`.
- Pre-commit or Before Commit hook to run `ruff format` and `ruff check --fix`.

Modify
- Project interpreter → use project `.venv` created by `uv` (Python 3.14+).
- Import settings → prefer absolute imports; avoid auto-converting to `from module import name` unless needed.
- File templates → remove Python shebang.

Delete/Avoid
- Black/autopep8 formatter settings if Ruff is the formatter of record.
- System Python interpreters for this project.
- Low ports (<10000) in web Run Configs.

---

## Proposed commit message

```
docs: add PyCharm operational guide for Junie’s rules

Map junies-cursor-rules.md to concrete PyCharm settings:
- Set interpreter to project .venv (Python 3.14+), created via uv
- Install Ruff plugin; use Ruff as formatter and on‑save linter
- Set default test runner to pytest with pytest.ini
- Configure imports and remove shebang in Python file template
- Add Before Commit/pre-commit hooks for ruff format + check
- Recommend ports ≥ 10000 for web run configurations
```
