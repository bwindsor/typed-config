from enum import Enum
from typing import TypeVar, Callable, Type

TEnum = TypeVar("TEnum", bound="Enum")


def enum_cast(enum_type: Type[TEnum]) -> Callable[[str], TEnum]:
    def getter(name: str) -> TEnum:
        try:
            return enum_type[name]
        except KeyError:
            raise KeyError(f"{name} is not a member of {enum_type}")

    return getter
