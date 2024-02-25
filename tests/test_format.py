from jsque import format


def test_format_jsque_expression():
    from jsque import ast

    assert format.format_jsque_expression(ast.Root()) == "@"
    assert format.format_jsque_expression(ast.ChildMapExpr(ast.Root())) == "@.*"
    assert format.format_jsque_expression(ast.Index(0)) == "0"
    assert format.format_jsque_expression(ast.MemberMapExpr(ast.Root())) == "@[*]"
    assert (
        format.format_jsque_expression(ast.SubExpr(ast.Root(), ast.Identifier("evo")))
        == "@.evo"
    )
    assert (
        format.format_jsque_expression(
            ast.MemberMapExpr(ast.SubExpr(ast.Root(), ast.Identifier("evo")))
        )
        == "@.evo[*]"
    )
