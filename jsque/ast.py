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
from typing import Any, ClassVar
from jsque import pipeline as pipe


class DictIsomorphism:
    @abstractmethod
    def dict(self) -> dict: ...

    @classmethod
    @abstractmethod
    def fromdict(cls, d: "dict"): ...


class QueryTerm(DictIsomorphism):
    _registry: ClassVar = {}
    type: str
    value: Any
    children: list["QueryTerm"]

    def __init__(self, type: str, value: Any = None, children: list["QueryTerm"] = []):
        self.type = type
        self.value = value
        self.children = children

    @classmethod
    def register(cls, name: str):
        def decorator(subclass):
            cls._registry[name] = subclass
            return subclass

        return decorator

    def dict(self) -> dict:
        d: dict[str, Any] = {"type": self.type}
        if self.value is not None:
            d["value"] = self.value
        if self.children:
            d["children"] = list(map(lambda _d: _d.dict(), self.children))
        return d

    @classmethod
    def fromdict(cls, d: "dict") -> "QueryTerm":
        assert d.get("type") in cls._registry
        _root_cls = cls._registry[d["type"]]
        if children := d.get("children"):
            children = list(map(lambda _d: cls.fromdict(_d), children))
            if value := d.get("value"):
                return _root_cls(value, children)
            return _root_cls(*children)
        if value := d.get("value"):
            return _root_cls(value)
        return _root_cls()


class QueryExpr(QueryTerm):
    @abstractmethod
    def pipe(self) -> pipe.Pipe: ...


@QueryTerm.register("root")
class Root(QueryTerm):
    def __init__(self):
        super().__init__("root")


QueryOperand = Root | QueryExpr


@QueryTerm.register("index")
class Index(QueryTerm):
    number: int

    def __init__(self, number: int):
        super().__init__("index", number)
        self.number = number


@QueryTerm.register("identifier")
class Identifier(QueryTerm):
    key: str

    def __init__(self, key: str):
        super().__init__("identifier", key)
        self.key = key


def primary_expr_class(d: "dict") -> "type":
    return {
        "root": Root,
        "idx_op": IndexExpr,
        "mmap_op": MemberMapExpr,
        "sub_op": SubExpr,
        "cmap_op": ChildMapExpr,
    }[d["type"]]


@QueryTerm.register("idx_op")
class IndexExpr(QueryExpr):
    sequence: QueryOperand
    item: Index

    def __init__(self, sequence: QueryOperand, item: Index):
        if not isinstance(item, Index):
            raise IndexError("Bad index argument supplied: %r\n\nMust be Index." % item)
        super().__init__("idx_op", children=[sequence, item])
        self.sequence = sequence
        self.item = item

    def pipe(self) -> pipe.Injection:
        return pipe.Index(self.item.number)


@QueryTerm.register("mmap_op")
class MemberMapExpr(QueryExpr):
    sequence: QueryOperand

    def __init__(self, sequence: QueryOperand):
        super().__init__("mmap_op", children=[sequence])
        self.sequence = sequence

    def pipe(self) -> pipe.Surjection:
        return pipe.MemberMap()


@QueryTerm.register("sub_op")
class SubExpr(QueryExpr):
    parent: QueryOperand
    child: Identifier

    def __init__(self, parent: QueryOperand, child: Identifier):
        if not isinstance(child, Identifier):
            raise AttributeError(
                "Bad sub-argument supplied: %r\n\nMust be Identifier." % child
            )
        super().__init__("sub_op", children=[parent, child])

        self.parent = parent
        self.child = child

    def pipe(self) -> pipe.Injection:
        return pipe.Sub(self.child.key)


@QueryTerm.register("cmap_op")
class ChildMapExpr(QueryExpr):
    parent: QueryOperand

    def __init__(self, parent: QueryOperand):
        super().__init__("cmap_op", children=[parent])
        self.parent = parent

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
