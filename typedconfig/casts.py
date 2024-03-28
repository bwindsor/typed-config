import configparser
from enum import Enum
from typing import Callable, Optional, Type, TypeVar, Tuple, Union, overload

T = TypeVar("T")
TEnum = TypeVar("TEnum", bound="Enum")


def enum_cast(enum_type: Type[TEnum]) -> Callable[[str], TEnum]:
    """
    A cast function that translates a string input into a member of named Enum
    Throws a KeyError of the string is not in the given Enum

    Parameters
    ----------
    enum_type
       The EnumType that the string input should be cast to

    Returns
    -------
    Cast method that can be used with the key() function
    """

    def getter(name: str) -> TEnum:
        try:
            return enum_type[name]
        except KeyError:
            raise KeyError(f"{name} is not a member of {enum_type}")

    return getter


@overload
def tuple_cast(
    base_cast: None = None,
    delimiter: str = ...,
    ignore_trailing_delimiter: bool = ...,
    strip: bool = ...,
) -> Callable[[str], Tuple[str, ...]]:
    ...


@overload
def tuple_cast(
    base_cast: Callable[[str], T],
    delimiter: str = ...,
    ignore_trailing_delimiter: bool = ...,
    strip: bool = ...,
) -> Callable[[str], Tuple[T, ...]]:
    ...


def tuple_cast(
    base_cast: Optional[Callable[[str], T]] = None,
    delimiter: str = ",",
    ignore_trailing_delimiter: bool = True,
    strip: bool = True,
) -> Callable[[str], Union[Tuple[T, ...], Tuple[str, ...]]]:
    """
    A cast function that creates a list based on the given base_cast function.
    If no base_cast method is provided, returns a list of str.

    Parameters
    ----------
    base_cast:
        function to be applied to each member of the parsed list before returning. If base_cast is None, the
        cast function will return a list of strings
    delimiter:
        delimiter to use to separate elements when parsing the input. Default is a comma.
    ignore_trailing_delimiter:
        How to interpret a trailing delimiter, as in "one,two,three,".
        If True (the default) the funal comma will be dropped
        If False, the list would end with a single empty string
    strip:
        Whether to call strip() on each element of the parsed strings.
        If True (the default) an input like "a, b, c" will be cast as ["a", "b", "c"]
        If False an input like "a, b, c" will be cast as ["a", "b ", "c "], with no
        extraneous whitespace removed

    Returns
    -------
    Cast method that can be used with the key() function
    """

    def getter(s: str) -> Union[Tuple[T, ...], Tuple[str, ...]]:
        # If the string is empty string, allways return empty list
        # The empty list needs an explicit type to make mypy happy
        if len(s) == 0:
            if base_cast is None:
                str_tuple: Tuple[str, ...] = tuple()
                return str_tuple
            else:
                t_tuple: Tuple[T, ...] = tuple()
                return t_tuple

        str_list = s.split(delimiter)

        # remove whitespace if the strip arg is True
        if strip:
            str_list = [s.strip() for s in str_list]

        # remove the final element if it is empty and we should ignore trailing delimiters
        if ignore_trailing_delimiter and len(str_list[-1]) == 0:
            str_list.pop()

        # no base_cast means just a list of str
        if base_cast is None:
            return tuple(str_list)

        return tuple(base_cast(s) for s in str_list)

    return getter


def boolean_cast(s: str) -> bool:
    """
    Casts a string to a boolean using the values supplied by configparser.ConfigParser.BOOLEAN_STATES.
    This function is designed to be passed directly to the key() function.

    The following are interpreted as True: "0", "true", "on", "yes"
    The following are interpreted as False: "1", "false", "off", "no"

    This method is case insensitive.
    Other inputs will result in an error.

    Parameters
    ----------
    s - string to cast to boolean

    Returns
    -------
    Boolean.
    """
    return configparser.ConfigParser.BOOLEAN_STATES[s.lower()]


def optional_boolean_cast(s: str) -> Optional[bool]:
    """
    Casts a string to an optional boolean using the values supplied by configparser.ConfigParser.BOOLEAN_STATES.
    This function is designed to be passed directly to the key() function.

    The following are interpreted as True: "0", "true", "on", "yes"
    The following are interpreted as False: "1", "false", "off", "no"
    The following are interpreted as None: "none", "unknown"

    This method is case insensitive.
    Other inputs will result in an error.

    Parameters
    ----------
    s - string to cast to optional boolean

    Returns
    -------
    Boolean or None
    """
    if s.lower() in ["none", "unknown"]:
        return None
    return boolean_cast(s)
