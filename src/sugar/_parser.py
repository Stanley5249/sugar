"""Parser classes for parsing command-line arguments and subcommands."""

import enum
import shlex
import sys
from abc import abstractmethod
from collections.abc import (
    Callable,
    Collection,
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    Sequence,
    Set,
)
from io import StringIO
from itertools import islice, pairwise
from typing import IO, Any, ClassVar, Literal, Protocol, Self, assert_never, overload
from weakref import ReferenceType, ref

from docstring_parser import Docstring, parse_from_object

import __main__
from sugar._action import DEFAULT_ACTION, Action, Event, KeywordToken, PositionalToken
from sugar._constant import MISSING, PROG
from sugar._formatter import DEFAULT_FORMATTER, Formatter, SupportsStrings
from sugar._spec import ArgumentSpec, MagicSpec, PositionalSpec
from sugar._utils import (
    AutoRepr,
    Pair,
    did_you_mean,
    join_oxford_comma,
    pop_traceback,
    update_name_to_dest,
)
from sugar.exception import SugarError, SugarExit

POSITIONAL_ONLY = "Positional-only"
POSITIONAL_OR_KEYWORD = "Positional or keyword"
VAR_POSITIONAL = "Variadic positional"
KEYWORD_ONLY = "Keyword-only"
VAR_KEYWORD = "Variadic keyword"
MAGIC = "Magic"
COMMANDS = "Commands"

DEFAULT_HELP_FLAGS = "help", "h"


class Parser[T](Protocol):
    """Protocol for parsers."""

    # ================================================================================
    # attributes
    # ================================================================================

    formatter: Formatter
    state: T

    # ================================================================================
    # read-write properties
    # ================================================================================

    @property
    @abstractmethod
    def names(self) -> tuple[str, ...]: ...

    @names.setter
    @abstractmethod
    def names(self, value: tuple[str, ...]) -> None: ...

    @property
    @abstractmethod
    def brief(self) -> str | None: ...

    @brief.setter
    @abstractmethod
    def brief(self, value: str | None) -> None: ...

    @property
    @abstractmethod
    def detail(self) -> str | None: ...

    @detail.setter
    @abstractmethod
    def detail(self, value: str | None) -> None: ...

    @property
    @abstractmethod
    def docstring(self) -> Docstring | None: ...

    @docstring.setter
    @abstractmethod
    def docstring(self, value: Docstring | None) -> None: ...

    @property
    @abstractmethod
    def parent(self) -> "Parser[Any] | None": ...

    @parent.setter
    @abstractmethod
    def parent(self, value: "Parser[Any]") -> None: ...

    # ================================================================================
    # read-only properties
    # ================================================================================

    @property
    @abstractmethod
    def prog(self) -> str: ...

    @property
    @abstractmethod
    def path(self) -> list[str]: ...

    # ================================================================================
    # formatter methods
    # ================================================================================

    @abstractmethod
    def to_strings(self) -> list[str]: ...

    @abstractmethod
    def write_help(self, io: IO[str]) -> None: ...

    @abstractmethod
    def format_help(self) -> str: ...

    @abstractmethod
    def print_help(self) -> None: ...

    # ================================================================================
    # main methods
    # ================================================================================

    @abstractmethod
    def run(
        self, argv: str | Sequence[str] | None = None
    ) -> tuple["Parser[Any]", list[Any], dict[str, Any]]: ...

    @abstractmethod
    def stream(
        self,
        prompt: Any = None,
        input: Callable[[Any], str] = input,
    ) -> Iterator[tuple["Parser[Any]", list[Any], dict[str, Any]]]: ...

    @abstractmethod
    def cycle(
        self,
        prompt: Any = None,
        input: Callable[[Any], str] = input,
    ) -> None: ...

    @abstractmethod
    def parse_vals(
        self,
        vals: list[str],
        named_vals: list[tuple[str, list[str]]],
    ) -> tuple["Parser[Any]", list[Any], dict[str, Any]]: ...


class BaseParser[T](
    AutoRepr,
    Parser[T],
    fields=("names", "brief", "detail", "docstring", "parent", "state"),
):
    """Base class for parsers."""

    _names: tuple[str, ...]
    _brief: str | None
    _detail: str | None
    _docstring: Docstring | None = None
    _parent: ReferenceType[Parser[Any]] | None

    _name_to_dest: MutableMapping[str, str]
    _dest_to_group: MutableMapping[str, str]
    _magic_specs: MutableMapping[str, MagicSpec]

    def __init__(
        self,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
        formatter: Formatter = DEFAULT_FORMATTER,
        state: T = None,
        help_flags: tuple[str, ...] | None = DEFAULT_HELP_FLAGS,
    ) -> None:
        self._names = names

        self._brief = brief
        self._detail = detail
        self._docstring = docstring

        self._parent = None

        self._name_to_dest = {}
        self._dest_to_group = {}
        self._magic_specs = {}

        self.formatter = formatter
        self.state = state

        if help_flags:
            self._add_magic(
                None, help_flags, self.print_help, "show this help message and exit"
            )

    # ================================================================================
    # read-write properties
    # ================================================================================

    @property
    def names(self) -> tuple[str, ...]:
        return self._names

    @names.setter
    def names(self, value: tuple[str, ...]) -> None:
        if self._parent is not None:
            raise ValueError("names of subparser cannot be changed")
        self._names = value

    @property
    def brief(self) -> str | None:
        brief = self._brief
        if brief is not None:
            return brief

        docstring = self.docstring
        if docstring is not None:
            return docstring.short_description

    @brief.setter
    def brief(self, value: str | None) -> None:
        self._brief = value

    @property
    def detail(self) -> str | None:
        detail = self._detail
        if detail is not None:
            return detail

        docstring = self.docstring
        if docstring is not None:
            return docstring.long_description

    @detail.setter
    def detail(self, value: str | None) -> None:
        self._detail = value

    @property
    def docstring(self) -> Docstring | None:
        if self._parent is None and self._docstring is None:
            self._docstring = parse_from_object(__main__)
        return self._docstring

    @docstring.setter
    def docstring(self, value: Docstring | None) -> None:
        self._docstring = value

    @property
    def parent(self) -> Parser[Any] | None:
        if self._parent is None:
            return None
        parent = self._parent()
        if parent is None:
            raise ValueError("reference to parent parser is dead")
        return parent

    @parent.setter
    def parent(self, value: Parser[Any]) -> None:
        if self._parent is not None:
            raise ValueError("parent of subparser cannot be changed")
        self._parent = ref(value)

    # ================================================================================
    # read-only properties
    # ================================================================================

    @property
    def prog(self) -> str:
        # similar to 'dest'
        if self._names:
            return self._names[0]
        if self._parent is None:
            return PROG
        raise ValueError("subparser should have at least one name")

    @property
    def path(self) -> list[str]:
        path = []
        x = self
        while x:
            path.append(x.prog)
            x = x.parent
        path.reverse()
        return path

    # ================================================================================
    # formatter methods
    # ================================================================================

    def to_strings(self) -> list[str]:
        name = ", ".join(self.names)
        brief = self.brief
        if brief is None:
            brief = ""
        return [name, brief]

    def format_help(self) -> str:
        io = StringIO()
        self.write_help(io)
        return io.getvalue()

    def print_help(self) -> None:
        self.write_help(sys.stdout)

    # ================================================================================
    # main methods
    # ================================================================================

    def run(
        self,
        argv: str | Sequence[str] | None = None,
    ) -> tuple[Parser[Any], list[Any], dict[str, Any]]:
        with pop_traceback:
            try:
                argv = get_argv(argv)
                vals, named_vals = separate_argv(argv)
                return self.parse_vals(vals, named_vals)
            except SugarError as e:
                self.formatter.write_exception(sys.stderr, e)
                raise SugarExit(2)

    def stream(
        self,
        prompt: Any = None,
        input: Callable[[Any], str] = input,
    ) -> Iterator[tuple[Parser[Any], list[Any], dict[str, Any]]]:
        with pop_traceback:
            self.print_help()

            if prompt is None:
                prompt = getattr(sys, "ps1", ">>> ")

            while True:
                try:
                    x = input(prompt)
                except EOFError:
                    break
                except KeyboardInterrupt:
                    sys.stderr.write("\n")
                    raise

                if x:
                    try:
                        yield self.run(x)
                    except SugarExit:
                        pass

    def cycle(self, prompt: Any = None, input: Callable[[Any], str] = input) -> None:
        with pop_traceback:
            for _ in self.stream(prompt, input):
                pass

    # ================================================================================
    # private methods
    # ================================================================================

    def _make_tokens_by_group(
        self,
        named_vals: Iterable[tuple[str, list[str]]],
        groups: Set[str],
    ) -> dict[str | None, dict[str, KeywordToken]]:
        group_tokens: dict[str | None, dict[str, KeywordToken]] = {
            group: {} for group in groups
        }
        group_tokens[None] = unknown_tokens = {}

        for name, val in named_vals:
            dest = self._name_to_dest.get(name, None)

            if dest is None:
                target = unknown_tokens
                dest = name
            else:
                group = self._dest_to_group[dest]
                target = group_tokens.get(group, unknown_tokens)

            token = target.get(dest, None)

            if token is None:
                target[dest] = KeywordToken(dest, val, 1)
            else:
                token.value.extend(val)
                token.count += 1

        return group_tokens

    def _update_name_to_group(
        self,
        names: tuple[str, ...] | None,
        dest: str | None,
        group: str,
    ) -> tuple[tuple[str, ...], str]:
        names, dest = update_name_to_dest(names, dest, self._name_to_dest)

        if not dest.isidentifier():
            raise ValueError(f"dest {dest!r} must be a valid identifier")

        other = self._dest_to_group.get(dest, None)
        if other is not None:
            raise ValueError(f"dest {dest!r} already used as a/an {other!r} argument")

        self._dest_to_group[dest] = group
        return names, dest

    def _add_magic(
        self,
        dest: str | None,
        names: tuple[str, ...] | None,
        func: Callable[..., Any],
        help: str | None,
    ) -> None:
        names, dest = self._update_name_to_group(names, dest, MAGIC)
        self._magic_specs[dest] = MagicSpec(names, help or "", Event(func))

    def _handle_magic(self, dest_to_tokens: dict[str, KeywordToken]) -> None:
        if dest_to_tokens:
            spec = self._magic_specs
            for dest, token in dest_to_tokens.items():
                spec[dest].action.call_keyword(token)
            raise SugarExit(0)


class ArgumentParser[T](BaseParser[T]):
    _groups: ClassVar[Set[str]] = {
        POSITIONAL_ONLY,
        POSITIONAL_OR_KEYWORD,
        KEYWORD_ONLY,
        MAGIC,
    }

    _pos_only_specs: MutableMapping[str, PositionalSpec]
    _pos_or_kw_specs: MutableMapping[str, ArgumentSpec]
    _kw_only_specs: MutableMapping[str, ArgumentSpec]
    _var_pos_spec: Pair[str, ArgumentSpec]
    _var_kw_spec: Pair[str, ArgumentSpec]
    _tables_of_specs: Mapping[str, Collection[SupportsStrings]]
    _tables_of_extra: Mapping[str, Collection[SupportsStrings]]

    def __init__(
        self,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
        formatter: Formatter = DEFAULT_FORMATTER,
        state: T = None,
        help_flags: tuple[str, ...] | None = DEFAULT_HELP_FLAGS,
    ) -> None:
        super().__init__(
            *names,
            brief=brief,
            detail=detail,
            docstring=docstring,
            formatter=formatter,
            state=state,
            help_flags=help_flags,
        )
        self._pos_only_specs = {}
        self._pos_or_kw_specs = {}
        self._kw_only_specs = {}
        self._var_pos_spec = Pair()
        self._var_kw_spec = Pair()
        self._tables_of_specs = {
            POSITIONAL_ONLY: self._pos_only_specs.values(),
            POSITIONAL_OR_KEYWORD: self._pos_or_kw_specs.values(),
            VAR_POSITIONAL: self._var_pos_spec.values(),
            KEYWORD_ONLY: self._kw_only_specs.values(),
            VAR_KEYWORD: self._var_kw_spec.values(),
        }
        self._tables_of_extra = {MAGIC: self._magic_specs.values()}

    def write_help(self, io: IO[str]) -> None:
        formatter = self.formatter
        write_common(self, formatter, io, "[MAGIC] [POSITIONAL] [KEYWORD]")
        formatter.write_tables(io, self._tables_of_specs)
        formatter.write_tables(io, self._tables_of_extra)

    def add_positional_only(
        self,
        dest: str | None = None,
        *,
        names: tuple[str, ...] | None = None,
        action: Action[Any] | None = None,
        help: str | None = None,
        default: Any = MISSING,
    ) -> None:
        names, dest = self._update_name_to_group(names, dest, POSITIONAL_ONLY)
        self._pos_only_specs[dest] = PositionalSpec(
            names,
            action or DEFAULT_ACTION,
            help or "",
            default,
        )

    def add_positional_or_keyword(
        self,
        dest: str | None = None,
        *,
        names: tuple[str, ...] | None = None,
        action: Action[Any] | None = None,
        help: str | None = None,
        default: Any = MISSING,
    ) -> None:
        names, dest = self._update_name_to_group(names, dest, POSITIONAL_OR_KEYWORD)
        self._pos_or_kw_specs[dest] = ArgumentSpec(
            names,
            action or DEFAULT_ACTION,
            help or "",
            default,
        )

    def add_var_positional(
        self,
        dest: str | None = None,
        *,
        names: tuple[str, ...] | None = None,
        action: Action[Any] | None = None,
        help: str | None = None,
        default: Any = MISSING,
    ) -> None:
        if self._var_pos_spec:
            raise ValueError("only one var-positional argument is allowed")

        names, dest = self._update_name_to_group(names, dest, VAR_POSITIONAL)
        self._var_pos_spec[dest] = ArgumentSpec(
            names,
            action or DEFAULT_ACTION,
            help or "",
            default,
        )

    def add_keyword_only(
        self,
        dest: str | None = None,
        *,
        names: tuple[str, ...] | None = None,
        action: Action[Any] | None = None,
        help: str | None = None,
        default: Any = MISSING,
    ) -> None:
        names, dest = self._update_name_to_group(names, dest, KEYWORD_ONLY)
        self._kw_only_specs[dest] = ArgumentSpec(
            names,
            action or DEFAULT_ACTION,
            help or "",
            default,
        )

    def add_var_keyword(
        self,
        dest: str | None = None,
        *,
        names: tuple[str, ...] | None = None,
        action: Action[Any] | None = None,
        help: str | None = None,
        default: Any = MISSING,
    ) -> None:
        if self._var_kw_spec:
            raise ValueError("only one var-keyword argument is allowed")

        names, dest = self._update_name_to_group(names, dest, VAR_KEYWORD)
        self._var_kw_spec[dest] = ArgumentSpec(
            names,
            action or DEFAULT_ACTION,
            help or "",
            default,
        )

    def parse_vals(
        self,
        vals: list[str],
        named_vals: list[tuple[str, list[str]]],
    ) -> tuple[Self, list[Any], dict[str, Any]]:
        group_tokens = self._make_tokens_by_group(named_vals, self._groups)

        magic_tokens = group_tokens[MAGIC]
        self._handle_magic(magic_tokens)

        pos_only_tokens = group_tokens[POSITIONAL_ONLY]
        pos_or_kw_tokens = group_tokens[POSITIONAL_OR_KEYWORD]
        kw_only_tokens = group_tokens[KEYWORD_ONLY]
        var_kw_tokens = group_tokens[None]

        self._handle_errors(
            vals,
            pos_only_tokens,
            pos_or_kw_tokens,
            kw_only_tokens,
            var_kw_tokens,
        )

        n_pos_only = len(self._pos_only_specs)
        n_pos_or_kw = len(self._pos_or_kw_specs)
        n_pos = n_pos_only + n_pos_or_kw

        n_vals = len(vals)

        args = []

        for i, (dest, spec) in enumerate(self._pos_only_specs.items()):
            if i < n_vals:
                x = spec.action.call_positional(PositionalToken(dest, vals[i]))
            else:
                x = spec.default
            args.append(x)

        for i, (dest, spec) in enumerate(self._pos_or_kw_specs.items(), n_pos_only):
            if i < n_vals:
                x = spec.action.call_positional(PositionalToken(dest, vals[i]))
            else:
                token = pos_or_kw_tokens.get(dest, None)
                if token is None:
                    x = spec.default
                else:
                    x = spec.action.call_keyword(token)

            args.append(x)

        if self._var_pos_spec:
            dest, spec = self._var_pos_spec.item
            args += map(
                spec.action.call_positional,
                [PositionalToken(dest, val) for val in vals[n_pos:]],
            )

        kwargs = {}

        for dest, spec in self._kw_only_specs.items():
            token = kw_only_tokens.get(dest, None)
            if token is None:
                x = spec.default
            else:
                x = spec.action.call_keyword(token)
            kwargs[dest] = x

        if self._var_kw_spec:
            dest, spec = self._var_kw_spec.item

            for name, token in var_kw_tokens.items():
                x = spec.action.call_keyword(token)
                kwargs[name] = x

        return self, args, kwargs

    def _handle_errors(
        self,
        vals: list[str],
        pos_only_tokens: dict[str, KeywordToken],
        pos_or_kw_tokens: dict[str, KeywordToken],
        kw_only_tokens: dict[str, KeywordToken],
        unknown_tokens: dict[str, KeywordToken],
    ) -> None:
        notes = []

        n_vals = len(vals)
        n_pos_only = len(self._pos_only_specs)
        n_pos_or_kw = len(self._pos_or_kw_specs)

        if n_vals < n_pos_only:
            _ = join_oxford_comma(
                islice(self._pos_only_specs, n_vals, n_pos_only), "and"
            )
            notes.append(f"missing positional-only arguments {_}")

        if pos_only_tokens:
            _ = join_oxford_comma(pos_only_tokens, "and")
            notes.append(f"conflicting positional-only arguments {_}")

        conflicting_dests = []
        missing_pos_dests = []

        for i, (dest, spec) in enumerate(self._pos_or_kw_specs.items(), n_pos_only):
            if i < n_vals:
                if dest in pos_or_kw_tokens:
                    conflicting_dests.append(dest)
            else:
                if dest not in pos_or_kw_tokens and spec.default is MISSING:
                    missing_pos_dests.append(dest)

        if missing_pos_dests:
            _ = join_oxford_comma(missing_pos_dests, "and")
            notes.append(f"missing positional or keyword arguments {_}")

        if conflicting_dests:
            _ = join_oxford_comma(conflicting_dests, "and")
            notes.append(f"conflicting positional or keyword arguments {_}")

        if not self._var_pos_spec and n_vals > n_pos_only + n_pos_or_kw:
            notes.append("too many positional arguments")

        missing_kw_dests = [
            dest
            for dest, spec in self._kw_only_specs.items()
            if dest not in kw_only_tokens and spec.default is MISSING
        ]

        if missing_kw_dests:
            _ = join_oxford_comma(missing_kw_dests, "and")
            notes.append(f"missing keyword arguments {_}")

        if not self._var_kw_spec and unknown_tokens:
            if len(unknown_tokens) == 1:
                name = next(iter(unknown_tokens))
                notes.append(
                    did_you_mean(
                        f"unknown keyword argument {name!r}", name, self._name_to_dest
                    )
                )
            else:
                _ = join_oxford_comma(unknown_tokens, "and")
                notes.append(f"unknown keyword arguments {_}")

        if notes:
            exc = SugarError("missing or conflicting arguments")
            exc.__notes__ = notes
            raise exc


class CommandParser[T](BaseParser[T]):
    _groups: ClassVar[Set[str]] = {MAGIC}

    _parsers: MutableMapping[str, Parser]
    _name_to_parser: MutableMapping[str, str]

    def __init__(
        self,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
        formatter: Formatter = DEFAULT_FORMATTER,
        state: T = None,
        help_flags: tuple[str, ...] | None = DEFAULT_HELP_FLAGS,
    ) -> None:
        super().__init__(
            *names,
            brief=brief,
            detail=detail,
            docstring=docstring,
            formatter=formatter,
            state=state,
            help_flags=help_flags,
        )
        self._parsers = {}
        self._name_to_parser = {}
        self._tables = {
            COMMANDS: self._parsers.values(),
            MAGIC: self._magic_specs.values(),
        }

    def write_help(self, io: IO[str]) -> None:
        formatter = self.formatter
        write_common(self, formatter, io, "[MAGIC] <COMMAND> ...")
        formatter.write_tables(io, self._tables)

    def add_parser(
        self,
        parser: Parser,
    ) -> None:
        if parser.parent is not None:
            raise ValueError("subparser must not have parent")

        names, dest = update_name_to_dest(parser.names, None, self._name_to_parser)

        if dest in self._parsers:
            raise ValueError("name must be unique within the parser")

        for name in names:
            self._name_to_parser[name] = dest

        parser.parent = self
        self._parsers[dest] = parser

    @overload
    def get_subparser(
        self, name: str, ignore_error: Literal[False] = False
    ) -> Parser[T]: ...
    @overload
    def get_subparser(self, name: str, ignore_error: bool = False) -> Parser[T] | None: ...
    def get_subparser(self, name: str, ignore_error: bool = False) -> Parser[T] | None:
        dest = self._name_to_parser.get(name, None)
        if dest is None:
            if ignore_error:
                return None
            if name.isidentifier():
                raise ValueError(
                    did_you_mean(f"subparser {name!r} not found", name, self._parsers)
                )
            raise ValueError(f"{name!r} is not a valid subparser name")

        return self._parsers[dest]

    def parse_vals(
        self,
        vals: list[str],
        named_vals: list[tuple[str, list[str]]],
    ) -> tuple[Parser[Any], list[Any], dict[str, Any]]:
        if vals:
            name = vals.pop(0)
            name = name.replace("-", "_")

            try:
                parser = self.get_subparser(name)
            except ValueError as exc:
                raise SugarError(str(exc)) from None

            res = parser.parse_vals(vals, named_vals)
            return res

        group_tokens = self._make_tokens_by_group(named_vals, self._groups)
        magic_tokens = group_tokens[MAGIC]
        unknown_tokens = group_tokens[None]

        self._handle_magic(magic_tokens)

        if unknown_tokens:
            _ = join_oxford_comma(unknown_tokens, "and")
            raise SugarError(f"unknown arguments: {_}")

        raise SugarExit(0)


def get_argv(argv: str | Sequence[str] | None) -> list[str]:
    if argv is None:
        return sys.argv[1:]
    if isinstance(argv, str):
        try:
            return shlex.split(argv)
        except ValueError as exc:
            note = str(exc)
            exc = SugarError("failed to parse argv")
            exc.add_note(note)
            raise exc from None
    if isinstance(argv, list):
        return argv
    if isinstance(argv, Sequence):
        return [*argv]
    assert_never(argv)


class FlagEnum(enum.Enum):
    LONG = enum.auto()
    SHORT = enum.auto()
    NON = enum.auto()


LONG_FLAG = FlagEnum.LONG
SHORT_FLAG = FlagEnum.SHORT
NON_FLAG = FlagEnum.NON


def parse_flag_and_value(
    arg: str,
    *,
    error_on_bad_long: bool = True,
    error_on_bad_short: bool = False,
) -> tuple[FlagEnum, str]:
    if arg[:2] == "--":
        flag = arg[2:].replace("-", "_")
        if flag.isidentifier():
            return LONG_FLAG, flag
        if error_on_bad_long:
            raise SugarError(f"invalid long flag {arg!r}")

    # short flags can be combined, e.g., -abc is equivalent to -a -b -c
    elif arg[:1] == "-":
        flag = arg[1:].replace("-", "_")
        # dirty hack to validate short flags, equivalent to all(map(isidentifier, flag))
        if flag.replace("_", "A").isalpha():
            return SHORT_FLAG, flag
        if error_on_bad_short:
            raise SugarError(f"invalid short flag {arg!r}")

    return NON_FLAG, arg


def separate_argv(argv: list[str]) -> tuple[list[str], list[tuple[str, list[str]]]]:
    if not argv:
        return [], []

    flag_enum_and_vals = [*map(parse_flag_and_value, argv)]

    fs = [e for e, _ in flag_enum_and_vals]
    vs = [v for _, v in flag_enum_and_vals]

    iflags = [i for i, f in enumerate(fs) if f is not NON_FLAG]
    iflags.append(len(flag_enum_and_vals))

    vals = vs[: iflags[0]]
    named_vals = []

    for i, j in pairwise(iflags):
        e, flag = flag_enum_and_vals[i]
        assert e is not NON_FLAG, e

        if e is SHORT_FLAG:
            *shorts, flag = flag
            for short in shorts:
                named_vals.append((short, []))

        named_vals.append((flag, vs[i + 1 : j]))

    return vals, named_vals


def write_common(self: Parser, formatter: Formatter, io: IO[str], usage: str) -> None:
    formatter.write_usage(io, self.path, usage)
    formatter.write_paragraph(io, self.brief)
    formatter.write_paragraph(io, self.detail)
