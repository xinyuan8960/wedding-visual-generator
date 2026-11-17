from __future__ import annotations

import argparse
import sys

from .questionnaire import load_questionnaire
from .spec import load_spec
from .validation import ValidationError


def _cmd_validate_spec(args: argparse.Namespace) -> int:
    try:
        load_spec(args.path)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"OK: {args.path} is a valid spec")
    return 0


def _cmd_validate_questionnaire(args: argparse.Namespace) -> int:
    try:
        load_questionnaire(args.path)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1
    print(f"OK: {args.path} is a valid questionnaire")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wedding-visual")
    sub = parser.add_subparsers(dest="command", required=True)

    p_spec = sub.add_parser("validate-spec", help="Validate a spec.json against schema/spec.schema.json")
    p_spec.add_argument("path")
    p_spec.set_defaults(func=_cmd_validate_spec)

    p_q = sub.add_parser(
        "validate-questionnaire",
        help="Validate questionnaire answers against schema/questionnaire.schema.json",
    )
    p_q.add_argument("path")
    p_q.set_defaults(func=_cmd_validate_questionnaire)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
