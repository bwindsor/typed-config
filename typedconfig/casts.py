from enum import Enum, EnumMeta
from typing import  Callable

def enum_cast(enum_type: EnumMeta)->Callable[[str], Enum]:
    def getter(name: str)->Enum:
        if name not in enum_type._member_names_:
            raise KeyError(f"{name} is not a member of {enum_type}")
        cast_value = enum_type._member_map_[name]
        return cast_value

    return getter