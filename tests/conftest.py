import string
from hypothesis import strategies as st
from hypothesis.strategies._internal.core import DrawFn
from jsque import ast


def jsque_identifiers() -> st.SearchStrategy[ast.QueryTerm]:
    return st.builds(
        ast.Identifier,
        st.text(
            alphabet=string.ascii_letters + "_",
            min_size=1,
        ),
    )


def jsque_indices() -> st.SearchStrategy[ast.QueryTerm]:
    return st.one_of(st.builds(ast.Index, st.integers(min_value=-100, max_value=100)))


def jsque_root() -> st.SearchStrategy[ast.QueryTerm]:
    return st.just(ast.Root())


@st.composite
def jsque_query(draw: DrawFn, max_leaves: int = 100):
    return draw(
        st.recursive(
            jsque_root(),
            lambda children: st.one_of(
                st.builds(ast.IndexExpr, children, jsque_indices()),
                st.builds(ast.MemberMapExpr, children),
                st.builds(ast.SubExpr, children, jsque_identifiers()),
                st.builds(ast.ChildMapExpr, children),
            ),
            max_leaves=max_leaves,
        )
    )
