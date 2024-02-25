from typing import Any

from jsque import ast


# def evaluate(query: ast.QueryTerm, obj: Any) -> Any:
#     if isinstance(query, ast.Root):
#         return obj
#     elif isinstance(query, ast.IndexExpr):
#         if not isinstance(query.item, ast.Index):
#             raise Exception("IndexExpr item must be an Index.")
#         if not ast.buffered(query.sequence):
#             sequence = evaluate(query.sequence, obj)
#             return sequence[query.item.number]
#         else:
#             sequence = query.sequence
#     elif isinstance(query, ast.MemberMapExpr):
#         if not ast.value(query.sequence):
#             sequence = evaluate(query.sequence, obj)
