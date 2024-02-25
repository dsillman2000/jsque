"""
`@.event_type.*[*]`

type: mmap_op
children:
- type: cmap_op
  children:
  - type: sub_op
    children:
    - type: root
    - type: identifier
      value: event_type
"""

from abc import abstractmethod
from typing import Any, ClassVar, Self
from jsque import pipeline as pipe


class DictIsomorphism:
    """Trait for defining a dict-isomorphism for a class."""

    @abstractmethod
    def dict(self) -> dict: ...

    @classmethod
    @abstractmethod
    def fromdict(cls, d: "dict"): ...


class ASTException(Exception):
    pass


class QueryTerm(DictIsomorphism):
    """QueryTerm is a factory registry managing the dict isomorphism from our ASTs (stored in
    QueryExprs), using the correct class for the "type" key in the dict.

    Class vars:
    - _registry: A mapping of string -> type[QueryTerm], which acts as a lookup from the "type" key
      of a dict to the correct class for the QueryTerm.

    Attributes:
    - type: str (the type of the QueryTerm, used to lookup the correct class in the _registry)
    - value: Any (the value of the QueryTerm, if any)
    - children: list[QueryTerm] (the children terms of the QueryTerm, if any)
    """

    _registry: ClassVar = {}
    type: str
    value: Any
    children: list["QueryTerm"]

    def __init__(self, type: str, value: Any = None, children: list["QueryTerm"] = []):
        """Initialize a new QueryTerm with the specified data.

        Args:
            type (str): The type name of the QueryTerm.
            value (Any, optional): Value of the QueryTerm, if any. Defaults to None.
            children (list["QueryTerm"], optional): Children terms of the QueryTerm.
                Defaults to [].
        """
        self.type = type
        self.value = value
        self.children = children

    @classmethod
    def register(cls, name: str):
        """Register a subclass of QueryTerm with the specified name in the _registry."""

        def decorator(subclass):
            cls._registry[name] = subclass
            return subclass

        return decorator

    def dict(self) -> dict:
        """Writes the query term to a dict object. If the term has children, it will also write them
        to the dict, recursively invoking their `dict()` functions.

        Returns:
            dict: Dictionary representation of the query term.
        """
        d: dict[str, Any] = {"type": self.type}
        if self.value is not None:
            d["value"] = self.value
        if self.children:
            d["children"] = list(map(lambda _d: _d.dict(), self.children))
        return d

    @classmethod
    def fromdict(cls, d: "dict") -> "Self":
        """Construct a QueryTerm from a dict representation of the term. Looks up in the registry
        for a QueryTerm constructor from the dictionary's "type" key.

        Args:
            d (dict): Dictionary representation of the query term.

        Returns:
            Self: Constructed QueryTerm from the dict.
        """
        if d.get("type") not in cls._registry:
            raise ASTException(
                "Unrecognized type in dict QueryTerm: %r" % d.get("type")
            )
        _root_cls = cls._registry[d["type"]]
        if children := d.get("children"):
            children = list(map(lambda _d: cls.fromdict(_d), children))
            if value := d.get("value"):
                return _root_cls(value, children)
            return _root_cls(*children)
        if value := d.get("value"):
            return _root_cls(value)
        return _root_cls()


class QueryOp(QueryTerm):
    """A QueryOp is a QueryTerm that represents an operation on a query expression. It has a `pipe()`
    interface for converting the operation to a pipeline component for evaluation.
    """

    @abstractmethod
    def pipe(self) -> pipe.Pipe: ...


@QueryTerm.register("root")
class Root(QueryTerm):
    def __init__(self):
        super().__init__("root")


QueryExpr = Root | QueryOp


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


def primary_expr_class(d: "dict") -> "type[QueryExpr]":
    """Looks up into the registry for the correct class for the QueryExpr from the dictionary's "type",
    assuming it is an expression and not a erroneous term.

    Args:
        d (dict): QueryTerm dictionary representation to get the type from.

    Returns:
        type[QueryExpr]: Constructor (type) for the QueryExpr one can construct from the dict.
    """
    try:
        return {
            "root": Root,
            "idx_op": IndexExpr,
            "mmap_op": MemberMapExpr,
            "sub_op": SubExpr,
            "cmap_op": ChildMapExpr,
        }[d["type"]]
    except KeyError:
        raise ASTException(
            "Unrecognized type in dict representing QueryExpr: %r" % d.get("type")
        )


@QueryTerm.register("idx_op")
class IndexExpr(QueryOp):
    sequence: QueryExpr
    item: Index

    def __init__(self, sequence: QueryExpr, item: Index):
        if not isinstance(item, Index):
            raise IndexError("Bad index argument supplied: %r\n\nMust be Index." % item)
        super().__init__("idx_op", children=[sequence, item])
        self.sequence = sequence
        self.item = item

    def pipe(self) -> pipe.Injection:
        return pipe.Index(self.item.number)


@QueryTerm.register("mmap_op")
class MemberMapExpr(QueryOp):
    sequence: QueryExpr

    def __init__(self, sequence: QueryExpr):
        super().__init__("mmap_op", children=[sequence])
        self.sequence = sequence

    def pipe(self) -> pipe.Surjection:
        return pipe.MemberMap()


@QueryTerm.register("sub_op")
class SubExpr(QueryOp):
    parent: QueryExpr
    child: Identifier

    def __init__(self, parent: QueryExpr, child: Identifier):
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
class ChildMapExpr(QueryOp):
    parent: QueryExpr

    def __init__(self, parent: QueryExpr):
        super().__init__("cmap_op", children=[parent])
        self.parent = parent

    def pipe(self) -> pipe.Surjection:
        return pipe.ChildMap()


def to_pipeline(query: QueryExpr) -> pipe.Pipeline:
    """Parses a jsque query expression AST into a pipeline for evaluation.

    Args:
        query (QueryExpr): Query expression AST to build pipeline from.

    Raises:
        ASTException: When encountering an unexpected term in the AST.

    Returns:
        pipe.Pipeline: Pipeline for evaluating the query expression.
    """
    # Root case has no pipeline component to execute (null pipeline).
    if isinstance(query, Root):
        return pipe.Pipeline()
    # Other expressions have a .pipe() method to convert them to a pipeline component, which can
    # be concatenated onto the pipeline. Because everything associates left, the concatenation
    # of the second argument's pipe is always on the right.
    elif isinstance(query, IndexExpr):
        return to_pipeline(query.sequence) + pipe.Pipeline(query.pipe())
    elif isinstance(query, MemberMapExpr):
        return to_pipeline(query.sequence) + pipe.Pipeline(query.pipe())
    elif isinstance(query, SubExpr):
        return to_pipeline(query.parent) + pipe.Pipeline(query.pipe())
    elif isinstance(query, ChildMapExpr):
        return to_pipeline(query.parent) + pipe.Pipeline(query.pipe())
    else:
        raise ASTException("unexpected term: %r" % query)
