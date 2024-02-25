import abc
from typing import Any, Generator


class EvaluationException(Exception):
    pass


class Pipe:
    """Notion of a pipeline component which can be additively concatenated with other components."""

    def __add__(self, other: "Pipe") -> "Pipeline":
        """Defining pipeline concatenation as the addition operator.

        Args:
            other (Pipe): Other pipeline component to concatenate with, forming a pipeline.

        Returns:
            Pipeline: Evaluation pipeline formed of the two components.
        """
        return Pipeline(self, other)


class Injection(Pipe):
    """An _injection_ is a query plan which can evaluate to any object result. It is a specific type
    of query operation which requests a specific member or specific child.

    When an injection succeeds, it returns its targeted result.

    When an injection fails, it returns null or raises an exception.
    """

    @abc.abstractmethod
    def eval(self, x: Any) -> Any: ...


class Index(Injection):
    """An Index pipe, which takes the "i"th element of its first argument.

    Attributes:
        number (int): Index to select from the first argument.
    """

    number: int

    def __init__(self, number: int) -> None:
        self.number = number

    def eval(self, x: Any) -> Any:
        """Indexes into the object "x" with the index "number", returning None if the index is out
        of bounds, or raising an exception if the object does not support indexing.

        Args:
            x (Any): Object to index into

        Raises:
            EvaluationException: If the object does not support indexing (e.g. is an integer).

        Returns:
            Any: Member object at the index, or None if the index is out of bounds.
        """
        if not hasattr(x, "__getitem__"):
            raise EvaluationException(
                "IndexExpr sequence must support __getitem__.\nCannot index into %s: %r"
                % (type(x).__name__, x)
            )
        try:
            return x[self.number]
        except Exception:
            return None


class Sub(Injection):
    """A Sub pipe, which looks up "key" in its first argument.

    Attributes:
        key (str): Key to look up in the first argument.
    """

    key: str

    def __init__(self, key: str) -> None:
        self.key = key

    def eval(self, x: Any) -> Any:
        """Looks up "key" in the object "x", returning None if the key is not found, or raising an
        exception if the object does not support key lookup.

        Args:
            x (Any): Object to lookup into.

        Raises:
            EvaluationException: If the object does not support key lookup.

        Returns:
            Any: Member object at the key, or None if the key is not found.
        """
        if not hasattr(x, "__getitem__"):
            raise EvaluationException(
                "SubExpr parent must support __getitem__.\nCannot lookup into %s: %r"
                % (type(x).__name__, x)
            )
        try:
            return x[self.key]
        except Exception:
            return None


class Surjection(Pipe):
    """A _surjection_ is a query plan which can evaluate to a sequence of objects. It is a
    non-specific type of query operation which requests all members or all children.

    When a surjection succeeds, it returns a sequence of results over which the remainder of the
    pipeline should be evaluated on.

    When a surjection fails, it returns an empty sequence or raises an exception.

    **Note**: I sometimes refer to a surjection as _exploding_ an input sequence.
    """

    @abc.abstractmethod
    def eval(self, x: Any) -> Generator[Any, None, None]: ...


class MemberMap(Surjection):
    """A MemberMap pipe, which explodes the elements of its first argument."""

    def eval(self, x: Any) -> Generator[Any, None, None]:
        """Explodes the sequence "x" into its elements (if it has any). If "x" does not support
        iteration, raises an exception.

        Args:
            x (Any): Sequence to explode.

        Raises:
            EvaluationException: If the sequence does not support iteration.

        Yields:
            Generator[Any, None, None]: Sequence of elements in the input sequence.
        """
        if not hasattr(x, "__iter__"):
            raise EvaluationException("MemberMapExpr sequence must support __iter__.")
        for item in x:
            yield item


class ChildMap(Surjection):
    """A ChildMap pipe, which explodes the children/values of its first argument."""

    def eval(self, x: Any) -> Generator[Any, None, None]:
        """Explodes the the object "x" into its values (if it has any). If "x" is not a mapping of
        keys to values, raises an exception.

        Args:
            x (Any): Object whose values should be exploded.

        Raises:
            EvaluationException: If the object does not support values iteration.

        Yields:
            Generator[Any, None, None]: Sequence of values in the input object.
        """
        if not hasattr(x, "values"):
            raise EvaluationException("ChildMapExpr parent must support values.")
        for value in x.values():
            yield value


class Pipeline:
    """A complete query plan formed by concatenating multiple pipeline components into a single
    evaluation pipeline.

    Attributes:
        components (tuple[Pipe, ...]): Sequence of pipeline components to evaluate in order, from
        left to right.
    """

    components: tuple[Pipe, ...]

    def __init__(self, *components: Pipe):
        """Instantiate a new pipeline from the supplied components."""
        self.components = components

    def __add__(self, other: "Pipeline") -> "Pipeline":
        """Concatenate two pipelines together, forming a new pipeline.

        Args:
            other (Pipeline): Right pipeline in concatenation.

        Returns:
            Pipeline: Concatenated pipeline.
        """
        return Pipeline(*self.components, *other.components)

    def eval(self, x: Any) -> Any:
        """_Folds_ a query plan over an input object, returning the result of the query.

        Args:
            x (Any): Input object to evaluate the query plan on.

        Returns:
            Any: Result of the query plan on the input object.

        Raises:
            EvaluationException: If any constituent pipeline component raises an exception.
        """
        components = list(self.components)
        while components and (component := components.pop(0)):
            try:
                if isinstance(component, Injection):
                    x = component.eval(x)
                elif isinstance(component, Surjection):
                    right_pipeline = Pipeline(*components)
                    return [right_pipeline.eval(y) for y in component.eval(x)]
            except EvaluationException as e:
                component_name = type(component).__name__
                raise EvaluationException(
                    "Error evaluating %s on %s:\n%s"
                    % (component_name, type(x).__name__, e)
                )
        return x
