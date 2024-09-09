import pytest

from sugar._action import Choice, KeywordToken, Map, PositionalToken
from sugar._eval import int_
from sugar.exception import SugarError


def test_Choice() -> None:
    choices = {1, 2}
    action = Choice(choices, int_)

    pos_0 = PositionalToken("pos_0", "0")
    pos_1 = PositionalToken("pos_1", "1")
    pos_2 = PositionalToken("pos_2", "2")

    pytest.raises(SugarError, action.call_positional, pos_0)
    assert action.call_positional(pos_1) == 1
    assert action.call_positional(pos_2) == 2

    kw_0 = KeywordToken("kw_0", ["0"], 1)
    kw_1 = KeywordToken("kw_1", ["1"], 1)
    kw_2 = KeywordToken("kw_2", ["2"], 1)

    pytest.raises(SugarError, action.call_keyword, kw_0)
    assert action.call_keyword(kw_1) == 1
    assert action.call_keyword(kw_2) == 2


def test_Map() -> None:
    mapping = {1: "one", 2: "two"}
    action = Map(mapping, int_)
    print(action)

    pos_0 = PositionalToken("pos_0", "0")
    pos_1 = PositionalToken("pos_1", "1")
    pos_2 = PositionalToken("pos_2", "2")

    pytest.raises(SugarError, action.call_positional, pos_0)
    assert action.call_positional(pos_1) == "one"
    assert action.call_positional(pos_2) == "two"

    kw_0 = KeywordToken("kw_0", ["0"], 1)
    kw_1 = KeywordToken("kw_1", ["1"], 1)
    kw_2 = KeywordToken("kw_2", ["2"], 1)

    pytest.raises(SugarError, action.call_keyword, kw_0)
    assert action.call_keyword(kw_1) == "one"
    assert action.call_keyword(kw_2) == "two"
