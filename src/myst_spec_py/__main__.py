"""CLI for cmark_to_ast"""
import argparse
import json
import sys

from myst_spec_py.mdast_to_html import render
from myst_spec_py.mdit_to_mdast import parse


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):
    def _format_action(self, action):
        """Remove metavar for sub-parsers."""
        parts = super(argparse.RawDescriptionHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts


def cli_myst_spec(args=None):
    """Convert CommonMark to MDAST JSON"""
    main_parser = argparse.ArgumentParser(
        prog="myst-spec",
        description="MyST Specification tools.",
        formatter_class=SubcommandHelpFormatter,
    )
    subparsers = main_parser.add_subparsers(
        title="Commands", dest="subparser_name", metavar="COMMAND"
    )

    cmark2mdast_parser = subparsers.add_parser(
        "to-mdast", help="Convert CommonMark to MDAST JSON."
    )
    cmark2mdast_parser.add_argument(
        "-s",
        "--source",
        type=argparse.FileType("r"),
        default=(None if sys.stdin.isatty() else sys.stdin),
        help="CommonMark source file (default is stdin).",
    )
    cmark2mdast_parser.add_argument(
        "--indent", type=int, help="Indent level of output JSON."
    )

    cmark2html_parser = subparsers.add_parser(
        "to-html", help="Convert CommonMark to HTML."
    )
    cmark2html_parser.add_argument(
        "-s",
        "--source",
        type=argparse.FileType("r"),
        default=(None if sys.stdin.isatty() else sys.stdin),
        help="CommonMark source file (default is stdin).",
    )

    args = main_parser.parse_args(args)

    if args.subparser_name is None:
        raise SystemExit(main_parser.format_help())

    if args.source is None:
        raise SystemExit("No source provided via -s/--source or stdin.")
    if args.subparser_name == "to-mdast":
        print(json.dumps(parse(args.source.read()), indent=args.indent))
    elif args.subparser_name == "to-html":
        print(render(parse(args.source.read())))


if __name__ == "__main__":
    sys.exit(cli_myst_spec())
