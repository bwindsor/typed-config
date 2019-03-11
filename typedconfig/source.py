import os
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from configparser import ConfigParser


class ConfigSource(ABC):
    @abstractmethod
    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        raise NotImplementedError()


class EnvironmentConfigSource(ConfigSource):
    def __init__(self, prefix: str=""):
        self.prefix = prefix

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        return os.environ.get(f"{self.prefix.upper()}_{section_name.upper()}_{key_name.upper()}", None)


class AbstractIniConfigSource(ConfigSource):
    def __init__(self, config: ConfigParser):
        self._config = config

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        return self._config.get(section_name, key_name, fallback=None)


class IniStringConfigSource(AbstractIniConfigSource):
    def __init__(self, ini_string, source='<string>'):
        config = ConfigParser()
        config.read_string(ini_string, source=source)
        super().__init__(config)


class IniFileConfigSource(AbstractIniConfigSource):
    def __init__(self, filename: str, encoding: str=None, must_exist=True):
        self.filename = filename
        config = ConfigParser()
        if os.path.exists(self.filename):
            config.read(self.filename, encoding=encoding)
        elif must_exist:
            raise FileNotFoundError(f"Could not find config file {self.filename}")
        super().__init__(config)


class DictConfigSource(ConfigSource):
    def __init__(self, config: Dict[str, Dict[str, str]]):
        self._config = config

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        section = self._config.get(section_name, None)
        if section is None:
            return None
        value = section.get(key_name, None)
        return value
