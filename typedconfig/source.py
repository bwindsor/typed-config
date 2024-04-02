import os
import sys
import argparse
from abc import ABC, abstractmethod
from typing import Optional, Dict
from configparser import ConfigParser


class ConfigSource(ABC):
    @abstractmethod
    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        raise NotImplementedError()

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}>"


class EnvironmentConfigSource(ConfigSource):
    def __init__(self, prefix: str = ""):
        self.prefix = prefix

        self._prefix = prefix
        if len(self._prefix) > 0:
            self._prefix += "_"

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        return os.environ.get(f"{self._prefix.upper()}{section_name.upper()}_{key_name.upper()}", None)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}(prefix={repr(self.prefix)})>"


class AbstractIniConfigSource(ConfigSource):
    def __init__(self, config: ConfigParser):
        self._config = config

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        return self._config.get(section_name, key_name, fallback=None)


class IniStringConfigSource(AbstractIniConfigSource):
    def __init__(self, ini_string: str, source: str = "<string>"):
        config = ConfigParser()
        config.read_string(ini_string, source=source)
        super().__init__(config)


class IniFileConfigSource(AbstractIniConfigSource):
    def __init__(self, filename: str, encoding: Optional[str] = None, must_exist: bool = True):
        self.filename = filename
        config = ConfigParser()
        if os.path.exists(self.filename):
            config.read(self.filename, encoding=encoding)
        elif must_exist:
            raise FileNotFoundError(f"Could not find config file {self.filename}")
        super().__init__(config)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}(filename='{str(self.filename)}')>"


class DictConfigSource(ConfigSource):
    def __init__(self, config: Dict[str, Dict[str, str]]):
        # Quick checks on data format
        assert type(config) is dict
        for k, v in config.items():
            assert type(k) is str
            assert type(v) is dict
            for v_k, v_v in v.items():
                assert type(v_k) is str
                assert type(v_v) is str
        # Convert all keys to lowercase
        self._config = {k.lower(): {v_k.lower(): v_v for v_k, v_v in v.items()} for k, v in config.items()}

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        section = self._config.get(section_name.lower(), None)
        if section is None:
            return None
        return section.get(key_name.lower(), None)


class CmdConfigSource(ConfigSource):
    def __init__(self, prefix: str = ""):
        self._init_prefix = prefix

        self._prefix = prefix.lower()
        if len(self._prefix) > 0:
            self._prefix += "_"

    @property
    def prefix(self) -> str:
        return self._init_prefix

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        sys_argv_lower = [x.lower() for x in sys.argv]
        arg_name = f"{self._prefix}{section_name.lower()}_{key_name.lower()}"
        parser = argparse.ArgumentParser(allow_abbrev=False, exit_on_error=False)
        parser.add_argument("--" + arg_name, type=str)
        parsed_args, rest = parser.parse_known_args(sys_argv_lower)
        # Attribute should always exist, but will be None if the argument was not found
        return getattr(parsed_args, arg_name)

    def __repr__(self) -> str:
        return f"<{self.__class__.__qualname__}(prefix={repr(self.prefix)})>"
