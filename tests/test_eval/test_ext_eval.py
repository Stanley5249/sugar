from itertools import chain
from typing import Any

import pytest

from sugar._eval import ext_eval

name_cases = [
    ("a", "a"),
    ("a1", "a1"),
    ("a_", "a_"),
    ("_", "_"),
    ("_a", "_a"),
    ("_1", "_1"),
]


str_cases = [
    ("''", ""),
    ('""', ""),
    ("'42'", "42"),
    ("'a'", "a"),
]


int_cases = [
    ("0", 0),
    ("42", 42),
    ("+42", 42),
    ("-42", -42),
    ("0b101010", 42),
    ("0B101010", 42),
    ("0o52", 42),
    ("0O52", 42),
    ("0x2a", 42),
    ("0X2A", 42),
    ("1_000", 1000),
]


float_cases = [
    ("0", 0.0),
    (".0", 0.0),
    ("0.", 0.0),
    ("0.0", 0.0),
    (".5", 0.5),
    ("0.5", 0.5),
    ("5e-1", 0.5),
    ("5E-1", 0.5),
    ("-0.5", -0.5),
    ("-5e-1", -0.5),
    ("-5E-1", -0.5),
]


complex_cases = [
    ("1+2j", 1 + 2j),
    ("1-2j", 1 - 2j),
    ("+1+2j", 1 + 2j),
    ("-1+2j", -1 + 2j),
    ("0.5+2j", 0.5 + 2j),
    ("1+2.5j", 1 + 2.5j),
    ("1.5+1.5j", 1.5 + 1.5j),
    ("1 + 2j", 1 + 2j),
]

bytes_cases = [
    ("b''", b""),
    ("B''", b""),
    ("b'42'", b"42"),
    ("b'a'", b"a"),
]

bool_cases = [("True", True), ("False", False)]

none_cases = [("None", None)]

ellipsis_cases = [("...", ...)]

empty_container_cases = [("()", ()), ("[]", []), ("{}", {}), ("set()", set())]

mixed_cases = [
    (
        "(0, [1, 2], {3, 4}, {'a': 5, 'b': 6}, 7 + 8j, set(), 'c', d)",
        (0, [1, 2], {3, 4}, {"a": 5, "b": 6}, 7 + 8j, set(), "c", "d"),
    )
]

valid_cases = chain(
    name_cases,
    str_cases,
    int_cases,
    float_cases,
    complex_cases,
    bytes_cases,
    bool_cases,
    none_cases,
    ellipsis_cases,
    empty_container_cases,
    mixed_cases,
)


@pytest.mark.parametrize(("source", "exp"), valid_cases)
def test_valid(source: str, exp: Any) -> None:
    assert ext_eval(source) == exp


syntax_error_cases = [
    "0a",
    "'",
    '"',
]


@pytest.mark.parametrize("source", syntax_error_cases)
def test_syntax_error(source: str) -> None:
    pytest.raises(SyntaxError, ext_eval, source)


value_error_cases = ["dict()", "set(args)", "{**kwargs}", "1j + 2j", "1 + 2"]


@pytest.mark.parametrize("source", value_error_cases)
def test_value_error(source: str) -> None:
    pytest.raises(ValueError, ext_eval, source)
