from jsque import lexer, parser, format
import yaml


def main():
    src: str = "@.event_type"
    tokens = lexer.tokenize(src)
    print(tokens)

    print()

    parsed = parser.parse_jsque_expression(src)
    print(yaml.safe_dump(parsed.dict(), sort_keys=False))

    formatted = format.format_jsque_expression(parsed)
    print(formatted)
