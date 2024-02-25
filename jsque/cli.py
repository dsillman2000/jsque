import argparse
from pathlib import Path
from typing import Any


def input_subparsers(parser: argparse.ArgumentParser):
    parser.add_argument(
        "-f", "--file", type=Path, help="(input) from file", dest="input"
    )
    parser.add_argument(
        "-s", "--stdin", type=str, help="(input) from stdin", dest="input"
    )
    return parser


def main():

    argparser = argparse.ArgumentParser(description="jsque CLI")
    cmd_subparser = argparser.add_subparsers(title="cmd", dest="cmd")

    # cmd subparser for parsing
    parse_subparser = cmd_subparser.add_parser(
        "parse", help="parse input jsque expression into YML"
    )
    input_subparsers(parse_subparser)

    # cmd subparser for formatting
    format_subparser = cmd_subparser.add_parser(
        "format", help="format input jsque expression"
    )
    input_subparsers(format_subparser)

    # cmd subparser for evaluating
    eval_subparser = cmd_subparser.add_parser(
        "eval", help="evaluate jsque expression on input"
    )
    input_subparsers(eval_subparser)
    eval_subparser.add_argument(
        "-q", type=str, help="jsque query expression", required=True, dest="query"
    )

    arguments = argparser.parse_args()

    if not arguments.cmd:
        raise Exception("cmd required")

    from jsque import ast, parser

    parsed_ast: ast.QueryTerm

    if not arguments.input:
        raise Exception("input required")

    _result: Any
    if isinstance(arguments.input, Path):
        arguments.input = arguments.input.read_text()

    if arguments.cmd == "eval":
        parsed_ast = parser.parse_jsque_expression(arguments.query)
        import yaml

        subject = yaml.safe_load(arguments.input)
        _result = ast.to_pipeline(parsed_ast).eval(subject)
    elif arguments.cmd in ("parse", "format"):
        try:
            parsed_ast = parser.parse_jsque_expression(arguments.input)
        except Exception:
            import yaml

            yml_content = yaml.safe_load(arguments.input)
            primary = ast.primary_expr_class(yml_content)
            parsed_ast = primary.fromdict(yml_content)
        if arguments.cmd == "parse":
            import yaml

            _result = yaml.safe_dump(parsed_ast.dict(), sort_keys=False)
        else:
            from jsque import format

            _result = format.format_jsque_expression(parsed_ast)
    else:
        raise Exception("unexpected cmd: %r" % arguments.cmd)

    print(_result)
