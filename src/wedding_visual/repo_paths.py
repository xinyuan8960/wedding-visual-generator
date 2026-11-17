"""Locate the repo root from an editable install.

Several top-level directories (schema/, fonts/, templates/) live outside the
src/wedding_visual package so they read as a single source of truth shared by
Python, non-Python tooling, and humans browsing the repo. That only resolves
cleanly for an editable install (`pip install -e .`), which is this project's
primary usage mode; a packaged wheel would need each of them bundled as package
data instead.
"""
from __future__ import annotations

from pathlib import Path


class RepoRootNotFoundError(RuntimeError):
    pass


def repo_root(*, marker_dir: str) -> Path:
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (candidate / "pyproject.toml").is_file() and (candidate / marker_dir).is_dir():
            return candidate
    raise RepoRootNotFoundError(
        f"Could not locate the repo root (looked for a parent directory containing "
        f"both pyproject.toml and {marker_dir}/). Are you running from an editable install?"
    )
