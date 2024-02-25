import pytest
from jsque import ast, parser, format
from tests.conftest import *
from hypothesis import given


@pytest.fixture
def query_eq(monkeypatch: pytest.MonkeyPatch):
    def __query_eq__(self: ast.QueryTerm, __other: ast.QueryTerm) -> bool:
        return self.dict() == __other.dict()

    with monkeypatch.context() as ctx:
        ctx.setattr(ast.QueryTerm, "__eq__", __query_eq__)
        yield


@pytest.mark.parametrize(
    "input,parsed",
    [
        pytest.param("@", ast.Root()),
        pytest.param("@[*]", ast.MemberMapExpr(ast.Root())),
        pytest.param("@.evo", ast.SubExpr(ast.Root(), ast.Identifier("evo"))),
        pytest.param(
            "@.evo[*]",
            ast.MemberMapExpr(ast.SubExpr(ast.Root(), ast.Identifier("evo"))),
        ),
    ],
)
def test_parser(input, parsed, query_eq):
    assert parser.parse_jsque_expression(input) == parsed


@pytest.mark.parametrize(
    "input",
    [
        pytest.param("@"),
        pytest.param("@.*"),
        pytest.param("@[*]"),
        pytest.param("@.evo"),
        pytest.param("@.evo[1]"),
        pytest.param("@.evo[*].*.ok"),
    ],
)
def test_parse_format_inv__parametrized(input: str):
    assert input == format.format_jsque_expression(parser.parse_jsque_expression(input))


@given(jsque_query(max_leaves=100))
def test_parse_format_inv__hypothesis(jsque_query):
    assert (
        jsque_query.dict()
        == parser.parse_jsque_expression(
            format.format_jsque_expression(jsque_query)
        ).dict()
    )
