import pytest

from sugar._parser import separate_argv
from sugar.exception import SugarError

argv_cases = [
    (
        [],
        ([], []),
    ),
    (
        ["0", "1"],
        (["0", "1"], []),
    ),
    (
        ["-a", "-b"],
        ([], [("a", []), ("b", [])]),
    ),
    (
        ["--apple", "--banana"],
        ([], [("apple", []), ("banana", [])]),
    ),
    (
        ["-a", "0", "1"],
        ([], [("a", ["0", "1"])]),
    ),
    (
        ["-a", "0", "-b", "1"],
        ([], [("a", ["0"]), ("b", ["1"])]),
    ),
    (
        ["-a", "0", "1", "-b", "2", "3"],
        ([], [("a", ["0", "1"]), ("b", ["2", "3"])]),
    ),
    (
        ["--apple", "0", "1"],
        ([], [("apple", ["0", "1"])]),
    ),
    (
        ["--apple", "0", "--banana", "1"],
        ([], [("apple", ["0"]), ("banana", ["1"])]),
    ),
    (
        ["--apple", "0", "1", "--banana", "2", "3"],
        ([], [("apple", ["0", "1"]), ("banana", ["2", "3"])]),
    ),
    (
        ["0", "1", "-a", "2", "3"],
        (["0", "1"], [("a", ["2", "3"])]),
    ),
    (
        ["0", "1", "--apple", "2", "3"],
        (["0", "1"], [("apple", ["2", "3"])]),
    ),
    (
        ["-a", "0", "1", "--apple", "2", "3"],
        ([], [("a", ["0", "1"]), ("apple", ["2", "3"])]),
    ),
    (
        ["0", "1", "-a", "2", "3", "--banana", "4", "5"],
        (["0", "1"], [("a", ["2", "3"]), ("banana", ["4", "5"])]),
    ),
    (
        ["-abc"],
        ([], [("a", []), ("b", []), ("c", [])]),
    ),
    (
        ["-abc", "0", "1"],
        ([], [("a", []), ("b", []), ("c", ["0", "1"])]),
    ),
    (
        ["0", "1", "-abc", "2", "3"],
        (["0", "1"], [("a", []), ("b", []), ("c", ["2", "3"])]),
    ),
    (
        ["0", "1", "-abc", "2", "3", "--dog", "4", "5"],
        (["0", "1"], [("a", []), ("b", []), ("c", ["2", "3"]), ("dog", ["4", "5"])]),
    ),
]


@pytest.mark.parametrize(("argv", "exp"), argv_cases)
def test_separate(
    argv: list[str],
    exp: tuple[list[str], list[tuple[str, list[str]]]],
) -> None:
    assert separate_argv(argv) == exp


invalid_flag_cases = (["--"], ["--1"])


@pytest.mark.parametrize("argv", invalid_flag_cases)
def test_invalid_flag(argv: list[str]) -> None:
    pytest.raises(SugarError, separate_argv, argv)
