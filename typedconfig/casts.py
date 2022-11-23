from enum import Enum, EnumMeta
from typing import TypeVar, Callable, Type

TEnum = TypeVar('TEnum', bound="Enum")

def enum_cast(enum_type: Type[TEnum]) -> Callable[[str], Enum]:
    def getter(name: str)->Enum:
        try:
             return  enum_type[name]
        except KeyError:
            raise KeyError(f"{name} is not a member of {enum_type}")
    return getter