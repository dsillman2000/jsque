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
from jsque import pipeline as pipe


class QueryTerm:
    @abstractmethod
    def dict(self) -> dict: ...

    @classmethod
    @abstractmethod
    def fromdict(cls, d: "dict"): ...


class QueryExpr(QueryTerm):
    @abstractmethod
    def pipe(self) -> pipe.Pipe: ...


class Root(QueryTerm):

    def dict(self):
        return {"type": "root"}

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "root"
        return cls()


QueryOperand = Root | QueryExpr


class Index(QueryTerm):
    number: int

    def __init__(self, number: int):
        self.number = number

    def dict(self) -> dict:
        return {"type": "index", "value": self.number}

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "index"
        return cls(d["value"])


class Identifier(QueryTerm):
    key: str

    def __init__(self, key: str):
        self.key = key

    def dict(self):
        return {"type": "identifier", "value": self.key}

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "identifier"
        return cls(d["value"])


def primary_expr_class(d: "dict") -> "type":
    return {
        "root": Root,
        "idx_op": IndexExpr,
        "mmap_op": MemberMapExpr,
        "sub_op": SubExpr,
        "cmap_op": ChildMapExpr,
    }[d["type"]]


class IndexExpr(QueryExpr):
    sequence: QueryOperand
    item: Index

    def __init__(self, sequence: QueryOperand, item: Index):
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

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "idx_op"
        sequence = d["children"][0]
        sequence_cls = primary_expr_class(sequence)
        return cls(
            sequence_cls.fromdict(sequence),
            Index.fromdict(d["children"][1]),
        )

    def pipe(self) -> pipe.Injection:
        return pipe.Index(self.item.number)


class MemberMapExpr(QueryExpr):
    sequence: QueryOperand

    def __init__(self, sequence: QueryOperand):
        self.sequence = sequence

    def dict(self) -> dict:
        return {
            "type": "mmap_op",
            "children": [
                self.sequence.dict(),
            ],
        }

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "mmap_op"
        sequence = d["children"][0]
        sequence_cls = primary_expr_class(sequence)
        return cls(sequence_cls.from_dict(sequence))

    def pipe(self) -> pipe.Surjection:
        return pipe.MemberMap()


class SubExpr(QueryExpr):
    parent: QueryOperand
    child: Identifier

    def __init__(self, parent: QueryOperand, child: Identifier):
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

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "sub_op"
        parent = d["children"][0]
        parent_cls = primary_expr_class(parent)
        return cls(
            parent_cls.fromdict(parent),
            Identifier.fromdict(d["children"][1]),
        )

    def pipe(self) -> pipe.Injection:
        return pipe.Sub(self.child.key)


class ChildMapExpr(QueryExpr):
    parent: QueryOperand

    def __init__(self, parent: QueryOperand):
        self.parent = parent

    def dict(self) -> dict:
        return {
            "type": "cmap_op",
            "children": [
                self.parent.dict(),
            ],
        }

    @classmethod
    def fromdict(cls, d: "dict"):
        assert d.get("type") == "cmap_op"
        parent = d["children"][0]
        parent_cls = primary_expr_class(parent)
        return cls(parent_cls.fromdict(parent))

    def pipe(self) -> pipe.Surjection:
        return pipe.ChildMap()


def to_pipeline(query: QueryTerm) -> pipe.Pipeline:
    if isinstance(query, Root):
        return pipe.Pipeline()
    elif isinstance(query, IndexExpr):
        return to_pipeline(query.sequence) + pipe.Pipeline(query.pipe())
    elif isinstance(query, MemberMapExpr):
        return to_pipeline(query.sequence) + pipe.Pipeline(query.pipe())
    elif isinstance(query, SubExpr):
        return to_pipeline(query.parent) + pipe.Pipeline(query.pipe())
    elif isinstance(query, ChildMapExpr):
        return to_pipeline(query.parent) + pipe.Pipeline(query.pipe())
    else:
        raise Exception("unexpected term: %r" % query)
