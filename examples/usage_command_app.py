from sugar import CommandApp

app = CommandApp()


@app.command()
def add(a: int, b: int) -> None:
    """Add two numbers."""
    print(f"{a} + {b} = {a + b}")


@app.command()
def sub(a: int, b: int) -> None:
    """Subtract two numbers."""
    print(f"{a} - {b} = {a - b}")


if __name__ == "__main__":
    app.run()
