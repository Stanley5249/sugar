import collections.abc
import typing

import pytest

from sugar._action import ext_isinstance


def test_test() -> None:
    assert ext_isinstance(
        ([1, 2, 3], {4, 5, 6}, (7, 8, 9)),
        tuple[list[int], set[int], tuple[int, int, int]],
    )


# ================================================================================
# Primitives
# ================================================================================


def test_none() -> None:
    pytest.raises(TypeError, ext_isinstance, None, None)


def test_int() -> None:
    tp = int
    assert ext_isinstance(42, tp)
    assert not ext_isinstance("42", tp)


def test_str() -> None:
    tp = str
    assert not ext_isinstance(42, tp)
    assert ext_isinstance("42", tp)


def test_any() -> None:
    tp = typing.Any
    assert ext_isinstance(42, tp)
    assert ext_isinstance("42", tp)
    assert ext_isinstance(None, tp)


# ================================================================================
# typing.Union, typing.Optional, and types.UnionType
# ================================================================================


def test_types_union_type() -> None:
    tp = int | str
    assert ext_isinstance(42, tp)
    assert ext_isinstance("42", tp)


def test_typing_union() -> None:
    tp = typing.Union[int, str]
    assert ext_isinstance(42, tp)
    assert ext_isinstance("42", tp)


def test_types_union_type_with_none() -> None:
    tp = int | None
    assert ext_isinstance(42, tp)
    assert ext_isinstance(None, tp)


def test_typing_union_with_None() -> None:
    tp = typing.Union[int, None]
    assert ext_isinstance(42, tp)
    assert ext_isinstance(None, tp)


# ================================================================================
# list
# ================================================================================


def test_list() -> None:
    tp = list
    assert ext_isinstance([], tp)
    assert ext_isinstance([1, "2", 3], tp)
    assert not ext_isinstance((1, "2", 3), tp)


def test_list_of_int() -> None:
    tp = list[int]
    assert ext_isinstance([], tp)
    assert ext_isinstance([1, 2, 3], tp)
    assert not ext_isinstance([1, "2", 3], tp)
    assert not ext_isinstance(["1", "2", "3"], tp)


def test_list_of_union() -> None:
    tp = list[int | str]
    assert ext_isinstance([1, 2, 3], tp)
    assert ext_isinstance([1, "2", 3], tp)
    assert ext_isinstance(["1", "2", "3"], tp)


def test_list_of_list_of_int() -> None:
    tp = list[list[int]]
    assert ext_isinstance([[1, 2, 3], [4, 5, 6]], tp)
    assert not ext_isinstance([[1, "2", 3], [4, 5, 6]], tp)
    assert not ext_isinstance([[1, "2", 3], [4, "5", 6]], tp)
    assert not ext_isinstance([["1", "2", "3"], [4, "5", 6]], tp)
    assert not ext_isinstance([["1", "2", "3"], ["4", "5", "6"]], tp)


def test_list_of_list_of_union() -> None:
    tp = list[list[int | str]]
    assert ext_isinstance([[1, 2, 3], [4, 5, 6]], tp)
    assert ext_isinstance([[1, "2", 3], [4, 5, 6]], tp)
    assert ext_isinstance([[1, "2", 3], [4, "5", 6]], tp)
    assert ext_isinstance([["1", "2", "3"], [4, "5", 6]], tp)
    assert ext_isinstance([["1", "2", "3"], ["4", "5", "6"]], tp)


def test_list_of_list_of_int_or_list_of_str() -> None:
    tp = list[list[int] | list[str]]
    assert ext_isinstance([[1, 2, 3], [4, 5, 6]], tp)
    assert not ext_isinstance([[1, "2", 3], [4, 5, 6]], tp)
    assert not ext_isinstance([[1, "2", 3], [4, "5", 6]], tp)
    assert not ext_isinstance([["1", "2", "3"], [4, "5", 6]], tp)
    assert ext_isinstance([["1", "2", "3"], ["4", "5", "6"]], tp)


def test_list_of_any() -> None:
    tp = list[typing.Any]
    assert ext_isinstance([], tp)
    assert ext_isinstance([1, "2", 3], tp)
    assert ext_isinstance([1, "2", 3, None], tp)


# ================================================================================
# dict
# ================================================================================


def test_dict() -> None:
    tp = dict
    assert ext_isinstance({}, tp)
    assert ext_isinstance({1: "1", 2: "2", 3: "3"}, tp)
    assert not ext_isinstance(set(), tp)


def test_dict_of_int_to_str() -> None:
    tp = dict[int, str]
    assert ext_isinstance({}, tp)
    assert ext_isinstance({1: "1", 2: "2", 3: "3"}, tp)
    assert not ext_isinstance({"1": "1", "2": "2", "3": "3"}, tp)
    assert not ext_isinstance({"1": 1, "2": 2, "3": 3}, tp)
    assert not ext_isinstance({1: 1, 2: 2, 3: 3}, tp)


def test_dict_of_unknown() -> None:
    """The function 'ext_isinstance' should raise a 'TypeError' when receiving a dict[()], but currently it does not. This issue arises due to the behavior of 'typing.get_origin' and 'typing.get_args', which do not differentiate between 'dict[()]' and 'typing.Dict'."""

    # tp = dict[()]  # type: ignore
    # pytest.raises(TypeError, ext_isinstance, {"1": "1", "2": "2", "3": "3"}, tp)


def test_dict_of_int_to_unknown() -> None:
    tp = dict[int]  # type: ignore
    pytest.raises(TypeError, ext_isinstance, {"1": "1", "2": "2", "3": "3"}, tp)


# ================================================================================
# collections.abc and typing
# ================================================================================


def test_collection_abc_sequence() -> None:
    obj = [1, 2, 3]
    tp = collections.abc.Sequence
    assert ext_isinstance(obj, tp)
    assert ext_isinstance(obj, tp[int])
    assert not ext_isinstance(obj, tp[str])


def test_typing_sequence() -> None:
    obj = [1, 2, 3]
    tp = typing.Sequence
    assert ext_isinstance(obj, tp)
    assert ext_isinstance(obj, tp[int])
    assert not ext_isinstance(obj, tp[str])


def test_typing_list() -> None:
    obj = [1, 2, 3]
    tp = typing.List
    assert ext_isinstance(obj, tp)
    assert ext_isinstance(obj, tp[int])
    assert not ext_isinstance(obj, tp[str])


# ================================================================================
# typing.TypeAliasType
# ================================================================================

type IntType = int
type A = list[A] | int
type B = int | list[B]
type C = list[C]


def test_typing_type_alias_type() -> None:
    assert ext_isinstance(42, IntType)


def test_typing_type_alias_type_with_left_recursion() -> None:
    assert ext_isinstance(42, A)
    assert ext_isinstance([1, 2, 3], A)
    assert ext_isinstance([42, [1, 2, 3]], A)
    assert not ext_isinstance([42, ""], A)


def test_typing_type_alias_type_with_right_recursion() -> None:
    assert ext_isinstance(42, B)
    assert ext_isinstance([1, 2, 3], B)
    assert ext_isinstance([42, [1, 2, 3]], B)
    assert not ext_isinstance([42, ""], B)


def test_typing_type_alias_type_with_recursion() -> None:
    assert ext_isinstance([], C)
    assert ext_isinstance([[]], C)
    assert ext_isinstance([[], []], C)
    assert ext_isinstance([[[]]], C)
    assert not ext_isinstance([[42]], C)
