"""Locate the JSON Schema files that live under the repo's top-level schema/ dir.

Schemas are kept outside the package (schema/, not src/wedding_visual/schema/) so
they read as the single source of truth for both this CLI and any non-Python
tooling (editor validation, CI). That only resolves cleanly for an editable
install (`pip install -e .`), which is the project's primary usage mode; a
packaged wheel would need schema/ bundled as package data instead.
"""
from __future__ import annotations

from pathlib import Path


class SchemaNotFoundError(RuntimeError):
    pass


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / "schema").is_dir():
            return candidate
    raise SchemaNotFoundError(
        "Could not locate the repo root (looked for a parent directory containing "
        "both pyproject.toml and schema/). Are you running from an editable install?"
    )


def schema_path(name: str) -> Path:
    path = _repo_root() / "schema" / name
    if not path.is_file():
        raise SchemaNotFoundError(f"No such schema file: {path}")
    return path
