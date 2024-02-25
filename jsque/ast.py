"""

`event_type.*[*]`

type: idx_op
children:
- type: sub_op
  children:
  - type: identifier
    value: event_type
  - type: wild
- type: wild

"""

from abc import abstractmethod
from typing import Any


def value(__obj: Any) -> bool:
    return bool(getattr(__obj, "__value__", False))


class QueryTerm:
    __value__: bool

    @abstractmethod
    def dict(self) -> dict: ...


class Root(QueryTerm):
    __value__ = True

    def dict(self):
        return {"type": "root"}


class Wildcard(QueryTerm):
    __value__ = True

    def dict(self) -> dict:
        return {"type": "wild"}


class Index(QueryTerm):
    __value__ = True
    number: int

    def __init__(self, number: int):
        self.number = number

    def dict(self) -> dict:
        return {"type": "index", "value": self.number}


class Identifier(QueryTerm):
    __value__ = True
    key: str

    def __init__(self, key: str):
        self.key = key

    def dict(self):
        return {"type": "identifier", "value": self.key}


class IndexExpr(QueryTerm):
    __value__ = False
    sequence: QueryTerm
    item: Index

    def __init__(self, sequence: QueryTerm, item: Index):
        if not isinstance(item, Index):
            raise IndexError("Bad index argument supplied: %r\n\nMust be Index." % item)

        self.sequence = sequence
        self.item = item

    def dict(self):
        return {
            "type": "idx_op",
            "children": [
                self.sequence.dict(),
                self.item.dict(),
            ],
        }


class MemberMapExpr(QueryTerm):
    __value__ = False
    sequence: QueryTerm

    def __init__(self, sequence: QueryTerm):
        self.sequence = sequence

    def dict(self) -> dict:
        return {
            "type": "mmap_op",
            "children": [
                self.sequence.dict(),
            ],
        }


class SubExpr(QueryTerm):
    __value__ = False
    parent: QueryTerm
    child: Identifier

    def __init__(self, parent: QueryTerm, child: Identifier):
        if not isinstance(child, Identifier):
            raise AttributeError(
                "Bad sub-argument supplied: %r\n\nMust be Identifier." % child
            )

        self.parent = parent
        self.child = child

    def dict(self) -> dict:
        return {
            "type": "sub_op",
            "children": [
                self.parent.dict(),
                self.child.dict(),
            ],
        }


class ChildMapExpr(QueryTerm):
    __value__ = False
    parent: QueryTerm

    def __init__(self, parent: QueryTerm):
        self.parent = parent

    def dict(self) -> dict:
        return {
            "type": "cmap_op",
            "children": [
                self.parent.dict(),
            ],
        }
