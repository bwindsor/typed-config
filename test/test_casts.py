import pytest

from enum import Enum
from typedconfig.casts import enum_cast


class ExampleEnum(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


def test_valid_enum_cast():
    getter = enum_cast(ExampleEnum)
    assert getter("BLUE") == ExampleEnum.BLUE


def test_invalid_enum_cast():
    getter = enum_cast(ExampleEnum)
    with pytest.raises(KeyError):
        getter("PURPLE")
