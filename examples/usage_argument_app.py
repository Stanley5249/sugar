from sugar import ArgumentApp

app = ArgumentApp()


@app.command()
def add(a: int, b: int) -> None:
    """Add two numbers."""
    print(f"{a} + {b} = {a + b}")


if __name__ == "__main__":
    app.run()
