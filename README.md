[![Build Status](https://travis-ci.org/bwindsor/typed-config.svg?branch=master)](https://travis-ci.org/bwindsor/typed-config)
[![codecov](https://codecov.io/gh/bwindsor/typed-config/branch/master/graph/badge.svg)](https://codecov.io/gh/bwindsor/typed-config)

# typed-config
Typed, extensible, dependency free configuration reader for Python projects for multiple config sources and working well in IDEs for great autocomplete performance.

`pip install typed-config`

Requires python 3.6 or above.

## Basic usage
```python
# my_app/config.py
from typedconfig import Config, key, section
from typedconfig.source import EnvironmentConfigSource

@section('database')
class AppConfig(Config):
    host = key(cast=str)
    port = key(cast=int)
    timeout = key(cast=float)
    
config = AppConfig()
config.add_source(EnvironmentConfigSource())
config.read()
```

```python
# my_app/main.py
from my_app.config import config
print(config.host)
```
In PyCharm, and hopefully other IDEs, it will recognise the datatypes of your configuration and allow you to autocomplete. No more remembering strings to get the right thing out!

## How it works
Configuration is always supplied in a two level structure, so your source configuration can have multiple sections, and each section contains multiple key/value configuration pairs. For example:
```ini
[database]
host = 127.0.0.1
port = 2000

[algorithm]
max_value = 10
min_value = 20
```

You then create your configuration hierarchy in code (this can be flat or many levels deep) and supply the matching between strings in your config sources and properties of your configuration classes.

You provide one or more `ConfigSource`s, from which the config for your application can be read. For example, you might supply an `EnvironmentConfigSource`,  and two `IniFileConfigSource`s. This would make your application first look for a configuration value in environment variables, if not found there it would then look at the first INI file (perhaps a user-specific file), before falling back to the second INI file (perhaps a default configuration shared between all users). If a parameter is still not found and is a required parameter, an error would be thrown.

There is emphasis on type information being available for everything so that an IDE will autocomplete when trying to use your config across your application.

### Multiple data sources
```python
from typedconfig import Config, key, section, group_key
from typedconfig.source import EnvironmentConfigSource, IniFileConfigSource

@section('database')
class DatabaseConfig(Config):
    host = key(cast=str)
    port = key(cast=int)
    username = key(cast=str)
    password = key(cast=str)

config = DatabaseConfig()
config.add_source(EnvironmentConfigSource(prefix="EXAMPLE"))
config.add_source(IniFileConfigSource("config.cfg"))

# OR provide sources directly to the constructor
config = DatabaseConfig(sources=[
    EnvironmentConfigSource(prefix="EXAMPLE"),
    IniFileConfigSource("config.cfg")
])
```

Since you don't want to hard code your secret credentials, you might supply them through the environment.
So for the above configuration, the environment might look like this:
```bash
export EXAMPLE_DATABASE_USERNAME=my_username
export EXAMPLE_DATABASE_PASSWORD=my_very_secret_password
export EXAMPLE_DATABASE_PORT=2001
```

Those values which couldn't be found in the environment would then be read from the INI file, which might look like this:
```ini
[database]
HOST = db1.mydomain.com
PORT = 2000
```

Note after this, `config.port` will be equal to `2001` as the value in the environment took priority over the value in the INI file.

### Caching
When config values are first used, they are read. This is lazy evaluation by default so that not everything is read if not necessary.

After first use, they are cached in memory so that there should be no further I/O if the config value is used again.

For fail fast behaviour, and also to stop unexpected latency when a config value is read partway through your application (e.g. your config could be coming across a network), the option is available to read all config values at the start. Just call

`config.read()`

This will throw an exception if any required config value cannot be found, and will also keep all read config values in memory for next time they are used. If you do not use `read` you will only get the exception when you first try to use the offending config key.

### Hierarchical configuration
Use `group_key` to represent a "sub-config" of a configuration. Set up "sub-configs" exactly as demonstrated above, and then create a parent config to compose them in one place.
```python
from typedconfig import Config, key, section, group_key
from typedconfig.source import EnvironmentConfigSource, IniFileConfigSource

@section('database')
class DatabaseConfig(Config):
    host = key(cast=str)
    port = key(cast=int)

@section('algorithm')
class AlgorithmConfig(Config):
    max_value = key(cast=float)
    min_value = key(cast=float)

class ParentConfig(Config):
    database = group_key(DatabaseConfig)
    algorithm = group_key(AlgorithmConfig)
    description = key(cast=str, section_name="general")

config = ParentConfig()
config.add_source(EnvironmentConfigSource(prefix="EXAMPLE"))
config.add_source(IniFileConfigSource("config.cfg"))
config.read()
```

The first time the `config.database` or `config.algorithm` is accessed (which in the case above is when `read()` is called), then an instance will be instantiated. Notice that it is the class definition, not an instance of the class, which is passed to the `group_key` function.

### Custom section/key names, optional parameters, default values
Let's take a look at this:
```python
from typedconfig import Config, key, section

@section('database')
class AppConfig(Config):
    host1 = key()
    host2 = key(section_name='database', key_name='HOST2',
                required=True, cast=str, default=None)
```
Both `host1` and `host2` are legitimate configuration key definitions.

* `section_name` - this name of the section in the configuration source from which this parameter should be read. This can be provided on a key-by-key basis, but if it is left out then the section name supplied by the `@section` decorator is used. If all keys supply a `section_name`, the class decorator is not needed. If both `section_name` and a decorator are provided, the `section_name` argument takes priority.
* `key_name` - the name of this key in the configuration source from which this parameter is read. If not supplied, some magic uses the object property name as the key name.
* `required` - default True. If False, and the configuration value can't be found, no error will be thrown and the default value will be used, if provided. If a default not provided, `None` will be used.
* `cast` - probably the most important option for typing. **If you want autocomplete typing support you must specify this**. It's just a function which takes a string as an input and returns a parsed value. See the casting section for more. If not supplied, the value remains as a string.
* `default` - only applicable if `required` is false. When `required` is false this value is used if a value cannot be found.

### Types
```python
from typedconfig import Config, key, section
from typing import List

def split_str(s: str) -> List[str]:
    return [x.strip() for x in s.split(",")]

@section('database')
class AppConfig(Config):
    host = key()
    port = key(cast=int)
    users = key(cast=split_str)
    zero_based_index = key(cast=lambda x: int(x)-1)
config = AppConfig(sources=[...])
```
In this example we have three ways of casting:
1. Not casting at all. This default to returning a `str`, but your IDE won't know that so if you want type hints use `cast=str`
2. Casting to an built in type which can take a string input and parse it, for example `int`
3. Defining a custom function. Your function should take one string input and return one output of any type. To get type hint, just make sure your function has type annotations.
4. Using a lambda expression. The type inference may or may not work depending on your expression, so if it doesn't just write it as a function with type annotations.

### Validation
You can validate what has been supplied by providing a custom `cast` function to a `key`, which validates the configuration value in addition to parsing it.

### Extending configuration using shared ConfigProvider

Multiple application modules may use different configuration schemes while sharing the same configuration source. Analogously, various `Config` classes may provide different view of the same configuration data, sharing the same `ConfigProvider`.

```python
# app/config.py
from typedconfig.provider import ConfigProvider
from typedconfig.source import EnvironmentConfigSource, IniFileConfigSource

provider = ConfigProvider()
provider.add_source(EnvironmentConfigSource(prefix="EXAMPLE"))
provider.add_source(IniFileConfigSource("config.cfg"))

__all__ = ["provider"]
```
```python
# app/database/config.py
from typedconfig import Config, key, section
from app.config import provider

@section('database')
class DatabaseConfig(Config):
    host = key(cast=str)
    port = key(cast=int)

database_config = DatabaseConfig(provider=provider)
```
```python
# app/algorithm/config.py
from typedconfig import Config, key, section
from app.config import provider

@section('algorithm')
class AlgorithmConfig(Config):
    max_value = key(cast=float)
    min_value = key(cast=float)

algorithm_config = AlgorithmConfig(provider=provider)
```

Shared configuration provider can be used by plugins, which may need to declare additional configuration sections within the same configuration files as the main application.  Let's assume we have `[database]` section used by main application and `[app_extension]` that provides 3rd party plugin configuration:

```ini
[database]
host = 127.0.0.1
port = 2000

[app_extension]
api_key = secret
```

e.g. `app/config.py` may look like that:

```python
from typedconfig import Config, key, section, group_key
from typedconfig.source import EnvironmentConfigSource, IniFileConfigSource

@section('database')
class DatabaseConfig(Config):
    """Database configuration"""
    host = key(cast=str)
    port = key(cast=int)

class ApplicationConfig(Config):
    """Main configuration object"""
    database = group_key(DatabaseConfig)

app_config = ApplicationConfig(sources=[
    EnvironmentConfigSource(),
    IniFileConfigSource("config.cfg")
])
```

and plugin can read additional sections by using the same configuration provider as main application config.

e.g. `plugin/config.py`:
```python
from typedconfig import Config, key, section, group_key

from app.config import ApplicationConfig, app_config

@section('app_extension')
class ExtensionConfig(Config):
    """Extension configuration"""
    api_key = key(cast=str)

# ExtendedAppConfig extends ApplicationConfig 
# so original sections are also included
class ExtendedAppConfig(ApplicationConfig):
    """Extended main configuration object"""
    app_extension = group_key(ExtensionConfig)
    
# ExtendedAppConfig uses the same provider as the main app_config
extended_config = ExtendedAppConfig(provider=app_config.provider)
```
```python
from plugin.config import extended_config

# Plugin can access both main and extra sections
print(extended_config.app_extension.api_key)
print(extended_config.database.host)
```

### Configuration variables which depend on other configuration variables
Sometimes you may wish to set the value of some configuration variables based on others. You may also wish to validate some variables, for example allowed values may be different depending on the value of another config variable. For this you can add a `post_read_hook`.

The default implementation of `post_read_hook` returns an empty `dict`. You can override this by implementing your own `post_read_hook` method. It should receive only `self` as an input, and return a `dict`. This `dict` should be a simple mapping from config keys to values. For hierarchical configurations, you can nest the dictionaries. If you provide a `post_read_hook` in both a parent and a child class which both make changes to the same keys (don't do this) then the values returned by the child method will overwrite those by the parent.

This hook is called whenever you call the `read` method. If you use lazy loading and skip calling the `read` method, you cannot use this hook.
```python
# my_app/config.py
from typedconfig import Config, key, group_key, section
from typedconfig.source import EnvironmentConfigSource

@section('child')
class ChildConfig(Config):
    http_port_plus_one = key(cast=int, required=False)

@section('app')
class AppConfig(Config):
    use_https = key(cast=bool)
    http_port = key(key_name='port', cast=int, required=False)
    child = group_key(ChildConfig)
    
    def post_read_hook(self) -> dict:
        config_updates = dict()
        # If the port has not been provided, set it based on the value of use_https
        if self.http_port is None:
            config_updates.update(http_port=443 if self.use_https else 80)
        else:
            # Modify child config
            config_updates.update(child=dict(http_port_plus_one=self.http_port + 1))
            
        # Validate that the port number has a sensible value
        # It is recommended to do validation inside the cast method for individual keys, however for dependent keys it can be useful here
        if self.http_port is not None:
            if self.use_https:
                assert self.http_port in [443, 444, 445]
            else:
                assert self.http_port in [80, 81, 82]

        return config_updates
            
config = AppConfig()
config.add_source(EnvironmentConfigSource())
config.read()
```

## Configuration Sources
Configuration sources are how your main `Config` class knows where to get its data from. These are totally extensible so that you can read in your configuration from wherever you like - from a database, from S3, anywhere that you can write code for.

You supply your configuration source to your config after you've instantiated it, but **before** you try to read any data from it:
```python
config = AppConfig()
config.add_source(my_first_source)
config.add_source(my_second_source)
config.read()
```
Or you can supply the sources directly in the constructor like this:
```python
config = AppConfig(sources=[my_first_source, my_second_source])
config.read()
```


### Modifying or refreshing configuration after it has been loaded
In general it is bad practice to modify configuration at runtime because the configuration for your program should be fixed for the duration of it.  However, there are cases where it may be necessary.

To completely replace the set of config sources, you can use
```python
config = AppConfig(sources=[my_first_source, my_second_source])
config.set_sources([my_first_new_source, my_second_new_source])
```

To replace a specific config source, for example because a config file has changed and you need to re-read it from disk, you can use `replace_source`:
```python
from typedconfig.source import IniFileConfigSource
original_source = IniFileConfigSource("config.cfg")
config = AppConfig(sources=[source])
# Now say you change the contents to config.cfg and need to read it again
new_source = IniFileConfigSource("config.cfg")  # re-reads file during construction
config.replace_source(original_source, new_source)
```

**Important**: if you add or modify the config sources the config has been read, or need to refresh the config for some reason, you'll need to clear any cached values in order to force the config to be fetched from the `ConfigSource`s again. You can do this by
```python
config.clear_cache()
config.read()          # Read all configuration values again
```



### Supplied Config Sources
#### `EnvironmentConfigSource`
This just reads configuration from environment variables.
```python
from typedconfig.source import EnvironmentConfigSource
source = EnvironmentConfigSource(prefix="XYZ")
# OR just
source = EnvironmentConfigSource()
```
It just takes one optional input argument, a prefix. This can be useful to avoid name clashes in environment variables.

* If prefix is provided, environment variables are expected to look like `{PREFIX}_{SECTION}_{KEY}`, for example `export XYZ_DATABASE_PORT=2000`. 
* If no prefix is provided, environment variables should look like `{SECTION}_{KEY}`, for example `export DATABASE_PORT=2000`.

#### `IniFileConfigSource`
This reads from an INI file using Python's built in [configparser](https://docs.python.org/3/library/configparser.html). Read the docs for `configparser` for more about the structure of the file.
```python
from typedconfig.source import IniFileConfigSource
source = IniFileConfigSource("config.cfg", encoding='utf-8', must_exist=True)
```

* The first argument is the filename (absolute or relative to the current working directory).
* `encoding` is the text encoding of the file. `configparser`'s default is used if not supplied.
* `must_exist` - default `True`. If the file can't be found, an error will be thrown by default. Setting `must_exist` to be `False` allows the file not to be present, in which case this source will just report that it can't find any configuration values and your `Config` class will move onto looking in the next `ConfigSource`.

#### `IniStringConfigSource`
This reads from a string instead of a file
```python
from typedconfig.source import IniStringConfigSource
source = IniStringConfigSource("""
[section_name]
key_name=key_value
""")
```

#### `DictConfigSource`
The most basic source, entirely in memory, and also useful when writing tests. It is case insensitive.
```python
from typedconfig.source import DictConfigSource
source = DictConfigSource({
    'database': dict(HOST='db1', PORT='2000'),
    'algorithm': dict(MAX_VALUE='20', MIN_VALUE='10')
})
```

It expects data type `Dict[str, Dict[str, str]]`, i.e. such that `string_value = d['section_name']['key_name']`. Everything should be provided as string data so that it can be parsed in the same way as if data was coming from a file or elsewhere.

This is an alternative way of supplying default values instead of using the `default` option when defining your `key`s. Just provide a `DictConfigSource` as the lowest priority source, containing your defaults.

### Writing your own `ConfigSource`s
An abstract base class `ConfigSource` is supplied. You should extend it and implement the method `get_config_value` as demonstrated below, which takes a section name and key name, and returns either a `str` config value, or `None` if the value could not be found. It should not error if the value cannot be found, `Config` will throw an error later if it still can't find the value in any of its other available sources. To make it easier for the user try to make your source case insensitive.

Here's an outline of how you might implement a source to read your config from a JSON file, for example. Use the `__init__` method to provide any information your source needs to fetch the data, such as filename, api details, etc. You can do sanity checks in the `__init__` method and throw an error if something is wrong.
```python
import json
from typing import Optional
from typedconfig.source import ConfigSource

class JsonConfigSource(ConfigSource):
    def __init__(self, filename: str):
        # Read data - will raise an exception if problem with file
        with open(filename, 'r') as f:
            self.data = json.load(f)
        # Quick checks on data format
        assert type(self.data) is dict
        for k, v in self.data.items():
            assert type(k) is str
            assert type(v) is dict
            for v_k, v_v in v.items():
                assert type(v_k) is str
                assert type(v_v) is str
        # Convert all keys to lowercase
        self.data = {
            k.lower(): {
                v_k.lower(): v_v
                for v_k, v_v in v.items()
            }
            for k, v in self.data.items()
        }    

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        # Extract info from data which we read in during __init__
        section = self.data.get(section_name.lower(), None)
        if section is None:
            return None
        return section.get(key_name.lower(), None)
```

### Additional config sources
In order to keep `typed-config` dependency free, `ConfigSources` requiring additional dependencies are in separate packages, which also have `typed-config` as a dependency.

These are listed here:

| pip install name | import name | Description |
| --- | --- | --- |
| [typed-config-aws-sources](https://pypi.org/project/typed-config-aws-sources) | `typedconfig_awssource` | Config sources using `boto3` to get config e.g. from S3 or DynamoDB

## Contributing
Ideas for new features and pull requests are welcome. PRs must come with tests included. This was developed using Python 3.7 but Travis tests run with v3.6 too.

### Development setup
1. Clone the git repository
2. Create a virtual environment `virtualenv venv`
3. Activate the environment `venv/scripts/activate`
4. Install development dependencies `pip install -r requirements.txt`

### Running tests
`pytest`

To run with coverage:

`pytest --cov`

### Making a release
1. Bump version number in `typedconfig/__version__.py`
1. Add changes to [CHANGELOG.md](CHANGELOG.md)
1. Commit your changes and tag with `git tag -a v0.1.0 -m "Summary of changes"`
1. Travis will deploy the release to PyPi for you.

#### Staging release
If you want to check how a release will look on PyPi before tagging and making it live, you can do the following:
1. `pip install twine` if you don't already have it
1. Bump version number in `typedconfig/__version__.py`
1. Clear the dist directory `rm -r dist`
1. `python setup.py sdist bdist_wheel`
1. `twine check dist/*`
1. Upload to the test PyPI `twine upload --repository-url https://test.pypi.org/legacy/ dist/*`
1. Check all looks ok at [https://test.pypi.org/project/typed-config](https://test.pypi.org/project/typed-config)
1. If all looks good you can git tag and push for deploy to live PyPi

Here is [a good tutorial](https://realpython.com/pypi-publish-python-package) on publishing packages to PyPI.
