"""Locate the JSON Schema files that live under the repo's top-level schema/ dir."""
from __future__ import annotations

from pathlib import Path

from .repo_paths import repo_root


class SchemaNotFoundError(RuntimeError):
    pass


def schema_path(name: str) -> Path:
    path = repo_root(marker_dir="schema") / "schema" / name
    if not path.is_file():
        raise SchemaNotFoundError(f"No such schema file: {path}")
    return path
