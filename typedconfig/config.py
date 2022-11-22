import sys
import typing
from itertools import chain
from typing import TypeVar, List, Optional, Callable, Type, Union, Tuple, Any, overload, Dict

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    # Python <= 3.7
    from typing_extensions import Literal
from typedconfig.provider import ConfigProvider
from typedconfig.source import ConfigSource
import logging
import inspect

logger = logging.getLogger(__name__)

TConfig = TypeVar("TConfig", bound="Config")
T = TypeVar("T")
U = TypeVar("U")
V = TypeVar("V")

"""
required | cast | default | return_type
True  | None/missing    | -       | str
True  | NotNone | -       | T

False | NotNone | None/missing | Optional[T]
False | NotNone | NotNone | T
False | None    | -       | Union[str, Optional[T]]
"""


@overload
def key(
    *,
    section_name: Optional[str] = ...,
    key_name: Optional[str] = ...,
    required: Literal[False],
    cast: Callable[[str], T],
    default: T,
) -> T:
    ...


@overload
def key(
    *,
    section_name: Optional[str] = ...,
    key_name: Optional[str] = ...,
    required: Literal[False],
    cast: Callable[[str], T],
    default: None = ...,
) -> Optional[T]:
    ...


@overload
def key(
    *,
    section_name: Optional[str] = ...,
    key_name: Optional[str] = ...,
    required: Literal[False],
    cast: None = ...,
    default: Optional[T] = ...,
) -> Union[str, Optional[T]]:
    ...


@overload
def key(
    *,
    section_name: Optional[str] = ...,
    key_name: Optional[str] = ...,
    required: Literal[True] = ...,
    cast: Callable[[str], T],
    default: Optional[T] = ...,
) -> T:
    ...


@overload
def key(
    *,
    section_name: Optional[str] = ...,
    key_name: Optional[str] = ...,
    required: Literal[True] = ...,
    cast: None = ...,
    default: Optional[T] = ...,
) -> str:
    ...


def key(
    *,
    section_name: Optional[str] = None,
    key_name: Optional[str] = None,
    required: bool = True,
    cast: Optional[Callable[[str], T]] = None,
    default: Optional[T] = None,
) -> Union[Optional[T], str]:
    """
    Provides a getter for a configuration key
    Parameters
    ----------
    section_name: section name where the key resides. If not specified,
        the @section decorator should be used on the Config class to specify it
    key_name: key name within the specified section. If not specified,
        the python key name will be capitalised and used
    required: optional, default True. Whether the key is required or optional
    cast: optional, default None (no cast). Function taking a string argument and returning the parsed value
    default: optional, default None. If required is set to False, the value to use if the config value is not found
    """

    # In general, this should not store any state since the class property is shared across instances. However, the
    # property name will be the same across all instances, so when this is looked up the first time it is ok to store
    # it.
    _mutable_state = {"key_name": key_name.upper() if key_name is not None else None}

    def getter_method(self: Config) -> Union[Optional[T], str]:
        """
        Returns
        -------
        value: the parsed config value
        """

        resolved_section_name = self._resolve_section_name(section_name)

        resolved_key_name = _mutable_state["key_name"]
        if resolved_key_name is None:
            resolved_key_name = self._resolve_key_name(getter)
            _mutable_state["key_name"] = resolved_key_name

        # If value is cached, just use the cached value
        cached_value: Union[T, str] = self._provider.get_from_cache(resolved_section_name, resolved_key_name)
        if cached_value is not None:
            return cached_value

        string_value = self._provider.get_key(resolved_section_name, resolved_key_name)
        cast_value: Union[Optional[T], str] = None

        # If we still haven't found a config value and this parameter is required,
        # raise an exception, otherwise use the default
        if string_value is None:
            if required:
                raise KeyError("Config parameter {0}.{1} not found".format(resolved_section_name, resolved_key_name))
            else:
                if default is not None:
                    cast_value = default
        else:
            # If a casting function has been specified then cast to the required data type
            if cast is not None:
                cast_value = cast(string_value)
            else:
                cast_value = string_value

        # Cache this for next time if still not none
        if cast_value is not None:
            self._provider.add_to_cache(resolved_section_name, resolved_key_name, cast_value)

        return cast_value

    getter = property(getter_method)
    setattr(getter.fget, Config._config_key_registration_string, True)
    setattr(getter.fget, Config._config_key_key_name_string, key_name.upper() if key_name is not None else None)
    setattr(getter.fget, Config._config_key_section_name_string, section_name)
    return typing.cast(Union[Optional[T], str], getter)


def group_key(cls: Type[TConfig], *, group_section_name: Optional[str] = None, hierarchical: bool = False) -> TConfig:
    """
    Creates a key containing a composed config (or child config) of the configuration. The first time the
    child config is required, it is created and stored in an attribute. This attribute is then used from that
    point onwards.
    Parameters
    ----------
    f - getter function returning a new instance of the child config (usually just the constructor).

    Returns
    -------
    Decorated composed config getter function
    """

    def wrapped_f_getter(self: Config) -> TConfig:
        attr_name = "_" + self._get_property_name_from_object(wrapped_f)
        if not hasattr(self, attr_name):
            setattr(self, attr_name, cls(provider=self._provider))
        return typing.cast(TConfig, getattr(self, attr_name))

    wrapped_f = property(wrapped_f_getter)
    setattr(wrapped_f.fget, Config._composed_config_registration_string, True)

    return typing.cast(TConfig, wrapped_f)


def section(section_name: str) -> Callable[[Type[TConfig]], Type[TConfig]]:
    def _section(cls: Type[TConfig]) -> Type[TConfig]:
        class SectionConfig(cls):  # type: ignore
            def __init__(self, *args, **kwargs):  # type: ignore
                super().__init__(*args, section_name=section_name, **kwargs)

        SectionConfig.__name__ = cls.__name__
        SectionConfig.__qualname__ = cls.__qualname__

        return SectionConfig

    return _section


class Config:
    """
    Base class for all configuration objects
    """

    _composed_config_registration_string = "__composed_config__"
    _config_key_registration_string = "__config_key__"
    _config_key_key_name_string = "__config_key_key_name__"
    _config_key_section_name_string = "__config_key_section_name__"

    def __init__(
        self,
        section_name: Optional[str] = None,
        sources: Optional[List[ConfigSource]] = None,
        provider: Optional[ConfigProvider] = None,
    ):
        if provider is None:
            provider = ConfigProvider(sources=sources)
        elif not isinstance(provider, ConfigProvider):
            raise TypeError("provider must be a ConfigProvider object")
        self._section_name = section_name
        self._provider: ConfigProvider = provider

    def __repr__(self) -> str:
        key_names = self.get_registered_properties()
        group_key_info = inspect.getmembers(
            self.__class__,
            predicate=lambda x: self.is_member_registered(x, Config._composed_config_registration_string),
        )

        joined_repr = ", ".join(
            chain(
                (f"{k}={getattr(self, k)!r}" for k in key_names),
                (f"{k}={getattr(self, k)!r}" for k, _ in group_key_info),
            )
        )

        return f"{self.__class__.__name__}({joined_repr})"

    @property
    def config_sources(self) -> List[ConfigSource]:
        return self._provider.config_sources

    @property
    def provider(self) -> ConfigProvider:
        return self._provider

    def get_registered_properties(self) -> List[str]:
        """
        Gets a list of all properties which have been defined using the key function
        Returns
        -------
        A list of strings giving the names of the registered properties/methods
        """
        all_properties = self._get_registered_properties_with_values()
        return [f[0] for f in all_properties]

    def _get_registered_properties_with_values(self) -> List[Tuple[str, Any]]:
        return inspect.getmembers(
            self.__class__, predicate=lambda x: self.is_member_registered(x, Config._config_key_registration_string)
        )

    def _resolve_section_name(self, key_section_name: Optional[str]) -> str:
        if key_section_name is not None:
            return key_section_name

        if self._section_name is None:
            raise ValueError("Section name was not specified by the key function or the section class decorator.")
        return self._section_name

    def _resolve_key_name(self, property_object: property) -> str:
        key_key_name: str = getattr(property_object.fget, self._config_key_key_name_string)
        if key_key_name is not None:
            return key_key_name

        return self._get_property_name_from_object(property_object)

    def _get_property_name_from_object(self, property_object: property) -> str:
        members = inspect.getmembers(self.__class__, lambda x: x is property_object)
        assert len(members) == 1
        return members[0][0].upper()

    @staticmethod
    def is_member_registered(member: Any, reg_string: str) -> bool:
        if isinstance(member, property):
            return typing.cast(bool, getattr(member.fget, reg_string, False))
        else:
            return False

    def get_registered_composed_config(self) -> List["Config"]:
        """
        Gets a list of all composed configs or "sub configs",
        that is configs which are registered with the group_key function.
        This returns the sub-config instances themselves (not just references to the getter methods)
        Returns
        -------
        A list of Config subclasses which have been registered
        """

        all_properties = inspect.getmembers(
            self.__class__,
            predicate=lambda x: self.is_member_registered(x, Config._composed_config_registration_string),
        )
        return [getattr(self, f[0]) if isinstance(f[1], property) else f[1](self) for f in all_properties]

    def read(self) -> None:
        """
        Loops through all config properties generated with the key function and reads their values in.
        It is useful to call this after adding the config sources for fail-fast behaviour, since an error will occur at
        this point if any required config value is missing. It also means all config values are loaded into cache at
        this point so future accesses will be reliable and fast.
        Returns
        -------
        None
        """
        child_configs = self.get_registered_composed_config()
        registered_properties = self.get_registered_properties()
        for f in registered_properties:
            getattr(self, f)

        self._post_read(self.post_read_hook())

        for c in child_configs:
            c.read()

    def post_read_hook(self) -> Dict[str, Any]:
        """
        This method can be overridden to modify config values after read() is called.
        Returns
        -------
        A dict of key-value pairs containing new configuration values for key() items in this Config class
        """
        return dict()

    def _post_read(self, updated_values: Dict[str, Any]) -> None:
        registered_properties = set(self.get_registered_properties())

        for k, v in updated_values.items():
            if isinstance(v, dict):
                group_property_object: property = getattr(self.__class__, k)
                if not self.is_member_registered(group_property_object, self._composed_config_registration_string):
                    raise KeyError(f"{k} is not a valid typed config group_key() of {self.__class__.__name__}")
                child_config = getattr(self, k)
                child_config._post_read(v)
            else:
                if k not in registered_properties:
                    raise KeyError(f"{k} is not a valid attribute of {self.__class__.__name__}")

                key_property_object: property = getattr(self.__class__, k)

                section_name = self._resolve_section_name(
                    getattr(key_property_object.fget, self._config_key_section_name_string)
                )
                key_name = self._resolve_key_name(key_property_object)
                self._provider.add_to_cache(section_name, key_name, v)

    def clear_cache(self) -> None:
        """
        Config values are cached the first time they are requested. This means that if, for example, config values are
        coming from a database or API, the call does not need to be made again. This function clears the cache.
        Returns
        -------
        None
        """
        self._provider.clear_cache()

    def add_source(self, source: ConfigSource) -> None:
        """
        Adds a configuration source
        Parameters
        ----------
        source: a subclass of ConfigSource which can provide string values for configuration parameters

        Returns
        -------
        None
        """
        self._provider.add_source(source)

    def replace_source(self, old_source: ConfigSource, new_source: ConfigSource) -> None:
        """
        Replaces a ConfigSource with a new one. This is useful for example if you modify a config file, so want
        to swap a ConfigSource which reads from a file on initialisation for a new one.
        This does not clear the cache. To access new values you also need to call clear_cache.

        Parameters
        ----------
        old_source: The old config source to be replaced
        new_source: The config source to replace it with

        Returns
        -------
        None
        """
        self._provider.replace_source(old_source, new_source)

    def set_sources(self, sources: List[ConfigSource]) -> None:
        """
        Completely replaces the set of ConfigSources with a new set.

        This does not clear the cache. To access new values you also need to call clear_cache
        Parameters
        ----------
        sources: List of ConfigSource subclasses to supply the configuration

        Returns
        -------
        None
        """
        self._provider.set_sources(sources)

    def get_key(self, section_name: str, key_name: str) -> Optional[str]:
        """
        Gets a string configuration key from available sources
        Parameters
        ----------
        section_name: section name where the key resides
        key_name: key name within the specified section

        Returns
        -------
        value: the loaded config value as a string
        """
        return self._provider.get_key(section_name, key_name)
