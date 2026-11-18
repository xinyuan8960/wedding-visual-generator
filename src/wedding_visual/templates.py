"""Load parametric templates from the repo's top-level templates/ dir.

A template file stores only parameters (canvas size, font path, decorative motif choice,
colors) -- never another work's geometry, per the project's copyright constraint. The
actual drawing logic lives in render/svg.py, keyed off these parameters.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .repo_paths import repo_root


class TemplateNotFoundError(RuntimeError):
    pass


def load_template(template_id: str) -> dict[str, Any]:
    path = repo_root(marker_dir="templates") / "templates" / f"{template_id}.json"
    if not path.is_file():
        raise TemplateNotFoundError(f"No such template: {path}")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def resolve_font_path(template: dict[str, Any]) -> Path:
    return resolve_repo_path(template["font_path"])


def resolve_repo_path(relative: str) -> Path:
    return repo_root(marker_dir="fonts") / relative
