import pytest
import tempfile
import os
from unittest.mock import patch
from typedconfig.source import ConfigSource, IniFileConfigSource, IniStringConfigSource, DictConfigSource, EnvironmentConfigSource


def do_assertions(source: ConfigSource, expected_repr: str):
    v = source.get_config_value('s', 'A')
    assert '1' == v

    v = source.get_config_value('s', 'a')
    assert '1' == v

    v = source.get_config_value('s', 'B')
    assert '2' == v

    v = source.get_config_value('s', 'b')
    assert '2' == v

    v = source.get_config_value('t', 'A')
    assert v is None

    v = source.get_config_value('s', 'C')
    assert v is None

    assert repr(source) == expected_repr


def test_dict_config_source():
    source = DictConfigSource({
        's': dict(A='1', b='2')
    })
    do_assertions(source, "<DictConfigSource>")


@pytest.mark.parametrize("encoding", [
    "utf8",
    "windows-1252",
])
def test_ini_file_config_source(encoding):
    with tempfile.TemporaryDirectory() as td:
        file_name = os.path.join(td, 'config.cfg')
        with open(file_name, 'w', encoding=encoding) as f:
            f.write("""
[s]
a = 1
B = 2
""")

        source = IniFileConfigSource(file_name, encoding=encoding)
        do_assertions(source, f"<IniFileConfigSource(filename='{file_name}')>")


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
B = 2
    """)
    do_assertions(source, "<IniStringConfigSource>")


@patch.dict(os.environ, {'PREFIX_S_A': '1', 'PREFIX_S_B': '2'})
def test_environment_config_source_with_prefix():
    source = EnvironmentConfigSource("PREFIX")
    do_assertions(source, "<EnvironmentConfigSource(prefix='PREFIX')>")


@patch.dict(os.environ, {'S_A': '1', 'S_B': '2'})
def test_environment_config_source():
    source = EnvironmentConfigSource()
    do_assertions(source, "<EnvironmentConfigSource(prefix='')>")
