from jsque import ast


class FormatException(Exception):
    pass


def format_jsque_expression(query: ast.QueryExpr) -> str:
    """Format a jsque query expression AST back into a string.

    Args:
        query (ast.QueryExpr): Query expression AST to format

    Raises:
        FormatException: If the query expression AST is somehow malformed.

    Returns:
        str: Formatted jsque query expression string
    """
    if isinstance(query, ast.Root):
        return "@"
    elif isinstance(query, ast.Index):
        return str(query.number)
    elif isinstance(query, ast.IndexExpr):
        format_sequence: str = format_jsque_expression(query.sequence)
        format_item: str = str(query.item.number)
        return f"{format_sequence}[{format_item}]"
    elif isinstance(query, ast.MemberMapExpr):
        format_sequence: str = format_jsque_expression(query.sequence)
        return f"{format_sequence}[*]"
    elif isinstance(query, ast.SubExpr):
        format_parent: str = format_jsque_expression(query.parent)
        format_child: str = query.child.key
        return f"{format_parent}.{format_child}"
    elif isinstance(query, ast.ChildMapExpr):
        format_parent: str = format_jsque_expression(query.parent)
        return f"{format_parent}.*"
    elif isinstance(query, ast.Identifier):
        return query.key
    else:
        raise FormatException("unexpected term: %r" % query)
