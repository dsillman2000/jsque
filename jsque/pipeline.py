import abc
from typing import Any, Generator


class Pipe:
    def __add__(self, other: "Pipe") -> "Pipeline":
        return Pipeline(self, other)


class Injection(Pipe):
    @abc.abstractmethod
    def eval(self, x: Any) -> Any: ...


class Index(Injection):
    def __init__(self, number: int) -> None:
        self.number = number

    def eval(self, x: Any) -> Any:
        if not hasattr(x, "__getitem__"):
            raise Exception("IndexExpr sequence must support __getitem__.")
        try:
            return x[self.number]
        except Exception:
            return None


class Sub(Injection):
    def __init__(self, key: str) -> None:
        self.key = key

    def eval(self, x: Any) -> Any:
        if not hasattr(x, "__getitem__"):
            raise Exception("SubExpr parent must support __getitem__.")
        try:
            return x[self.key]
        except Exception:
            return None


class Surjection(Pipe):
    @abc.abstractmethod
    def eval(self, x: Any) -> Generator[Any, None, None]: ...


class MemberMap(Surjection):
    def eval(self, x: Any) -> Generator[Any, None, None]:
        if not hasattr(x, "__iter__"):
            raise Exception("MemberMapExpr sequence must support __iter__.")
        for item in x:
            yield item


class ChildMap(Surjection):
    def eval(self, x: Any) -> Generator[Any, None, None]:
        if not hasattr(x, "values"):
            raise Exception("ChildMapExpr parent must support values.")
        for value in x.values():
            yield value


class Pipeline:
    components: tuple[Pipe, ...]

    def __init__(self, *components: Pipe):
        self.components = components

    def __add__(self, other: "Pipeline") -> "Pipeline":
        return Pipeline(*self.components, *other.components)

    def eval(self, x: Any) -> Any:
        components = list(self.components)
        while components and (component := components.pop(0)):
            if isinstance(component, Injection):
                x = component.eval(x)
            elif isinstance(component, Surjection):
                right_pipeline = Pipeline(*components)
                return [right_pipeline.eval(y) for y in component.eval(x)]
        return x
