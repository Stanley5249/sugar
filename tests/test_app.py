from typing import Any

from sugar import ArgumentApp, CommandApp, sugar

argv = "'Hello world!' 42 0.0 1.0 2.0 --kw-only a b c --kw1 1 --kw2 \"'2'\" --kw3 3.0"
argv_with_cmd = "func " + argv


def func(
    pos_only: str,
    /,
    pos_or_kw: int,
    *args: float,
    kw_only: list[str],
    **kwargs: Any,
) -> None:
    assert isinstance(pos_only, str)
    assert pos_only == "Hello world!"

    assert isinstance(pos_or_kw, int)
    assert pos_or_kw == 42

    assert isinstance(args, tuple)
    assert all([isinstance(i, float) for i in args])

    assert args == (0.0, 1.0, 2.0)
    assert isinstance(kw_only, list)
    assert all([isinstance(i, str) for i in kw_only])
    assert kw_only == ["a", "b", "c"]

    assert isinstance(kwargs, dict)
    assert kwargs == {"kw1": 1, "kw2": "2", "kw3": 3.0}


def test_argument_app_command_decoractor() -> None:
    app = ArgumentApp()
    app.command()(func)
    assert app.get_command() is func


def test_argument_app_add_command() -> None:
    app = ArgumentApp()
    app.add_command(func)
    assert app.get_command() is func


def test_command_app_command_decoractor() -> None:
    app = CommandApp()
    app.command()(func)
    subapp = app.get_subapp("func")
    assert isinstance(subapp, ArgumentApp)
    assert subapp.get_command() is func


def test_command_app_add_command() -> None:
    app = CommandApp()
    app.add_command(func)
    subapp = app.get_subapp("func")
    assert isinstance(subapp, ArgumentApp)
    assert subapp.get_command() is func


def test_argument_app_run() -> None:
    app = ArgumentApp()
    app.add_command(func)
    app.run(argv)


def test_command_app_run() -> None:
    app = CommandApp()
    app.add_command(func)
    app.run(argv_with_cmd)


def test_run_callable() -> None:
    sugar(func).run(argv)


def test_run_sequence() -> None:
    sugar([func]).run(argv_with_cmd)


if __name__ == "__main__":
    sugar(func).run(argv)
