from typing import Any
import pytest


@pytest.mark.parametrize(
    "input,query,output",
    [
        pytest.param({"a": "value", "key": "value"}, "@.a", "value"),
        pytest.param({"a": "value", "key": "value"}, "@.key", "value"),
        pytest.param([1, 2, 3], "@[1]", 2),
        pytest.param([1, 2, 3], "@[-1]", 3),
        pytest.param({"a": [1, 2, 3]}, "@.a[0]", 1),
        pytest.param({"a": [[], 2, [{"three": 3}, 0, 0]]}, "@.a[-1][0].three", 3),
    ],
)
def test_pipeline__injections(input: Any, query: str, output: Any):
    from jsque import ast, parser

    query_term = parser.parse_jsque_expression(query)
    pipe = ast.to_pipeline(query_term)
    assert pipe.eval(input) == output


@pytest.mark.parametrize(
    "input,query,output",
    [
        pytest.param({"a": "value", "key": "value"}, "@.*", ["value", "value"]),
        pytest.param([1, 2, 3], "@[*]", [1, 2, 3]),
        pytest.param({"a": [1, 2, 3]}, "@.a[*]", [1, 2, 3]),
        pytest.param(
            {"a": [[], ["two"], {"three": 3}]}, "@.a[*].three", [None, None, 3]
        ),
        pytest.param(
            {
                "a": {"pron": "aye", "val": 0},
                "b": {"pron": "bee", "val": 1},
                "c": {"pron": "see", "val": 2},
            },
            "@.*.pron",
            ["aye", "bee", "see"],
        ),
        pytest.param(
            {
                "first": [0, 1],
                "second": [2, 2],
                "third": "ab",
                "fourth": [],
            },
            "@.*[1]",
            [1, 2, "b", None],
        ),
    ],
)
def test_pipeline__single_surjection(input: Any, query: str, output: Any):
    from jsque import ast, parser

    query_term = parser.parse_jsque_expression(query)
    pipe = ast.to_pipeline(query_term)
    assert pipe.eval(input) == output
