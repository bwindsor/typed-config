import inspect
import pytest
from unittest.mock import MagicMock
from typedconfig.config import Config, key, section, group_key, ConfigProvider
from typedconfig.source import DictConfigSource, ConfigSource


class GrandchildConfig(Config):
    prop1 = key('grandchild', 'PROP1')


class ChildConfig(Config):
    prop1 = key('child', 'PROP1')
    grandchild_config = group_key(GrandchildConfig)


class ParentConfig(Config):
    prop1 = key('parent', 'PROP1')
    child_config = group_key(ChildConfig)


def test_subclass_config():

    class SampleConfig(Config):
        prop1 = key('s', 'prop1', cast=float)
        prop2 = key('s', 'prop2', cast=int)
        prop3 = key('s', 'prop3', cast=str)
        prop4 = key('s', 'prop4')

    config_source = DictConfigSource({
        's': {
            'PROP1': '3.5',
            'PROP2': '2',
            'PROP3': 'hello',
            'PROP4': 'abc'
        }
    })
    config = SampleConfig()
    config.add_source(config_source)

    assert 3.5 == config.prop1
    assert 2 == config.prop2
    assert 'hello' == config.prop3
    assert 'abc' == config.prop4


def test_register_properties():
    class SampleConfig(Config):
        registerd_key1 = key('s', 'key1')
        registerd_key2 = key('s', 'key2')

        not_registered_key = 3

        def not_registered_method(self):
            pass

    config = SampleConfig()
    props = config.get_registered_properties()
    assert sorted(['registerd_key1', 'registerd_key2']) == sorted(props)


def test_register_composed_config():
    class ChildConfig1(Config):
        pass

    class ChildConfig2(Config):
        pass

    class SampleConfig(Config):
        composed_config1 = group_key(ChildConfig1)
        composed_config2 = group_key(ChildConfig2)

    config = SampleConfig()
    sub_configs = config.get_registered_composed_config()
    assert len(sub_configs) == 2
    assert isinstance(sub_configs[0], ChildConfig1)
    assert isinstance(sub_configs[1], ChildConfig2)

    # Check we're not creating a new instance of the sub configs each time we call
    sub_configs_2 = config.get_registered_composed_config()
    assert sub_configs[0] is sub_configs_2[0]
    assert sub_configs[1] is sub_configs_2[1]


@pytest.mark.parametrize("config_dict, expect_error", [
    ({}, True),
    ({'PROP1': 'x'}, False),
    ({'PROP1': 'x', 'PROP2': 'y'}, False)
], ids=["ConfigMissing", "PropertiesMatch", "ExtraConfig"])
def test_read(config_dict, expect_error):
    class SampleConfig(Config):
        prop1 = key('s', 'prop1')

    config = SampleConfig()
    config.add_source(DictConfigSource({'s': config_dict}))

    if expect_error:
        with pytest.raises(KeyError):
            config.read()
    else:
        config.read()

    if 'PROP1' in config_dict:
        assert config_dict['PROP1'] == config.prop1


@pytest.mark.parametrize("prop_val, args, expected_value_or_error", [
    ('a', dict(required=True), 'a'),
    (None, dict(required=False), None),
    (None, dict(required=False, default=3), 3),
    (None, dict(required=False, default=3, cast=str), '3'),
    (None, dict(required=True), KeyError),
    ('3', dict(), '3'),
    ('3', dict(cast=int), 3),
    ('a', dict(cast=int), ValueError),
])
def test_key_getter(prop_val, args, expected_value_or_error):
    class SampleConfig(Config):
        prop = key('s', 'prop1', **args)

    config = SampleConfig()
    if prop_val is None:
        source_dict = {}
    else:
        source_dict = {'s': {'PROP1': prop_val}}
    config.add_source(DictConfigSource(source_dict))

    if inspect.isclass(expected_value_or_error) and issubclass(expected_value_or_error, BaseException):
        with pytest.raises(expected_value_or_error):
            _ = config.prop
    else:
        v = config.prop
        assert expected_value_or_error == v


def test_get_key():
    class SampleConfig(Config):
        prop = key('s', 'prop1')

    config = SampleConfig()
    config.add_source(DictConfigSource({'s': {'PROP1': 'propval'}}))
    v = config.get_key('s', 'prop1')
    assert v == 'propval'


def test_caching():
    class SampleConfig(Config):
        prop1 = key('SampleConfig', 'PROP1')

    mock_source: ConfigSource = MagicMock(spec=ConfigSource)
    mock_source.get_config_value = MagicMock()
    s = SampleConfig()
    s.add_source(mock_source)

    mock_source.get_config_value.assert_not_called()
    a = s.prop1
    mock_source.get_config_value.assert_called_once_with('SampleConfig', 'PROP1')
    b = s.prop1
    mock_source.get_config_value.assert_called_once()
    s.clear_cache()
    c = s.prop1
    assert 2 == mock_source.get_config_value.call_count


def test_compose_configs():
    config = ParentConfig()
    config.add_source(DictConfigSource({
        'child': {'PROP1': '1'},
        'parent': {'PROP1': '2'},
    }))

    # Check that we are actually trying to read the grandchild which has a missing key
    with pytest.raises(KeyError):
        config.read()
    config.add_source(DictConfigSource({
        'grandchild': {'PROP1': '3'}
    }))
    config.read()
    assert '2' == config.prop1
    assert isinstance(config.child_config, ChildConfig)
    assert '1' == config.child_config.prop1
    assert isinstance(config.child_config.grandchild_config, GrandchildConfig)
    assert '3' == config.child_config.grandchild_config.prop1


def test_add_source():
    c = Config()
    with pytest.raises(TypeError):
        bad_type: ConfigSource = 3
        c.add_source(bad_type)

    assert len(c.config_sources) == 0
    new_source = DictConfigSource({})
    c.add_source(new_source)
    assert len(c.config_sources) == 1
    assert c.config_sources[-1] is new_source


def test_init_with_sources():
    c = Config(sources=[
        DictConfigSource({}),
        DictConfigSource({})
    ])
    assert 2 == len(c.config_sources)


def test_section_decorator():
    @section('my_section')
    class SampleConfig(Config):
        prop1 = key(key_name='prop1')

    c = SampleConfig()
    c.add_source(DictConfigSource({'my_section': dict(
        PROP1='abc'
    )}))
    assert 'abc' == c.prop1


def test_key_name_inference():
    class SampleConfig(Config):
        prop1 = key(section_name='s')
        prop2 = key(section_name='s')

    c = SampleConfig()

    c.add_source(DictConfigSource({'s': dict(
        PROP1='abc',
        PROP2='def',
    )}))
    assert 'abc' == c.prop1
    assert 'def' == c.prop2


def test_least_verbose_config():
    @section('X')
    class SampleConfig(Config):
        prop1 = key()
        prop2 = key(cast=int)

    c = SampleConfig()
    c.add_source(DictConfigSource({'X': dict(
        PROP1='abc',
        PROP2='44'
    )}))

    assert 'abc' == c.prop1
    assert 44 == c.prop2


def test_section_decorator_precedence():
    @section('decorator')
    class SampleConfig(Config):
        decorator_section = key(cast=str)
        key_specific_section = key(section_name='key_specific', cast=str)

    c = SampleConfig(sources=[DictConfigSource({
        'decorator': dict(decorator_section='a'),
        'key_specific': dict(key_specific_section='b')
    })])
    c.read()


def test_no_section_provided():
    class SampleConfig(Config):
        k = key(cast=str)

    c = SampleConfig()
    with pytest.raises(ValueError):
        c.read()


def test_multiple_group_keys_with_section_decorators():
    @section('a')
    class Child1(Config):
        k1 = key(cast=str)

    @section('b')
    class Child2(Config):
        k2 = key(cast=str)

    class ParentConfig(Config):
        c1 = group_key(Child1)
        c2 = group_key(Child2)

    c1 = Child1()
    c2 = Child2()

    assert c1._section_name == 'a'
    assert c2._section_name == 'b'

    p = ParentConfig()
    p.add_source(DictConfigSource({'a': {'k1': 'v1'}, 'b': {'k2': 'v2'}}))
    assert p.c1._section_name == 'a'
    assert p.c2._section_name == 'b'

    assert 'v1' == p.c1.k1
    assert 'v2' == p.c2.k2


def test_cast_with_default():

    @section('s')
    class SampleConfig(Config):
        nullable_key = key(cast=str, required=False, default=None)
        bool_key = key(cast=bool, required=False, default=False)

    s = SampleConfig()
    s.add_source(DictConfigSource({}))
    assert s.nullable_key is None
    assert s.bool_key is False


def test_provider_property_read():
    provider = ConfigProvider()
    config = ParentConfig(provider=provider)
    p = config.provider
    # Check same object is returned
    assert p is provider


def test_provider_property_is_readonly():
    config = ParentConfig()
    with pytest.raises(Exception):
        config.provider = ConfigProvider()


def test_construct_config_without_provider():
    sources = [DictConfigSource({})]
    config = ParentConfig(sources=sources)
    assert isinstance(config.provider, ConfigProvider)
    assert config.provider.config_sources == sources


def test_construct_config_bad_provider_type():
    with pytest.raises(TypeError):
        config = ParentConfig(provider=3)


def test_construct_config_with_provider():
    sources = [DictConfigSource({})]
    provider = ConfigProvider(sources)
    config = ParentConfig(sources=sources, provider=provider)
    assert config.provider is provider
    assert config.config_sources == sources


def test_replace_source():
    sources = [DictConfigSource({}), DictConfigSource({})]
    config = Config(sources=sources)

    assert config.config_sources == sources
    assert config.config_sources[0] is sources[0]
    assert config.config_sources[1] is sources[1]

    replacement_source = DictConfigSource({})
    config.replace_source(sources[0], replacement_source)

    assert config.config_sources == [replacement_source, sources[1]]
    assert config.config_sources[0] is replacement_source
    assert config.config_sources[1] is sources[1]


def test_replace_source_not_found():
    source_a = DictConfigSource({})
    source_b = DictConfigSource({})
    config = Config()
    config.add_source(source_a)
    with pytest.raises(ValueError):
        config.replace_source(source_b, source_a)


def test_replace_source_bad_type():
    source = DictConfigSource({})
    config = Config(sources=[source])
    with pytest.raises(TypeError):
        bad_type: ConfigSource = 3
        config.replace_source(source, bad_type)


def test_set_sources():
    old_sources = [DictConfigSource({})]
    new_sources = [DictConfigSource({}), DictConfigSource({})]
    config = Config(sources=old_sources)
    config.set_sources(new_sources)
    assert len(config.config_sources) == 2
    assert config.config_sources[0] is new_sources[0]
    assert config.config_sources[1] is new_sources[1]
