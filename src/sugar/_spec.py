import dataclasses
from functools import cache
from typing import Any

from sugar._action import Action, Event
from sugar._constant import MISSING


@dataclasses.dataclass(eq=False, frozen=True)
class ArgumentSpec:
    names: tuple[str, ...] = dataclasses.field()
    action: Action[Any] = dataclasses.field()
    help: str = dataclasses.field()
    default: Any = dataclasses.field()

    def join_names(self) -> str:
        return ", ".join(map(to_flag, self.names))

    @cache
    def to_strings(self) -> list[str]:
        return [
            self.join_names(),
            self.action.name,
            self.help,
            "[required]" if self.default is MISSING else f"{self.default!r}",
        ]


class PositionalSpec(ArgumentSpec):
    def join_names(self) -> str:
        return ", ".join(self.names)


@dataclasses.dataclass(eq=False, frozen=True)
class MagicSpec:
    names: tuple[str, ...] = dataclasses.field()
    help: str = dataclasses.field()
    action: Event = dataclasses.field()

    def join_names(self) -> str:
        return ", ".join(map(to_flag, self.names))

    def to_strings(self) -> list[str]:
        return [self.join_names(), self.help]


def to_flag(name: str) -> str:
    return f"-{name}" if len(name) == 1 else f"--{name}"
