from typing import Any

from jsque import ast


# def evaluate(query: ast.QueryTerm, obj: Any) -> dict:
#     if isinstance(query, ast.Root):
#         return obj
#     elif isinstance(query, ast.IndexExpr):
#         if not ast.value(query.sequence):
#             sequence = evaluate(query.sequence, obj)
#         if isinstance(query.item, ast.Wildcard):
#             return sequence