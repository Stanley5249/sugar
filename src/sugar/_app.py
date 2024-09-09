import dataclasses
import sys
from abc import abstractmethod
from collections.abc import Callable, Iterator, Mapping, MutableMapping, Sequence
from inspect import Parameter, signature
from typing import Any, Literal, Protocol, Self, assert_never, overload
from weakref import ReferenceType, ref

from docstring_parser import Docstring, parse_from_object

from sugar._action import Action, auto
from sugar._formatter import DEFAULT_FORMATTER, Formatter
from sugar._parser import (
    DEFAULT_HELP_FLAGS,
    MISSING,
    ArgumentParser,
    CommandParser,
    Interface,
    Parser,
)
from sugar._utils import AutoRepr, Shield, get_name, pop_traceback
from sugar.exception import SugarError


def sugar(
    obj: Callable[..., Any] | Sequence[Callable[..., Any]],
    argv: str | Sequence[str] | None = None,
) -> Any:
    if isinstance(obj, Sequence):
        app = CommandApp()
        for command in obj:
            app.add_command(command)
    elif callable(obj):
        app = ArgumentApp()
        app.add_command(obj)
    else:
        assert_never(obj)
    return app.run(argv)


class App[T](Interface[T], Protocol):
    @property
    def parser(self) -> Parser[ReferenceType[Self]]: ...

    @abstractmethod
    def parse_args(
        self,
        parser: Parser[ReferenceType["App"]],
        args: Sequence[str],
        kwargs: Mapping[str, Any],
    ) -> tuple["App", Any]: ...

    @abstractmethod
    def run(self, argv: str | Sequence[str] | None = None) -> tuple["App", Any]: ...

    @abstractmethod
    def stream(
        self, prompt: Any = None, input: Callable[[Any], str] = input
    ) -> Iterator[tuple["App", Any]]: ...

    @abstractmethod
    def cycle(
        self, prompt: Any = None, input: Callable[[Any], str] = input
    ) -> None: ...


class BaseApp[T](AutoRepr, App[T], fields=("parser",)):
    def run(self, argv: str | Sequence[str] | None = None) -> tuple[App, Any]:
        with pop_traceback:
            parser, args, kwargs = self.parser.run(argv)
            return self.parse_args(parser, args, kwargs)

    def stream(
        self,
        prompt: Any = None,
        input: Callable[[Any], str] = input,
    ) -> Iterator[tuple[App, Any]]:
        with pop_traceback:
            shield = Shield(True, sys._getframe(1))
            for parser, args, kwargs in self.parser.stream(prompt, input):
                with shield:
                    yield self.parse_args(parser, args, kwargs)

    def cycle(self, prompt: Any = None, input: Callable[[Any], str] = input) -> None:
        with pop_traceback:
            shield = Shield(True, sys._getframe(1))
            for parser, args, kwargs in self.parser.stream(prompt, input):
                with shield:
                    self.parse_args(parser, args, kwargs)


class ArgumentApp[T](BaseApp[T]):
    _command: Callable[..., Any] | None

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
        self._parser = ArgumentParser(
            *names,
            brief=brief,
            detail=detail,
            docstring=docstring,
            formatter=formatter,
            state=ref(self),
            help_flags=help_flags,
        )
        self.state = state
        self._command = None

    @property
    def parser(self) -> ArgumentParser[ReferenceType[Self]]:
        return self._parser

    def command[T_: Callable](
        self,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
    ) -> Callable[[T_], T_]:
        def decorator(command: T_) -> T_:
            return self.add_command(
                command,
                *names,
                brief=brief,
                detail=detail,
                docstring=docstring,
            )

        return decorator

    def add_command[T_: Callable](
        self,
        command: T_,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
    ) -> T_:
        if self.has_command():
            raise SugarError("command already set")

        parser = self.parser

        # resolution order: __init__() > command()/add_command() > command

        if not parser._names:
            if not names:
                name = get_name(command, True)
                if name is not None:
                    names = (name,)
            parser._names = names

        if parser._brief is None:
            parser._brief = brief
        if parser._detail is None:
            parser._detail = detail
        if parser._docstring is None:
            if docstring is None:
                docstring = parse_from_object(command)
            parser._docstring = docstring

        if not parser._docstring:
            parser._docstring = parse_from_object(command)

        add_arguments_from_signature(parser, command)

        self._command = command
        return command

    @overload
    def get_command(
        self, ignore_error: Literal[False] = False
    ) -> Callable[..., Any]: ...
    @overload
    def get_command(self, ignore_error: bool) -> Callable[..., Any] | None: ...
    def get_command(self, ignore_error: bool = False) -> Callable[..., Any] | None:
        command = self._command
        if ignore_error or command is not None:
            return command
        raise SugarError("command not set")

    def has_command(self) -> bool:
        return self._command is not None

    def parse_args(
        self,
        parser: Parser[ReferenceType[App]],
        args: Sequence[str],
        kwargs: Mapping[str, Any],
    ) -> tuple[Self, Any]:
        assert isinstance(parser.state, ReferenceType), parser.state
        assert isinstance((sugar := parser.state()), ArgumentApp), sugar
        assert sugar is self, sugar

        with pop_traceback:
            command = self.get_command()
            return self, command(*args, **kwargs)


class CommandApp[T](BaseApp[T]):
    _apps: MutableMapping[str, ArgumentApp]

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
        self._parser = CommandParser(
            *names,
            brief=brief,
            detail=detail,
            docstring=docstring,
            formatter=formatter,
            state=ref(self),
            help_flags=help_flags,
        )
        self.state = state
        self._apps = {}

    @property
    def parser(self) -> CommandParser[ReferenceType[Self]]:
        return self._parser

    def command[T_: Callable](
        self,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
    ) -> Callable[[T_], T_]:
        def decorator(command: T_) -> T_:
            return self.add_command(
                command,
                *names,
                brief=brief,
                detail=detail,
                docstring=docstring,
            )

        return decorator

    def add_command[T_: Callable](
        self,
        command: T_,
        *names: str,
        brief: str | None = None,
        detail: str | None = None,
        docstring: Docstring | None = None,
    ) -> T_:
        app = ArgumentApp()
        app.add_command(
            command, *names, brief=brief, detail=detail, docstring=docstring
        )
        parser = app.parser
        self._parser.add_parser(parser)
        self._apps[parser.prog] = app
        return command

    @overload
    def get_app(self, name: str, ignore_error: Literal[False] = False) -> App[Any]: ...
    @overload
    def get_app(self, name: str, ignore_error: bool) -> App[Any] | None: ...
    def get_app(self, name: str, ignore_error: bool = False) -> App[Any] | None:
        subparser = self._parser.get_parser(name, ignore_error)
        return subparser.state()  # type: ignore

    def parse_args(
        self,
        parser: Parser[ReferenceType[App]],
        args: Sequence[str],
        kwargs: Mapping[str, Any],
    ) -> tuple[App, Any]:
        with pop_traceback:
            assert isinstance(parser.state, ReferenceType), parser.state

            app = parser.state()
            if app is None:
                raise SugarError("reference to app is dead")

            assert isinstance(app, ArgumentApp), app
            return app.parse_args(parser, args, kwargs)


@dataclasses.dataclass(slots=True)
class Meta:
    names: tuple[str, ...] | None = dataclasses.field(default=None)
    action: Action[Any] | None = dataclasses.field(default=None)
    help: str | None = dataclasses.field(default=None)


POSITIONAL_ONLY = Parameter.POSITIONAL_ONLY
POSITIONAL_OR_KEYWORD = Parameter.POSITIONAL_OR_KEYWORD
VAR_POSITIONAL = Parameter.VAR_POSITIONAL
KEYWORD_ONLY = Parameter.KEYWORD_ONLY
VAR_KEYWORD = Parameter.VAR_KEYWORD
EMPTY = Parameter.empty


def add_arguments_from_signature(
    parser: ArgumentParser,
    func: Callable[..., Any],
) -> None:
    sig = signature(func, eval_str=True)

    for dest, param in sig.parameters.items():
        names = None
        action = None
        help = None
        default = MISSING if param.default is EMPTY else param.default
        annotation = MISSING if param.annotation is EMPTY else param.annotation

        metadata = getattr(annotation, "__metadata__", None)

        if isinstance(metadata, tuple):
            for data in reversed(metadata):
                if isinstance(data, Meta):
                    names = data.names
                    action = data.action
                    help = data.help
                    break

        if action is None and annotation is not MISSING:
            action = auto(annotation)

        kind = param.kind

        if kind is POSITIONAL_ONLY:
            parser.add_positional_only(
                dest, names=names, action=action, help=help, default=default
            )
        elif kind is POSITIONAL_OR_KEYWORD:
            parser.add_positional_or_keyword(
                dest, names=names, action=action, help=help, default=default
            )
        elif kind is VAR_POSITIONAL:
            parser.add_var_positional(
                dest, names=names, action=action, help=help, default=default
            )
        elif kind is KEYWORD_ONLY:
            parser.add_keyword_only(
                dest, names=names, action=action, help=help, default=default
            )
        elif kind is VAR_KEYWORD:
            parser.add_var_keyword(
                dest, names=names, action=action, help=help, default=default
            )
        else:
            assert_never(kind)
