from enum import Enum
import re
import string


class TokenType(Enum):
    Identifier = "identifier"
    Wildcard = "wild"
    SubOp = "sub_op"
    LeftBrac = "lbrac"
    RightBrac = "rbrac"
    Index = "index"
    Root = "root"


class Token:
    type: TokenType
    value: str

    def __init__(self, type: TokenType, value: str):
        self.type = type
        self.value = value

    @classmethod
    def root(cls):
        return cls(TokenType.Root, "@")

    @classmethod
    def identifier(cls, v: str):
        return cls(TokenType.Identifier, v)

    @classmethod
    def sub_op(cls):
        return cls(TokenType.SubOp, ".")

    @classmethod
    def wildcard(cls):
        return cls(TokenType.Wildcard, "*")

    @classmethod
    def left_bracket(cls):
        return cls(TokenType.LeftBrac, "[")

    @classmethod
    def right_bracket(cls):
        return cls(TokenType.RightBrac, "]")

    @classmethod
    def index(cls, v: str):
        return cls(TokenType.Index, v)

    def __repr__(self) -> str:
        return f'{self.type.value.upper()}("{self.value}")'


IDENTIFIER_TERMINATORS = [".", "["] + list(string.whitespace)


def next_identifier(source: str, start_idx: int) -> str:
    ident: str = ""
    idx = start_idx
    while idx < len(source):
        if (c := source[idx]) in IDENTIFIER_TERMINATORS:
            return ident
        idx += 1
        ident += c
    return ident


def next_index(source: str, start_idx: int) -> str:
    num: str = ""
    idx = start_idx
    while idx < len(source) and source[idx] in string.digits + "-":
        num += source[idx]
        idx += 1
    return num


def tokenize(source: str) -> list[Token]:
    tokens = []
    idx = 0

    while idx < len(source):
        char_i: str = source[idx]

        if char_i in string.whitespace:
            idx += 1
            continue

        if char_i == "@":
            tokens += [Token.root()]
            idx += 1
        elif char_i in (string.ascii_letters + "_"):
            id_name = next_identifier(source, idx)
            idx += len(id_name)
            tokens += [Token.identifier(id_name)]
        elif char_i == "@":
            tokens += [Token.root()]
            idx += 1
        elif char_i == ".":
            tokens += [Token.sub_op()]
            idx += 1
        elif char_i == "[":
            tokens += [Token.left_bracket()]
            idx += 1
        elif char_i == "]":
            tokens += [Token.right_bracket()]
            idx += 1
        elif char_i == "*":
            tokens += [Token.wildcard()]
            idx += 1
        elif char_i in string.digits + "-":
            index = next_index(source, idx)
            idx += len(index)
            tokens += [Token.index(index)]
        else:
            raise ValueError(
                "Unexpected character encountered during tokenize: %s" % char_i
            )

    return tokens
