# 🍬Sugar

A Python CLI library inspired by the excellent projects [typer](https://github.com/fastapi/typer) and [fire](https://github.com/google/python-fire).

## Overview

Sugar leverages Python's powerful typing system and syntactic sugar to quickly create CLI programs, offering a delightful and user-friendly experience.

**Disclaimer: This project is not yet production ready.**

## Installation

You can install Sugar CLI using either `pip` or [`uv`](https://github.com/astral-sh/uv), an alternative package manager.

```sh
# using pip
pip install sugar-cli

# using uv
uv pip install sugar-cli
```

## Basic Usage

This section is for those who are not familar with other CLI libraries.

Below a common header shared by the following examples.

```python
from sugar import *

def add(a: int, b: int) -> None:
    """Add two numbers."""
    print(f"{a} + {b} = {a + b}")

def sub(a: int, b: int) -> None:
    """Subtract two numbers."""
    print(f"{a} - {b} = {a - b}")
```

### One-liner Approach

This approach is similar to `fire`.

For an app without subcommands:

[examples\usage_without_cmds.py](examples\usage_without_cmds.py)

```python
if __name__ == "__main__":
    sugar(add)
```

For an app with subcommands:

[examples\usage_with_cmds.py](examples\usage_with_cmds.py)

```python
if __name__ == "__main__":
    sugar([add, sub])
```

### Decorator-based Approach

This approach is similar to `typer`.

For an app without subcommands:

[examples\usage_argument_app.py](examples\usage_argument_app.py)

```python
app = ArgumentApp()

@app.command()
def add(a: int, b: int) -> int: ...

if __name__ == "__main__":
    app.run()
```

For an app with subcommands:

[examples\usage_command_app.py](examples\usage_command_app.py)

```python
app = CommandApp()

@app.command()
def add(a: int, b: int) -> int: ...

@app.command()
def sub(a: int, b: int) -> int: ...

if __name__ == "__main__":
    app.run()
```

### Run

For an app without subcommands:

```
> python <FILENAME>.py 1 2
1 + 2 = 3
> python <FILENAME>.py --help
Usage: <FILENAME> [MAGIC] [POSITIONAL] [KEYWORD]

Add two numbers.

Positional or keyword:
  -a      int       [required]
  -b      int       [required]

Magic:
  --help, -h    show this help message and exit
```

For an app with subcommands:

```
> python <FILENAME>.py add 1 2
1 + 2 = 3
> python <FILENAME>.py -h
Usage: <FILENAME>.py [MAGIC] <COMMAND> ...

Commands:
  add           Add two numbers.
  sub           Subtract two numbers.

Magic:
  --help, -h    show this help message and exit
```

### Shell

[examples\usage_shell.py](examples\usage_shell.py)

To turn a CLI program into a shell-like program, replace `run` with `cycle`.

```python
if __name__ == "__main__":
    app.cycle()
```

You don't have to pass arguments with the python command.

```
> python <FILENAME>.py  
Usage: <FILENAME>.py [MAGIC] <COMMAND> ...

Commands:
  add           Add two numbers.
  sub           Subtract two numbers.

Magic:
  --help, -h    show this help message and exit

>>>
```

It'll print the help message and wait for your instructions.

```
>>> add 1 2
1 + 2 = 3
>>>
```

## Dependencies

### Required

- [`docstring-parser`](https://github.com/rr-/docstring_parser): For parsing docstrings.

### Development

- [`pytest`](https://github.com/pytest-dev/pytest): For running tests.
- [`ruff`](https://github.com/astral-sh/ruff): For linting and formatting.
- [`uv`](https://github.com/astral-sh/uv): For dependency management.

While it would be ideal to eliminate the dependency on `docstring-parser`, the complexity of handling various styles of docstrings makes it impractical to implement all of them ourselves. We are currently looking for better solutions.

## Testing

To run the tests, use [`pytest`](https://github.com/pytest-dev/pytest):

```sh
pytest tests
```

Make sure to install all required dependencies before running the tests.

## FAQ

### What does the name "Sugar" stand for?

**S**imple  
**U**tility for  
**G**enerating  
**A**rgument  
**R**unners

Although the acronym is a bit of a stretch, it has a nice ring to it. The real answer is that "Sugar" refers to syntactic sugar, which makes the code more readable and easier to write.

### Why Run a CLI Program as a Shell?

The answer is to avoid long start-up times when importing heavy modules. In recent years, many researchers use deep learning frameworks like PyTorch and TensorFlow, which often take a second to warm up. For CLI programs, it is better to have a quick response time to provide a better user experience. Using a shell, you only load things once, and the shell will handle exceptions.

Another approach to avoid long loading times is lazy import. Some projects rely on [`lazy-loader`](https://github.com/scientific-python/lazy-loader) from Scientific-Python, which is also a good choice. Additionally, Sugar has an experimental submodule for lazily importing libraries inside a context manager. See the Experimental section for details.

### Why Did We Start the Project?

Before starting this project, we read a great site called [Command Line Interface Guidelines](https://clig.dev). It highlighted the chaos of CLI:

> The world of the terminal is a mess. Inconsistencies are everywhere, slowing us down and making us second-guess ourselves.

Existing CLI libraries have many ambiguities that bothered us a lot. For example, in most libraries, `--FLAG 1 2` can be parsed in different ways: either `1` is an option of `FLAG` and `2` is positional, or both `1` and `2` belong to `FLAG`. The behavior depends on how the parser is built or other details. In our humble opinion, it should always be the latter, and positional arguments should always come before flags.

The above example is just the tip of the iceberg. It pushed us to write a whole new library. It may not be definitively better than others, as we are still finding better ways to solve these problems. However, we hope a standard can be established and ultimately become the new norm for CLIs.

Also from the section:

> "Abandon a standard when it is demonstrably harmful to productivity or user satisfaction." — Jef Raskin, [The Humane Interface](https://en.wikipedia.org/wiki/The_Humane_Interface)

See [Chaos](https://clig.dev/#chaos) for the original lines.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub. For more detailed guidelines, refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors

- Huang, Hong-Chang (seer852741@gmail.com)

