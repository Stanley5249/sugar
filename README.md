# 🍬Sugar

***Disclaimer**: This project is not yet production-ready and is actively seeking contributors.*

- [Overview](#overview)
- [Installation](#installation)
- [Basic Usage](#basic-usage)
- [Dependencies](#dependencies)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)

## Overview

Sugar leverages Python’s powerful typing system and syntactic sugar to simplify the creation of CLI programs, offering a delightful and user-friendly experience. It draws inspiration from the excellent projects [Typer](https://github.com/fastapi/typer) and [Python Fire](https://github.com/google/python-fire).

## Installation

You can install Sugar CLI using either `pip` or [`uv`](https://github.com/astral-sh/uv), an alternative package manager.

```sh
# using pip
pip install sugar-cli

# using uv
uv pip install sugar-cli
```

## Basic Usage

This section is for users unfamiliar with other CLI libraries. Below is a shared code snippet for the following examples.

```python
from sugar import *

def add(a: int, b: int) -> None:
    """Add two numbers."""
    print(f"{a} + {b} = {a + b}")

def sub(a: int, b: int) -> None:
    """Subtract two numbers."""
    print(f"{a} - {b} = {a - b}")
```

### Build the App

#### App without Subcommands

Use `ArgumentApp` ([example code](examples/usage_argument_app.py))

```python
app = ArgumentApp()

@app.command()
def add(a: int, b: int) -> int: ...
```

or `sugar` ([example code](examples/usage_without_cmds.py)).

```python
app = sugar(add)
```

#### App with Subcommands

Use `CommandApp` ([example code](examples/usage_command_app.py))

```python
app = CommandApp()

@app.command()
def add(a: int, b: int) -> int: ...

@app.command()
def sub(a: int, b: int) -> int: ...
```

or `sugar` ([example code](examples/usage_with_cmds.py)).

```python
app = sugar([add, sub])
```

### Execute the App

#### Run Mode

Use `run()` to execute it as a typical CLI program.

```python
if __name__ == "__main__":  
    app.run()
```

Example:

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

#### Cycle Mode

Use `cycle()` to enable a shell-like interface.

```python
if __name__ == "__main__":  
    app.cycle()
```

Example:

```
> python <FILENAME>.py  
Usage: <FILENAME>.py [MAGIC] <COMMAND> ...

Commands:
  add           Add two numbers.
  sub           Subtract two numbers.

Magic:
  --help, -h    show this help message and exit

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

### Documents

- [`mkdocs`](https://github.com/mkdocs/mkdocs)
- [`mkdocstrings[python]`](https://github.com/mkdocstrings/python)
- [`mkdocs-material`](https://github.com/squidfunk/mkdocs-material)

While it would be ideal to eliminate the dependency on `docstring-parser`, the complexity of handling various styles of docstrings makes it impractical to implement all of them ourselves. We are currently looking for better solutions.

## FAQ

### What does the name "Sugar" stand for?

**S**imple  
**U**tility for  
**G**enerating  
**A**rgument  
**R**unners

While the acronym might be a bit of a stretch, it has a nice ring to it. In reality, "Sugar" refers to syntactic sugar, which makes the code more readable and easier to write.

### Why Run a CLI Program as a Shell?

Quick response times are crucial for a good user experience in CLI programs. Running a CLI program as a shell helps avoid repeatedly loading heavy modules, making subsequent commands respond quicker. This is particularly important for researchers using deep learning frameworks like PyTorch and TensorFlow, which can take a second to initialize.

Another way to reduce loading times is through lazy imports. Some projects use the [`lazy-loader`](https://github.com/scientific-python/lazy-loader) from Scientific-Python, which is an effective solution. Additionally, Sugar offers an experimental submodule for lazy importing within a context manager. For more details, see the Experimental section.

### Why Did We Start the Project?

We embarked on this project after being inspired by the [Command Line Interface Guidelines](https://clig.dev), which shed light on the chaotic nature of CLI environments:

> The world of the terminal is a mess. Inconsistencies are everywhere, slowing us down and making us second-guess ourselves.

Existing CLI libraries are riddled with ambiguities that frustrated us. For instance, the command `--FLAG 1 2` can be interpreted in multiple ways: either `1` is an option for `FLAG` and `2` is positional, or both `1` and `2` are options for `FLAG`. This behavior varies based on the parser's design and other factors. We believe that argument parsers should be stateless, meaning the parser's settings should not influence the role of any arguments. Arguments that appear before the first keyword (flag or option) are treated as positional arguments, while arguments that appear between flags are associated with the preceding flag.

This issue is just one example of many that motivated us to develop a new library. While it may not yet be perfect, we are continually seeking better solutions to these problems. Our goal is to establish a standard that enhances productivity and user satisfaction, ultimately becoming the new norm for CLIs.

As Jef Raskin stated in The Humane Interface, "Abandon a standard when it is demonstrably harmful to productivity or user satisfaction." For more details, see [Chaos](https://clig.dev/#chaos).

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub. For more detailed guidelines, refer to the [CONTRIBUTING.md](.github/CONTRIBUTING.md) file.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Authors

- Huang, Hong-Chang (seer852741@gmail.com)

