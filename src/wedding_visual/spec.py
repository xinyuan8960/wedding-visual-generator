from __future__ import annotations

from pathlib import Path
from typing import Any

from .validation import load_json_document, validate_document


def load_spec(path: str | Path) -> dict[str, Any]:
    """Load and validate a spec.json. Raises ValidationError on any schema violation."""
    data = load_json_document(path)
    validate_document(data, "spec.schema.json", str(path))
    return data
