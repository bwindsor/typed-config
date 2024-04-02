import pytest
from enum import Enum
from typing import Dict, Tuple, Any, Union
from typedconfig.casts import enum_cast, tuple_cast, boolean_cast, optional_boolean_cast
from contextlib import nullcontext


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


@pytest.mark.parametrize(
    "value,expected_output",
    [
        ("true", True),
        ("True", True),
        ("false", False),
        ("False", False),
        ("yes", True),
        ("Yes", True),
        ("no", False),
        ("No", False),
        ("on", True),
        ("On", True),
        ("off", False),
        ("Off", False),
        ("0", False),
        ("1", True),
        ("none", KeyError),
    ],
)
def test_boolean_cast(value: str, expected_output: Union[bool, Exception]):
    with nullcontext() if type(expected_output) is bool else pytest.raises(expected_output):
        result = boolean_cast(value)
        assert result == expected_output


@pytest.mark.parametrize(
    "value,expected_output",
    [
        ("true", True),
        ("True", True),
        ("false", False),
        ("False", False),
        ("yes", True),
        ("Yes", True),
        ("no", False),
        ("No", False),
        ("on", True),
        ("On", True),
        ("off", False),
        ("Off", False),
        ("0", False),
        ("1", True),
        ("None", None),
        ("none", None),
        ("Unknown", None),
        ("unknown", None),
        ("other", KeyError),
    ],
)
def test_optional_boolean_cast(value: str, expected_output: Union[bool, None, Exception]):
    with (
        nullcontext() if (type(expected_output) is bool or expected_output is None) else pytest.raises(expected_output)
    ):
        result = optional_boolean_cast(value)
        assert result == expected_output
