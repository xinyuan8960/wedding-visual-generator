from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import jsonschema

from .schemas import schema_path


class ValidationError(ValueError):
    """Raised when a spec or questionnaire document fails schema validation."""

    def __init__(self, source: str, errors: list[jsonschema.ValidationError]):
        self.source = source
        self.errors = errors
        lines = [f"{source} failed schema validation ({len(errors)} error(s)):"]
        for err in errors:
            loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
            lines.append(f"  - {loc}: {err.message}")
        super().__init__("\n".join(lines))


def load_json_document(path: str | Path) -> Any:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def validate_document(data: Any, schema_name: str, source: str) -> None:
    with open(schema_path(schema_name), encoding="utf-8") as fh:
        schema = json.load(fh)
    validator = jsonschema.Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        raise ValidationError(source, errors)
