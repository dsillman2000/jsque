from jsque import ast


def format_jsque_expression(query: ast.QueryTerm) -> str:
    if isinstance(query, ast.Root):
        return "@"
    elif isinstance(query, ast.Index):
        return str(query.number)
    elif isinstance(query, ast.IndexExpr):
        format_sequence: str = format_jsque_expression(query.sequence)
        format_item: str = format_jsque_expression(query.item)
        return f"{format_sequence}[{format_item}]"
    elif isinstance(query, ast.MemberMapExpr):
        format_sequence: str = format_jsque_expression(query.sequence)
        return f"{format_sequence}[*]"
    elif isinstance(query, ast.SubExpr):
        format_parent: str = format_jsque_expression(query.parent)
        format_child: str = format_jsque_expression(query.child)
        return f"{format_parent}.{format_child}"
    elif isinstance(query, ast.ChildMapExpr):
        format_parent: str = format_jsque_expression(query.parent)
        return f"{format_parent}.*"
    elif isinstance(query, ast.Identifier):
        return query.key
    else:
        raise Exception("unexpected term: %r" % query)
