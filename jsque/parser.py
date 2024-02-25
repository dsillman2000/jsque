from jsque.ast import (
    ChildMapExpr,
    Index,
    MemberMapExpr,
    Root,
    SubExpr,
    QueryExpr,
    Identifier,
    IndexExpr,
)
from jsque.lexer import tokenize, TokenType


def parse_jsque_expression(source: str) -> QueryExpr:

    tokens = tokenize(source)
    if not tokens:
        raise Exception("No tokens to parse.")

    # All query expressions start with a root "@" token.
    if tokens[0].type != TokenType.Root:
        raise Exception("All expressions must start with a root '@'")

    expr: QueryExpr = Root()
    tokens.pop(0)

    while tokens:
        # Query operations are the token 3-grams/2-grams which follow the left operand expression.
        match (op_token := tokens.pop(0)).type:
            # If we see a left bracket, we're parsing an index expression, and need a full 3-gram.
            case TokenType.LeftBrac:
                if not len(tokens) >= 2:
                    raise Exception("Not enough tokens to complete index expression.")
                inner = tokens.pop(0)
                # Argument can be index or wildcard, mapping to IndexExpr and MemberMapExpr,
                # respectively.
                match inner.type:
                    case TokenType.Index:
                        expr = IndexExpr(expr, Index(int(inner.value)))
                    case TokenType.Wildcard:
                        expr = MemberMapExpr(expr)
                    case other:
                        raise Exception("Bad index argument. Got: %r" % other)
                # Must have closing bracket.
                assert (rbrac := tokens.pop(0)).type == TokenType.RightBrac, (
                    "Expected right bracket, got %s" % rbrac
                )
            # If we see a dot, we're parsing a sub expression, and need a full 2-gram.
            case TokenType.SubOp:
                if not len(tokens) >= 1:
                    raise Exception("Not enough tokens to complete sub expression.")
                inner = tokens.pop(0)
                # Argument can be identifier or wildcard, mapping to SubExpr and ChildMapExpr,
                # respectively.
                match inner.type:
                    case TokenType.Identifier:
                        expr = SubExpr(expr, Identifier(inner.value))
                    case TokenType.Wildcard:
                        expr = ChildMapExpr(expr)
                    case other:
                        raise Exception("Bad sub expression argument. Got: %r" % other)
            case _:
                raise Exception("Unexpected token: %r" % op_token)

    return expr
