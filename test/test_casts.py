import pytest

from enum import Enum
from typedconfig.casts import enum_cast


class ExampleEnum(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


def test_enum_cast():
    getter = enum_cast(ExampleEnum)

    assert getter("BLUE") == ExampleEnum.BLUE

    with pytest.raises(KeyError):
        getter("PURPLE")
