import collections.abc
import typing

import pytest

from sugar._action import (
    Build,
    Converter,
    KeywordToken,
    PositionalToken,
    Record,
    Store,
    auto,
)
from sugar.exception import SugarError

POS_TOKEN_INT_42 = PositionalToken("", "42")
POS_TOKEN_STR_A = PositionalToken("", "a")
POS_TOKEN_NONE = PositionalToken("", "None")

POS_TOKEN_LIST_OF_INT = PositionalToken("", "[1, 2, 3]")
POS_TOKEN_LIST_OF_STR = PositionalToken("", "['1', '2', '3']")
POS_TOKEN_LIST_OF_UNION = PositionalToken("", "[1, '2', 3]")

POS_TOKEN_TUPLE_INT_STR = PositionalToken("", "1, '1'")
POS_TOKEN_TUPLE_STR_INT = PositionalToken("", "'1', 1")
POS_TOKEN_TUPLE_INT_ELLIPSIS = PositionalToken("", "1, 2, 3")

POS_TOKEN_DICT_INT_TO_STR = PositionalToken("", "{1: '1', 2: '2', 3: '3'}")
POS_TOKEN_DICT_STR_TO_INT = PositionalToken("", "{'1': 1, '2': 2, '3': 3}")

KW_TOKEN_EMPTY = KeywordToken("", [], 1)

KW_TOKEN_LIST_OF_INT = KeywordToken("", ["1", "2", "3"], 1)
KW_TOKEN_LIST_OF_STR = KeywordToken("", ["'1'", "'2'", "'3'"], 1)
KW_TOKEN_LIST_OF_UNION = KeywordToken("", ["1", "'2'", "3"], 1)

KW_TOKEN_TUPLE_INT_STR = KeywordToken("", ["1", "'1'"], 1)
KW_TOKEN_TUPLE_STR_INT = KeywordToken("", ["'1'", "1"], 1)
KW_TOKEN_TUPLE_INT_ELLIPSIS = KeywordToken("", ["1", "2", "3"], 1)

KW_TOKEN_DICT_INT_TO_STR = KeywordToken("", ["{1: '1', 2: '2', 3: '3'}"], 1)
KW_TOKEN_DICT_STR_TO_INT = KeywordToken("", ["{'1': 1, '2': 2, '3': 3}"], 1)

# ================================================================================
# Primitives
# ================================================================================


def test_none() -> None:
    action = auto(None)
    assert isinstance(action, Store)
    assert action.call_keyword(KW_TOKEN_EMPTY) is None


type IntType = int
type StrType = str


@pytest.mark.parametrize("tp", [int, IntType])
def test_int(tp: typing.Any) -> None:
    action = auto(tp)
    assert isinstance(action, Converter)
    assert action.call_positional(POS_TOKEN_INT_42) == 42
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_STR_A)
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_NONE)


@pytest.mark.parametrize("tp", [str, StrType])
def test_str(tp: typing.Any) -> None:
    action = auto(tp)
    assert isinstance(action, Converter)
    assert action.call_positional(POS_TOKEN_INT_42) == "42"
    assert action.call_positional(POS_TOKEN_STR_A) == "a"
    assert action.call_positional(POS_TOKEN_NONE) == "None"


def test_any() -> None:
    action = auto(typing.Any)
    assert isinstance(action, Converter)
    assert action.call_positional(POS_TOKEN_INT_42) == 42
    assert action.call_positional(POS_TOKEN_STR_A) == "a"
    assert action.call_positional(POS_TOKEN_NONE) is None


# ================================================================================
# typing.Union, typing.Optional, and types.UnionType
# ================================================================================


@pytest.mark.parametrize("tp", [int | str, typing.Union[int, str]])
def test_union(tp: typing.Any) -> None:
    action = auto(tp)
    assert isinstance(action, Converter)
    assert action.call_positional(POS_TOKEN_INT_42) == 42
    assert action.call_positional(POS_TOKEN_STR_A) == "a"
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_NONE)


@pytest.mark.parametrize(
    "tp", [int | None, typing.Union[int, None], typing.Optional[int]]
)
def test_optional(tp: typing.Any) -> None:
    action = auto(tp)
    assert isinstance(action, Converter)
    assert action.call_positional(POS_TOKEN_INT_42) == 42
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_STR_A)
    assert action.call_positional(POS_TOKEN_NONE) is None


# ================================================================================
# list
# ================================================================================


@pytest.mark.parametrize(
    "tp", [list, typing.List, typing.Sequence, collections.abc.Sequence]
)
def test_list(tp: typing.Any) -> None:
    action = auto(tp)
    assert isinstance(action, Build)

    assert action.call_positional(POS_TOKEN_LIST_OF_INT) == [1, 2, 3]
    assert action.call_positional(POS_TOKEN_LIST_OF_STR) == ["1", "2", "3"]
    assert action.call_positional(POS_TOKEN_LIST_OF_UNION) == [1, "2", 3]

    assert action.call_keyword(KW_TOKEN_EMPTY) == []
    assert action.call_keyword(KW_TOKEN_LIST_OF_INT) == [1, 2, 3]
    assert action.call_keyword(KW_TOKEN_LIST_OF_STR) == ["1", "2", "3"]
    assert action.call_keyword(KW_TOKEN_LIST_OF_UNION) == [1, "2", 3]


@pytest.mark.parametrize(
    "tp",
    [list[int], typing.List[int], typing.Sequence[int], collections.abc.Sequence[int]],
)
def test_list_of_int(tp: typing.Any) -> None:
    action = auto(tp)
    assert isinstance(action, Build)

    assert action.call_positional(POS_TOKEN_LIST_OF_INT) == [1, 2, 3]
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_LIST_OF_STR)
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_LIST_OF_UNION)

    assert action.call_keyword(KW_TOKEN_EMPTY) == []
    assert action.call_keyword(KW_TOKEN_LIST_OF_INT) == [1, 2, 3]
    pytest.raises(SugarError, action.call_keyword, KW_TOKEN_LIST_OF_STR)
    pytest.raises(SugarError, action.call_keyword, KW_TOKEN_LIST_OF_UNION)


# ================================================================================
# dict
# ================================================================================


def test_dict() -> None:
    action = auto(dict)
    assert isinstance(action, Converter)

    pytest.raises(SugarError, action.call_keyword, KW_TOKEN_EMPTY)
    assert action.call_positional(POS_TOKEN_DICT_INT_TO_STR) == {1: "1", 2: "2", 3: "3"}
    assert action.call_keyword(KW_TOKEN_DICT_INT_TO_STR) == {1: "1", 2: "2", 3: "3"}


def test_dict_of_int_to_str() -> None:
    action = auto(dict[int, str])
    assert isinstance(action, Converter)

    assert action.call_positional(POS_TOKEN_DICT_INT_TO_STR) == {1: "1", 2: "2", 3: "3"}
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_DICT_STR_TO_INT)
    pytest.raises(SugarError, action.call_keyword, KW_TOKEN_DICT_STR_TO_INT)


# ================================================================================
# tuple
# ================================================================================


def test_tuple() -> None:
    action = auto(tuple)
    assert isinstance(action, Build)

    assert action.call_keyword(KW_TOKEN_EMPTY) == ()

    assert action.call_positional(POS_TOKEN_TUPLE_INT_STR) == (1, "1")
    assert action.call_positional(POS_TOKEN_TUPLE_STR_INT) == ("1", 1)

    assert action.call_keyword(KW_TOKEN_TUPLE_INT_STR) == (1, "1")
    assert action.call_keyword(KW_TOKEN_TUPLE_STR_INT) == ("1", 1)


def test_tuple_of_int_str() -> None:
    action = auto(tuple[int, str])
    assert isinstance(action, Record)

    assert action.call_keyword(KW_TOKEN_EMPTY) == ()

    assert action.call_positional(POS_TOKEN_TUPLE_INT_STR) == (1, "1")
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_TUPLE_STR_INT)

    assert action.call_keyword(KW_TOKEN_TUPLE_INT_STR) == (1, "1")
    pytest.raises(SugarError, action.call_keyword, KW_TOKEN_TUPLE_STR_INT)


def test_tuple_of_int_ellipsis() -> None:
    action = auto(tuple[int, ...])
    assert isinstance(action, Build)

    assert action.call_keyword(KW_TOKEN_EMPTY) == ()
    assert action.call_positional(POS_TOKEN_TUPLE_INT_ELLIPSIS) == (1, 2, 3)
    assert action.call_keyword(KW_TOKEN_TUPLE_INT_ELLIPSIS) == (1, 2, 3)


# ================================================================================
# recursive types
# ================================================================================

type A = list[A] | int
type B = int | list[B]
type C = list[C]

POS_TOKEN_RECURSION_UNION = PositionalToken("", "[1, [2, [3]]]")
POS_TOKEN_RECURSION_LIST = PositionalToken("", "[[], [[]], [[], [[]]]]")
KW_TOKEN_RECURSION_LIST = KeywordToken("", ["[]", "[[]]", "[[], [[]]]"], 1)


@pytest.mark.parametrize("tp", [A, B])
def test_recursion(tp) -> None:
    action = auto(tp)
    assert isinstance(action, Converter)

    assert action.call_positional(POS_TOKEN_INT_42) == 42
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_STR_A)
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_NONE)

    assert action.call_positional(POS_TOKEN_LIST_OF_INT) == [1, 2, 3]
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_LIST_OF_STR)
    assert action.call_positional(POS_TOKEN_RECURSION_UNION) == [1, [2, [3]]]


def test_recursion_c() -> None:
    action = auto(C)
    assert isinstance(action, Build)

    assert action.call_keyword(KW_TOKEN_EMPTY) == []
    assert action.call_positional(POS_TOKEN_RECURSION_LIST) == [[], [[]], [[], [[]]]]
    assert action.call_keyword(KW_TOKEN_RECURSION_LIST) == [[], [[]], [[], [[]]]]

    pytest.raises(SugarError, action.call_positional, POS_TOKEN_LIST_OF_INT)
    pytest.raises(SugarError, action.call_positional, POS_TOKEN_RECURSION_UNION)
