"""CLI for cmark_to_ast"""
import argparse
import json
import sys

from .mdit_to_mdast import parse


def cli_cmark_to_mdast(args=None):
    """Convert CommonMark to MDAST JSON"""
    main_parser = argparse.ArgumentParser(
        description="Convert CommonMark to MDAST JSON."
    )
    # main_parser.add_argument('source', help='CommonMark source string.')
    main_parser.add_argument(
        "-s",
        "--source",
        type=argparse.FileType("r"),
        default=(None if sys.stdin.isatty() else sys.stdin),
        help="CommonMark source file (default is stdin).",
    )
    main_parser.add_argument("--indent", type=int, help="Indent level of output JSON.")
    args = main_parser.parse_args(args)
    if args.source is None:
        raise SystemExit("No source provided via -s/--source or stdin.")
    print(json.dumps(parse(args.source.read()), indent=args.indent))


if __name__ == "__main__":
    sys.exit(cli_cmark_to_mdast())
