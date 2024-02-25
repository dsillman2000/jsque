from jsque.ast import (
    ChildMapExpr,
    Index,
    MemberMapExpr,
    Root,
    SubExpr,
    QueryTerm,
    Identifier,
    IndexExpr,
)
from jsque.lexer import tokenize, TokenType


def parse_jsque_expression(source: str) -> QueryTerm:
    tokens = tokenize(source)
    if not tokens:
        raise Exception("No tokens to parse.")
    if tokens[0].type != TokenType.Root:
        raise Exception("All expressions must start with a root '@'")
    expr: QueryTerm = Root()
    tokens.pop(0)

    while tokens:
        # Mutation fragments are the tokens which follow the left operand.
        match (op_token := tokens.pop(0)).type:
            case TokenType.LeftBrac:
                if not len(tokens) >= 2:
                    raise Exception("Not enough tokens to complete index expression.")
                inner = tokens.pop(0)
                match inner.type:
                    case TokenType.Index:
                        expr = IndexExpr(expr, Index(int(inner.value)))
                    case TokenType.Wildcard:
                        expr = MemberMapExpr(expr)
                    case other:
                        raise Exception("Bad index argument. Got: %r" % other)
                assert (rbrac := tokens.pop(0)).type == TokenType.RightBrac, (
                    "Expected right bracket, got %s" % rbrac
                )
            case TokenType.SubOp:
                if not len(tokens) >= 1:
                    raise Exception("Not enough tokens to complete sub expression.")
                inner = tokens.pop(0)
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
