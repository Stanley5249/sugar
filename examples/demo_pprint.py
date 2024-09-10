"""Demonstrates the experimental 'auto_pprint' feature."""

from pprint import pp
from typing import Annotated

from sugar import CommandApp, Meta, Store
from sugar.experimental import auto_pprint

auto_pprint.enable()

app = CommandApp()


@app.command()
def show(
    pretty: Annotated[
        bool,
        Meta(("p", "pretty"), Store(True), "if True, use pretty print"),
    ] = False,
) -> None:
    """Show the application."""
    if pretty:
        pp(app)
    else:
        print(app)


if __name__ == "__main__":
    app.cycle()
