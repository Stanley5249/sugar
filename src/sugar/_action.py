import dataclasses
import warnings
from abc import abstractmethod
from collections.abc import (
    Buffer,
    Callable,
    Collection,
    Container,
    Hashable,
    Iterable,
    Mapping,
    MutableMapping,
    MutableSequence,
    MutableSet,
    Reversible,
    Sequence,
    Set,
    Sized,
)
from functools import reduce
from inspect import isabstract, isclass
from operator import or_
from types import NoneType, UnionType
from typing import Annotated, Any, Protocol, TypeAliasType, Union, get_origin

from sugar._constant import SUGAR_DIRNAME
from sugar._eval import any_, bool_, bytes_, int_, none, str_
from sugar._utils import AutoRepr, cache_from_mapping, get_name, set_name
from sugar.exception import SugarError


@dataclasses.dataclass(slots=True)
class Token:
    dest: str = dataclasses.field()
    value: Any = dataclasses.field()


@dataclasses.dataclass(slots=True)
class PositionalToken(Token):
    value: str = dataclasses.field()


@dataclasses.dataclass(slots=True)
class KeywordToken(Token):
    value: list[str] = dataclasses.field()
    count: int = dataclasses.field()


class Action[T](AutoRepr, Protocol, fields=("name",)):
    name: str

    @abstractmethod
    def call_positional(self, token: PositionalToken, /) -> T: ...

    @abstractmethod
    def call_keyword(self, token: KeywordToken, /) -> T: ...


class KeywordOnlyAction[T](Action[T]):
    def call_positional(self, token: PositionalToken) -> T:
        raise SugarError(f"{self.__class__} can only be called with keyword arguments")


class Event(KeywordOnlyAction[None], fields=("name", "func")):
    def __init__(self, func: Callable[[], Any], name: str = "") -> None:
        self.func = func
        self.name = name

    def call_keyword(self, token: KeywordToken) -> None:
        n_vals = len(token.value)
        if n_vals:
            warnings.warn(
                error_expected_n(token.dest, 0, n_vals, self.name),
                skip_file_prefixes=(SUGAR_DIRNAME,),
            )
        self.func()


class Store[T](KeywordOnlyAction[T], fields=("name", "constant")):
    def __init__(self, constant: T, name: str = "") -> None:
        self.constant = constant
        self.name = name

    def call_keyword(self, token: KeywordToken) -> T:
        n_vals = len(token.value)
        if n_vals:
            warnings.warn(
                error_expected_n(token.dest, 0, n_vals, self.name),
                skip_file_prefixes=(SUGAR_DIRNAME,),
            )
        return self.constant


class Converter[T](Action[T], fields=("name", "func")):
    def __init__(
        self,
        func: Callable[[str], T],
        name: str | None = None,
    ) -> None:
        self.func = func
        self.name = get_name(func) if name is None else name

    def _call[_T](self, func: Callable[[str], _T], value: str, token: Token) -> _T:
        try:
            return func(value)
        except Exception:
            raise SugarError(error_invalid_value(token.dest, self.name, value))

    def call_positional(self, token: PositionalToken) -> T:
        return self._call(self.func, token.value, token)

    def call_keyword(self, token: KeywordToken) -> T:
        vals = token.value
        n_vals = len(vals)
        if n_vals != 1:
            raise SugarError(error_expected_n(token.dest, 1, n_vals, self.name))
        return self._call(self.func, vals[0], token)


class Build[T, E](Converter[T], fields=("name", "coll", "elem", "func")):
    def __init__(
        self,
        coll: Callable[[Iterable[E]], T],
        elem: Callable[[str], E],
        func: Callable[[str], T],
        name: str | None = None,
    ) -> None:
        super().__init__(func, name)
        self.coll = coll
        self.elem = elem

    def call_keyword(self, token: KeywordToken) -> T:
        func = self.elem
        return self.coll([self._call(func, val, token) for val in token.value])


class Record[T](Converter[T], fields=("name", "elem", "func")):
    def __init__(
        self,
        coll: Callable[[Iterable[Any]], T],
        elem: Sequence[Callable[[str], Any]],
        func: Callable[[str], T],
        name: str | None = None,
    ) -> None:
        super().__init__(func, name)
        self.coll = coll
        self.elem = elem

    def call_keyword(self, token: KeywordToken) -> T:
        return self.coll(
            [self._call(func, val, token) for func, val in zip(self.elem, token.value)]
        )


class Choice[T](Converter[T], fields=("name", "choices", "func")):
    def __init__(
        self,
        choices: Iterable[T],
        func: Callable[[str], T],
        name: str | None = None,
    ) -> None:
        self.choices = choices
        self.func = func
        if name is None:
            name = f"{ get_name(func)}[{", ".join(map(repr, choices))}]"
        self.name = name

    def call_positional(self, token: PositionalToken) -> T:
        val = self._call(self.func, token.value, token)
        if val in self.choices:
            return val
        raise SugarError(f"value {val!r} is not in {self.choices!r}")

    def call_keyword(self, token: KeywordToken) -> T:
        vals = token.value
        n_vals = len(vals)
        if n_vals != 1:
            raise SugarError(error_expected_n(token.dest, 1, n_vals, self.name))
        val = self._call(self.func, vals[0], token)

        if val in self.choices:
            return val
        raise SugarError(f"value {val!r} is not in {self.choices!r}")


class Map[K, V](Converter[V], fields=("name", "mapping", "func")):
    def __init__(
        self,
        mapping: Mapping[K, V],
        func: Callable[[str], K],
        name: str | None = None,
    ) -> None:
        self.mapping = mapping
        self.func = func
        if name is None:
            name = f"{get_name(func)}[{", ".join(map(repr, mapping))}]"
        self.name = name
        self.converter = Converter(func, name)

    def _mapping_get(self, key: K) -> V:
        val = self.mapping.get(key, None)
        if val is None:
            raise SugarError(f"key {key!r} is not in {self.mapping!r}")
        return val

    def call_positional(self, token: PositionalToken) -> V:
        return self._mapping_get(self.converter.call_positional(token))

    def call_keyword(self, token: KeywordToken) -> V:
        return self._mapping_get(self.converter.call_keyword(token))


PRIMITIVES: MutableMapping[Any, Callable[[str], Any]] = {
    str: str_,
    int: int_,
    float: float,
    complex: complex,
    bool: bool_,
    bytes: bytes_,
    NoneType: none,
    Any: any_,
}

DEFAULT_ACTION = Converter(any_)

ACTIONS: MutableMapping[Any, Action[Any]] = {
    str: Converter(str_),
    int: Converter(int_),
    float: Converter(float),
    complex: Converter(complex),
    bool: Converter(bool_),
    bytes: Converter(bytes_),
    NoneType: Store(None),
    Any: Converter(any_),
}

ABSTRACT_TO_CONCRETE: Mapping[type, type] = {
    Hashable: tuple,
    # Awaitable: None,
    # Coroutine: None,
    # AsyncIterable: None,
    # AsyncIterator: None,
    Iterable: list,
    # Iterator: iter,  # not a type
    Reversible: list,
    Sized: list,
    Container: list,
    Collection: list,
    # Callable: None,
    Set: set,
    MutableSet: set,
    Mapping: dict,
    MutableMapping: dict,
    Sequence: list,
    MutableSequence: list,
    # ByteString: bytes,  # deprecated
    Buffer: bytes,
    # MappingView: None,
    # KeysView: None,
    # ItemsView: None,
    # ValuesView: None,
    # ContextManager: None,
    # AsyncContextManager: None,
    # Generator: None,
    # AsyncGenerator: None,
}


def call[T](
    action: Action[Any],
    func: Callable[[str], T],
    value: str,
    token: Token,
) -> T:
    try:
        return func(value)
    except Exception:
        raise SugarError(error_invalid_value(token.dest, action.name, value))


def error_expected_n(dest: str, exp: int, n_vals: int, name: str = "") -> str:
    if name:
        return f"{dest!r} expected {exp} argument for {name}, but got {n_vals}"
    else:
        return f"{dest!r} expected {exp} argument, but got {n_vals}"


def error_invalid_value(dest: str, name: str, val: str) -> str:
    return f"{dest!r} got invalid {name} value {val!r}"


def error_type_arguments_count(cls: Any, super_cls: Any, exp: int, n: int) -> str:
    return f"{cls} is a subclass of {super_cls} and expected {exp} type arguments, but got {n}."


@cache_from_mapping(PRIMITIVES)
def make_type(tp: Any) -> Callable[[str], Any]:
    name = tp.__name__ if isclass(tp) else str(tp)

    @set_name(name)
    def type_(x: str) -> Any:
        y = any_(x)
        if ext_isinstance(y, tp):
            return y
        raise ValueError(f"{y} is not an instance of {name}")

    return type_


def ext_isinstance(obj: Any, tp: Any) -> bool:
    if tp is Any:
        return True

    if isinstance(tp, TypeAliasType):
        return ext_isinstance(obj, tp.__value__)

    origin = getattr(tp, "__origin__", None)
    args = getattr(tp, "__args__", None)

    if args is None:
        return isinstance(obj, tp if origin is None else origin)

    if isinstance(tp, UnionType) or origin is Union:
        return any(ext_isinstance(obj, arg) for arg in args)

    if origin is None:
        # may raise error
        return isinstance(obj, tp)

    if not isinstance(obj, origin):
        return False

    if isinstance(obj, tuple):
        n_args = len(args)

        if n_args == 2 and args[1] is ...:
            tp = args[0]
            return all(ext_isinstance(sub, tp) for sub in obj)

        n_obj = len(obj)

        if n_args != n_obj:
            raise TypeError(error_type_arguments_count(origin, tuple, n_args, n_obj))

        return all(ext_isinstance(sub, sub_tp) for sub, sub_tp in zip(obj, args))

    if isinstance(obj, Mapping):
        n_args = len(args)
        if n_args == 0:
            return True
        if n_args != 2:
            raise TypeError(error_type_arguments_count(origin, Mapping, 2, n_args))
        k_tp, v_tp = args
        return all(
            ext_isinstance(k, k_tp) and ext_isinstance(v, v_tp) for k, v in obj.items()
        )

    if isinstance(obj, Iterable):
        n_args = len(args)
        if n_args == 0:
            return True
        if n_args != 1:
            raise TypeError(error_type_arguments_count(origin, Iterable, 1, n_args))
        sub_tp = args[0]
        return all(ext_isinstance(sub, sub_tp) for sub in obj)

    raise TypeError(f"cannot check {tp} for {obj}")


def resolve_type(tp: Any) -> Any:
    return _resolve_type(tp, set())


def _resolve_type(tp: Any, ctx: set[Any]) -> Any:
    tid = id(tp)

    if tid in ctx:
        return tp

    ctx.add(tid)

    if tp is None:
        return NoneType

    if isinstance(tp, TypeAliasType):
        return _resolve_type(tp.__value__, ctx)

    origin = get_origin(tp)

    # _AnnotatedAlias is a private class
    if origin is Annotated:
        return _resolve_type(tp.__origin__, ctx)

    args = getattr(tp, "__args__", None)

    if args is None:
        return tp if origin is None else origin

    args = [_resolve_type(arg, ctx) for arg in args]

    if isinstance(tp, UnionType) or origin is Union:
        if Any in args:
            return Any
        return reduce(or_, args)

    if origin is None:
        raise TypeError(f"{tp} has args but no origin")

    if not hasattr(origin, "__class_getitem__"):
        raise TypeError(f"{origin} has no `__class_getitem__` method")

    return origin[*args]


def auto(tp: Any) -> Action[Any]:
    return _auto(resolve_type(tp))


@cache_from_mapping(ACTIONS)
def _auto(tp: Any) -> Action[Any]:
    if isinstance(tp, UnionType):
        return Converter(make_type(tp))

    origin = getattr(tp, "__origin__", tp)
    args = getattr(tp, "__args__", None)

    if not isclass(origin):
        raise TypeError(f"{tp} is not a class")

    if issubclass(origin, tuple):
        func = make_type(tp)

        if args is None:
            return Build(origin, any_, func)

        if len(args) == 2 and args[1] is ...:
            return Build(origin, make_type(args[0]), func)

        return Record(origin, [*map(make_type, args)], func)

    elif issubclass(origin, Mapping):
        pass

    elif issubclass(origin, Collection):
        if args is None:
            elem = any_
        elif len(args) != 1:
            raise TypeError(f"expected 1 type parameter for {tp}, but got {len(args)}")
        else:
            elem = make_type(args[0])

        if isabstract(origin):
            origin = ABSTRACT_TO_CONCRETE.get(origin, None)
            if origin is None:
                raise TypeError(f"no concrete type for abstract type {tp}")

        func = make_type(tp)

        return Build(origin, elem, func)

    func = make_type(tp)
    return Converter(func)
