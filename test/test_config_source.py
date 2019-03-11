import pytest
import tempfile
import os
from unittest.mock import patch
from typedconfig.source import ConfigSource, IniFileConfigSource, IniStringConfigSource, DictConfigSource, EnvironmentConfigSource


def do_assertions(source: ConfigSource):
    v = source.get_config_value('s', 'a')
    assert '1' == v

    v = source.get_config_value('t', 'a')
    assert v is None

    v = source.get_config_value('s', 'c')
    assert v is None


def test_dict_config_source():
    source = DictConfigSource({
        's': {
            'a': '1'
        }
    })
    do_assertions(source)


@pytest.mark.parametrize("encoding", [
    "utf8",
    "ansi",
    "windows-1252",
])
def test_ini_file_config_source(encoding):
    with tempfile.TemporaryDirectory() as td:
        file_name = os.path.join(td, 'config.cfg')
        with open(file_name, 'w', encoding=encoding) as f:
            f.write("""
[s]
a = 1
""")

        source = IniFileConfigSource(file_name, encoding=encoding)
        do_assertions(source)


def test_ini_file_config_source_no_file_existence_optional():
    source = IniFileConfigSource('config-this-file-definitely-does-not-exist.cfg', must_exist=False)
    v = source.get_config_value('s', 'a')
    assert v is None


def test_ini_file_config_source_no_file_must_exist():
    with pytest.raises(FileNotFoundError):
        IniFileConfigSource('config-this-file-definitely-does-not-exist.cfg', must_exist=True)


def test_ini_string_config_source():
    source = IniStringConfigSource("""
[s]
a = 1
    """)
    do_assertions(source)


@patch.dict(os.environ, {'THERMOBOT_TEST_S_A': '1'})
def test_environment_config_source():
    source = EnvironmentConfigSource("THERMOBOT_TEST")
    do_assertions(source)
