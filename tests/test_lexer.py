import pytest
from jsque.lexer import Token, tokenize


@pytest.fixture
def token_eq(monkeypatch: pytest.MonkeyPatch):
    def __token_eq__(self, b: Token) -> bool:
        return self.type == b.type and self.value == b.value

    with monkeypatch.context() as m:
        m.setattr(Token, "__eq__", __token_eq__)
        yield


@pytest.mark.parametrize(
    "input,tokens",
    [
        pytest.param("@", [Token.root()], id="Root"),
        pytest.param("@.*", [Token.root(), Token.sub_op(), Token.wildcard()]),
        pytest.param(
            "@[*].x.y",
            [
                Token.root(),
                Token.left_bracket(),
                Token.wildcard(),
                Token.right_bracket(),
                Token.sub_op(),
                Token.identifier("x"),
                Token.sub_op(),
                Token.identifier("y"),
            ],
        ),
    ],
)
def test_tokenize(input: str, tokens: list[Token], token_eq):
    assert tokenize(input) == tokens


def test_tokenize__whitespace(token_eq):
    assert tokenize("   @ ") == [Token.root()]
    assert tokenize(" @ . * ") == [Token.root(), Token.sub_op(), Token.wildcard()]
    assert tokenize("@[*]\n    . x\n    . y") == [
        Token.root(),
        Token.left_bracket(),
        Token.wildcard(),
        Token.right_bracket(),
        Token.sub_op(),
        Token.identifier("x"),
        Token.sub_op(),
        Token.identifier("y"),
    ]
