from __future__ import annotations

from pathlib import Path
from typing import Any

from .validation import load_json_document, validate_document


def load_questionnaire(path: str | Path) -> dict[str, Any]:
    """Load and validate questionnaire answers. Raises ValidationError on any schema violation."""
    data = load_json_document(path)
    validate_document(data, "questionnaire.schema.json", str(path))
    return data
