import pytest

from sugar._formatter import ceil_to_multiple

ceil_to_multiple_cases = [
    ([], 1, []),
    ([0], 2, [0]),
    ([1, 2, 3, 4, 5], 3, [3, 3, 3, 6, 6]),
    ([-3, 2, -5, 4, -1], 4, [0, 4, -4, 4, 0]),
    ([-1, -2, -3, -4, -5], 5, [0, 0, 0, 0, -5]),
]


@pytest.mark.parametrize("nums, mul, exp", ceil_to_multiple_cases)
def test_ceil_to_multiple(nums: list[int], mul: int, exp: list[int]) -> None:
    assert ceil_to_multiple(nums, mul) == exp
