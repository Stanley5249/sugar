"""Demonstrates the use of the 'Action' classes."""

from typing import Annotated

from sugar import ArgumentApp, Meta, Store

app = ArgumentApp()


@app.command()
def func(
    verbose: Annotated[bool, Meta(("v", "verbose"), Store(True))] = False,
) -> None:
    """Print the value of 'verbose'."""
    print(f"{verbose = }")


if __name__ == "__main__":
    app.cycle()
