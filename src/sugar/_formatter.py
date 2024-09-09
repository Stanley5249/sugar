import dataclasses
from collections.abc import Collection, Iterable, Iterator, Mapping
from itertools import chain, groupby, zip_longest
from textwrap import wrap
from typing import IO, Protocol


class SupportsStrings(Protocol):
    def to_strings(self) -> list[str]: ...


class Formatter(Protocol):
    def write_exception(self, io: IO[str], exc: BaseException) -> None: ...

    def write_usage(self, io: IO[str], path: list[str], usage: str): ...

    def write_paragraph(self, io: IO[str], text: str | None) -> None: ...

    def write_tables(
        self, io: IO[str], raw_tables: Mapping[str, Collection[SupportsStrings]]
    ) -> None: ...


@dataclasses.dataclass()
class DefaultFormatter(Formatter):
    max_width: int = dataclasses.field(default=80)
    col_width: int = dataclasses.field(default=6)
    indent: str = dataclasses.field(default="  ")

    def write_exception(self, io: IO[str], exc: BaseException) -> None:
        io.writelines(["Error: ", str(exc), "\n"])
        notes = getattr(exc, "__notes__", None)
        if notes:
            io.writelines(["\nDetails:\n"])
            for i, note in enumerate(notes, 1):
                io.writelines([self.indent, f"{i}", ". ", note, "\n"])

    def write_usage(self, io: IO[str], path: list[str], usage: str) -> None:
        io.write("Usage:")
        for name in path:
            io.writelines([" ", name])
        io.writelines([" ", usage, "\n\n"])

    def write_paragraph(self, io: IO[str], text: str | None) -> None:
        if text is None:
            return
        for g in split_sections(text):
            for lines in g:
                for line in wrap(lines, width=self.max_width):
                    io.writelines([line, "\n"])
            io.write("\n")

    def write_tables(
        self, io: IO[str], raw_tables: Mapping[str, Collection[SupportsStrings]]
    ) -> None:
        tables = [
            [spec.to_strings() for spec in specs] for specs in raw_tables.values()
        ]
        widths = get_min_widths(chain.from_iterable(tables))
        widths = ceil_to_multiple(widths, self.col_width)

        for title, table in zip(raw_tables, tables):
            if table:
                io.writelines([title, ":\n"])
                for cols in table:
                    for c, w in zip(cols, widths):
                        io.writelines([self.indent, c.ljust(w)])
                    io.write("\n")
                io.write("\n")


def split_sections(text: str) -> Iterator[Iterator[str]]:
    for k, g in groupby(text.splitlines(), key=bool):
        if k:
            yield g


def get_min_widths(table: Iterable[list[str]], min_width: int = 0) -> list[int]:
    return [
        *map(max, zip_longest(*[map(len, row) for row in table], fillvalue=min_width))
    ]


def ceil_to_multiple(nums: Iterable[int], mul: int) -> list[int]:
    d = mul - 1
    return [(i + d) // mul * mul for i in nums]


DEFAULT_FORMATTER = DefaultFormatter()
