import sys
from collections.abc import Callable, Iterable, Iterator, MutableMapping
from contextlib import AbstractContextManager
from difflib import get_close_matches
from functools import partial, partialmethod, wraps
from itertools import filterfalse
from reprlib import recursive_repr
from traceback import print_exception
from types import FrameType, TracebackType
from typing import Any, ClassVar, Literal, Protocol, overload


class Pair[K, V](MutableMapping[K, V]):
    __slots__ = ("_item",)

    _item: tuple[K, V] | None

    def __init__(self, item: tuple[K, V] | None = None) -> None:
        self._item = item

    def __repr__(self) -> str:
        item = f"{self.key!r}: {self.value!r}" if self._item else ""
        return f"{self.__class__.__name__}({{{item}}})"

    @property
    def key(self) -> K:
        if self._item:
            return self._item[0]
        raise ValueError("pair is empty")

    @property
    def value(self) -> V:
        if self._item:
            return self._item[1]
        raise ValueError("pair is empty")

    @property
    def item(self) -> tuple[K, V]:
        if self._item:
            return self._item
        raise ValueError("pair is empty")

    def __getitem__(self, key: K) -> V:
        if self._item:
            k, v = self._item
            if key == k:
                return v
        raise KeyError(key)

    def __setitem__(self, key: K, value: V) -> None:
        self._item = key, value

    def __delitem__(self, key: K) -> None:
        if self._item:
            if key == self._item[0]:
                self._item = None
                return
        raise KeyError(key)

    def __iter__(self) -> Iterator[K]:
        if self._item:
            yield self._item[0]

    def __len__(self) -> int:
        return 0 if self._item else 1

    def __contains__(self, key: object) -> bool:
        return bool(self._item) and key == self._item[0]

    def __bool__(self) -> bool:
        return bool(self._item)


class AutoRepr(Protocol):
    # name mangling
    __fields: ClassVar[tuple[str, ...]]

    def __init_subclass__(
        cls, fields: tuple[str, ...] | None = None, **kwargs: Any
    ) -> None:
        super().__init_subclass__(**kwargs)
        if fields is None:
            try:
                cls.__fields
            except AttributeError:
                raise ValueError("subclass of AutoRepr must define fields") from None
            return
        cls.__fields = fields

    def _get_auto_repr_fields(self) -> list[tuple[str, Any]]:
        return [(field, getattr(self, field)) for field in self.__fields]

    @recursive_repr()
    def __repr__(self) -> str:
        items = ", ".join(f"{k}={getattr(self, k)!r}" for k in self.__fields)
        return f"{self.__class__.__name__}({items})"


class Shield(AbstractContextManager):
    def __init__(
        self,
        pop_tb: bool = False,
        frame: FrameType | None = None,
        exc_types: type[BaseException] | tuple[type[BaseException], ...] = (
            Exception,
            KeyboardInterrupt,
        ),
    ) -> None:
        self.pop_tb = pop_tb
        self.frame = frame
        self.exc_types = exc_types

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        suppress = exc_type is not None and issubclass(exc_type, self.exc_types)
        if suppress:
            if self.pop_tb and exc_tb is not None:
                exc_tb = exc_tb.tb_next
            frame = self.frame
            if frame:
                exc_tb = TracebackType(
                    exc_tb,
                    frame,
                    frame.f_lasti,
                    frame.f_lineno,
                )
            sys.last_exc = exc_val
            print_exception(None, exc_val, exc_tb)
        return suppress


class PopTraceback(AbstractContextManager):
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if __debug__ and exc_val and exc_tb:
            exc_val.with_traceback(exc_tb.tb_next)


pop_traceback = PopTraceback()


def update_name_to_dest(
    names: tuple[str, ...] | None,
    dest: str | None,
    name_to_dest: MutableMapping[str, str],
) -> tuple[tuple[str, ...], str]:
    # names is not None and len(names) != 0
    if names:
        if dest is None:
            dest = names[0]
    else:
        if dest is None:
            raise ValueError("at least one name or dest must be provided")
        names = (dest,)

    invalids = [*filterfalse(str.isidentifier, names)]
    if invalids:
        _ = join_oxford_comma(invalids, "and")
        raise ValueError(f"invalid names {_}")
    else:
        dups = [n for n in names if n in name_to_dest]
        if dups:
            _ = join_oxford_comma(dups, "and")
            raise ValueError(f"duplicate names {_}")

    for name in names:
        name_to_dest[name] = dest

    return names, dest


def cache_from_mapping[K, V](
    m: MutableMapping[K, V],
) -> Callable[[Callable[[K], V]], Callable[[K], V]]:
    def decorator(func: Callable[[K], V]) -> Callable[[K], V]:
        @wraps(func)
        def cached_func(k: K) -> V:
            v = m.get(k, None)
            if v is None:
                m[k] = v = func(k)
            return v

        return cached_func

    return decorator


def join_oxford_comma(it: Iterable[str], conj: str) -> str:
    it = [*map(repr, it)]
    n = len(it)
    if n == 0:
        return ""
    if n == 1:
        return it[0]
    if n == 2:
        return f"{it[0]} {conj} {it[1]}"
    it[-1] = f"{conj} {it[-1]}"
    return ", ".join(it)


def did_you_mean(
    msg: str,
    word: str,
    possibilities: Iterable[str],
    sep: str = ". ",
    n: int = 3,
    cutoff: float = 0.6,
) -> str:
    m = get_close_matches(word, possibilities, n, cutoff)
    if m:
        hint = join_oxford_comma(m, "or")
        return f"{msg}{sep}Did you mean {hint}?"
    return msg


@overload
def get_name(obj: Callable[..., Any], ignore_error: Literal[False] = False) -> str: ...
@overload
def get_name(obj: Callable[..., Any], ignore_error: bool) -> str | None: ...
def get_name(obj: Callable[..., Any], ignore_error: bool = False) -> str | None:
    name = getattr(obj, "__name__", None)
    if name is None:
        if isinstance(obj, (partial, partialmethod)):
            return get_name(obj.func)
        if ignore_error:
            return None
        raise ValueError(f"cannot get name of {obj!r}")
    return name


def set_name[T: Callable](name: str) -> Callable[[T], T]:
    def decorator(obj: T) -> T:
        obj.__name__ = name
        obj.__qualname__ = name
        return obj

    return decorator


# def cleandoc(doc: str) -> list[str]:
#     lines = doc.expandtabs().splitlines()
#     if lines:
#         head, *tail = lines
#         lines[0] = head.lstrip()
#         if tail:
#             margin = min([len(line) - n for line in tail if (n := len(line.lstrip()))])
#             for i, line in enumerate(tail, 1):
#                 lines[i] = line[margin:].rstrip()
#         while lines and not lines[-1]:
#             lines.pop()
#         while lines and not lines[0]:
#             lines.pop(0)
#     return lines
