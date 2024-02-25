from enum import Enum
import re
import string


class TokenType(Enum):
    """Different types of tokens in jsque."""

    Identifier = "identifier"
    Wildcard = "wild"
    SubOp = "sub_op"
    LeftBrac = "lbrac"
    RightBrac = "rbrac"
    Index = "index"
    Root = "root"


class Token:
    """Object for storing a token string, with its associated type.

    Classmethods:

    - root: Create a root token.
    - identifier: Create an identifier token.
      args: v: str (the identifier string to store in the token)
    - sub_op: Create a sub_op token.
    - wildcard: Create a wildcard token.
    - left_bracket: Create a left_bracket token.
    - right_bracket: Create a right_bracket token.
    - index: Create an index token.
      args: v: str (the index string to store in the token)

    """

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
        """Human-readable representation of the token."""
        return f'{self.type.value.upper()}("{self.value}")'


IDENTIFIER_TERMINATORS = [".", "["] + list(string.whitespace)


def next_identifier(source: str, start_idx: int) -> str:
    """Consume from `source`, starting at index `start_idx`, until the identifier is terminated.

    Args:
        source (str): Source string to consume from
        start_idx (int): Index in string to start consuming from

    Returns:
        str: Consumed identifier name
    """
    ident: str = ""
    idx = start_idx
    while idx < len(source):
        if (c := source[idx]) in IDENTIFIER_TERMINATORS:
            return ident
        idx += 1
        ident += c
    return ident


def next_index(source: str, start_idx: int) -> str:
    """Consume from `source`, starting at index `start_idx`, until the index is terminated.

    Args:
        source (str): Source string to consume from
        start_idx (int): Index in string to start consuming from

    Returns:
        str: Consumed index string
    """
    num: str = ""
    idx = start_idx
    while idx < len(source) and source[idx] in string.digits + "-":
        num += source[idx]
        idx += 1
    return num


class LexerException(Exception):
    pass


def tokenize(source: str) -> list[Token]:
    """Tokenize a jsque query string.

    Args:
        source (str): Source string to tokenize

    Raises:
        LexerException: If an unexpected character is encountered during tokenization

    Returns:
        list[Token]: List of jsque tokens parsed from the source string.
    """

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
            raise LexerException(
                "Unexpected character encountered during tokenize: %s" % char_i
            )

    return tokens
