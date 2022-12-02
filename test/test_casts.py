import pytest
from enum import Enum
from typing import Dict, Tuple, Any
from typedconfig.casts import enum_cast, tuple_cast


class ExampleEnum(Enum):
    RED = 1
    GREEN = 2
    BLUE = 3


def test_valid_enum_cast() -> None:
    getter = enum_cast(ExampleEnum)
    assert getter("BLUE") == ExampleEnum.BLUE


def test_invalid_enum_cast() -> None:
    getter = enum_cast(ExampleEnum)
    with pytest.raises(KeyError):
        getter("PURPLE")


@pytest.mark.parametrize(
    "prop_val, args, expected_value",
    [
        ("a,b,c,d", dict(), ("a", "b", "c", "d")),
        ("1, 2,  3,  4 ", dict(base_cast=int), (1, 2, 3, 4)),
        ("a,b,c,d,", dict(), ("a", "b", "c", "d")),
        ("a,b,c,d,", dict(ignore_trailing_delimiter=False), ("a", "b", "c", "d", "")),
        ("a+b+c+d", dict(delimiter="+"), ("a", "b", "c", "d")),
        ("a//b//c//d//", dict(delimiter="//"), ("a", "b", "c", "d")),
        (
            "RED, BLUE, GREEN",
            dict(base_cast=enum_cast(ExampleEnum)),
            (ExampleEnum.RED, ExampleEnum.BLUE, ExampleEnum.GREEN),
        ),
        ("a, b, c, d,", dict(), ("a", "b", "c", "d")),
        ("a, b, c, d,", dict(strip=False), ("a", " b", " c", " d")),
        ("", dict(), tuple()),
        ("", dict(base_cast=int), tuple()),
        ("", dict(ignore_trailing_delimiter=False), tuple()),
    ],
)
def test_tuple_cast(prop_val: str, args: Dict[str, Any], expected_value: Tuple[Any]) -> None:
    getter = tuple_cast(**args)
    assert getter(prop_val) == expected_value
