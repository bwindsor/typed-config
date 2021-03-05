import logging
from typing import List, Optional, Dict
from typedconfig.source import ConfigSource

logger = logging.getLogger(__name__)


class ConfigProvider:
    """
    Configuration provider keeping the cache and sources that can be shared
    across the configuration objects
    """
    def __init__(self, sources: List[ConfigSource] = None):
        self._cache: Dict[str, Dict[str, str]] = {}
        self._config_sources: List[ConfigSource] = []
        if sources is not None:
            for source in sources:
                self.add_source(source)

    def add_to_cache(self, section_name: str, key_name: str, value) -> None:
        if section_name not in self._cache:
            self._cache[section_name] = {}
        self._cache[section_name][key_name] = value

    def get_from_cache(self, section_name: str, key_name: str):
        if section_name not in self._cache:
            return None
        return self._cache[section_name].get(key_name, None)

    def clear_cache(self) -> None:
        self._cache.clear()

    @property
    def config_sources(self) -> List[ConfigSource]:
        return self._config_sources

    def get_key(self, section_name: str, key_name: str) -> Optional[str]:
        value = None

        # Go through the config sources until we find one which supplies the requested value
        for source in self._config_sources:
            logger.debug(f'Looking for config value {section_name}/{key_name} in {source}')
            value = source.get_config_value(section_name, key_name)
            if value is not None:
                logger.debug(f'Found config value {section_name}/{key_name} in {source}')
                break

        return value

    def add_source(self, source: ConfigSource):
        if not isinstance(source, ConfigSource):
            raise TypeError("Sources must be subclasses of ConfigSource")
        logger.debug(f'Adding config source of type {source.__class__.__name__} to {self.__class__.__name__}')
        self._config_sources.append(source)

    def set_sources(self, sources: List[ConfigSource]):
        self._config_sources.clear()
        for source in sources:
            self.add_source(source)

    def replace_source(self, old_source: ConfigSource, new_source: ConfigSource):
        if not isinstance(new_source, ConfigSource):
            raise TypeError("Sources must be subclasses of ConfigSource")
        logger.debug(f'Replacing config source of type {old_source.__class__.__name__} with {new_source.__class__.__name__}')
        for i, source in enumerate(self.config_sources):
            if source is old_source:
                self.config_sources[i] = new_source
                return

        raise ValueError("ConfigProvider did not find the supplied old source to replace: %s", old_source)
