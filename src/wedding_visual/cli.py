from __future__ import annotations

import argparse
import json
import sys

from .layout.glyphs import Font
from .layout.monogram import compose_monogram, initial_of
from .mapping import questionnaire_to_spec
from .questionnaire import load_questionnaire
from .spec import load_spec
from .validation import ValidationError, validate_document


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


def _cmd_questionnaire_to_spec(args: argparse.Namespace) -> int:
    try:
        questionnaire = load_questionnaire(args.path)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1

    spec = questionnaire_to_spec(questionnaire, seed=args.seed)
    # Belt-and-suspenders: a mapping bug should fail loudly here, not surface later as a
    # confusing renderer crash several phases from now.
    validate_document(spec, "spec.schema.json", "<generated spec>")

    text = json.dumps(spec, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"OK: wrote {args.output}")
    else:
        print(text, end="")
    return 0


def _cmd_monogram_layout(args: argparse.Namespace) -> int:
    try:
        spec = load_spec(args.path)
    except ValidationError as exc:
        print(exc, file=sys.stderr)
        return 1

    if spec["design_basis"] != "names":
        print(
            f"{args.path}: design_basis is {spec['design_basis']!r}, but monogram-layout "
            "only handles 'names' (photo-silhouette layout is a separate, not-yet-built step)",
            file=sys.stderr,
        )
        return 1

    names = spec["names"]
    try:
        char_a = initial_of(names["partner_a"]["latin"])
        char_b = initial_of(names["partner_b"]["latin"])
    except KeyError:
        print(f"{args.path}: names.partner_a/partner_b need a 'latin' name for monogram layout", file=sys.stderr)
        return 1

    layout = spec["layout"]
    result = compose_monogram(
        char_a,
        char_b,
        layout["monogram_arrangement"],
        whitespace_ratio=layout["whitespace_ratio"],
        canvas_size=args.canvas_size,
        font=Font(),
    )

    text = json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"OK: wrote {args.output}")
    else:
        print(text, end="")
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

    p_map = sub.add_parser(
        "questionnaire-to-spec",
        help="Deterministically derive a spec.json from validated questionnaire answers",
    )
    p_map.add_argument("path", help="Path to a questionnaire.json")
    p_map.add_argument("--seed", type=int, required=True, help="Seed to record in the output spec")
    p_map.add_argument("-o", "--output", help="Write the spec here instead of stdout")
    p_map.set_defaults(func=_cmd_questionnaire_to_spec)

    p_mono = sub.add_parser(
        "monogram-layout",
        help="Compute initial placement (glyph outlines + bboxes) for a names-basis spec",
    )
    p_mono.add_argument("path", help="Path to a spec.json with design_basis: names")
    p_mono.add_argument("--canvas-size", type=float, default=512.0)
    p_mono.add_argument("-o", "--output", help="Write the layout here instead of stdout")
    p_mono.set_defaults(func=_cmd_monogram_layout)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
