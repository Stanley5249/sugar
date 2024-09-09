from pprint import pp

from sugar import ArgumentApp

app = ArgumentApp()


@app.command()
def func(p0, p1, /, p2, p3, *args, k1, k2, **kwargs) -> None:
    """Test function with all parameter kinds.

    Look at the output of this function to see how the parameters are passed.

    Args:
        p0: Positional-only parameter.
        p1: Positional-only parameter.
        p2: Positional or keyword parameter.
        p3: Positional or keyword parameter
        args: Variadic positional arguments.
        k1: Keyword-only parameter.
        k2: Keyword-only parameter.
        kwargs: Variadic keyword arguments.
    """
    pp(
        {
            "p0": p0,
            "p1": p1,
            "p2": p2,
            "p3": p3,
            "args": args,
            "k1": k1,
            "k2": k2,
            "kwargs": kwargs,
        }
    )


if __name__ == "__main__":
    app.run()
