# typed-config
Typed, extensible configuration reader for Python projects for multiple config sources and good autocomplete performance.

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
print(config.host)  # Will be read from the environment variable DATABASE_HOST
```
In PyCharm, and hopefully other IDEs, it will recognise the datatypes of your configuration and allow you to autocomplete. No more remembering strings to get the right thing out!

## How it works
Configuration is always supplied in a two level structure, so your source configuration can have multiple sections, and each section contains multiple key/value configuration pairs.

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

This will throw an exception if any required config value cannot be found, and will also keep all read config values in memory for next time they are used.

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

* `section_name` - this name of the section in the configuration source from which this parameter should be read. This can be provided on a key-by-key basis, but if it is left out then the section name supplied by the `@section` decorator is used. If all keys supply a `section_name`, the class decorator is not needed.
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
config = AppConfig()
```
In this example we have three ways of casting:
1. Not casting at all. This default to returning a `str`, but your IDE won't know that so if you want type hints use `cast=str`
2. Casting to an built in type which can take a string input and parse it, for example `int`
3. Defining a custom function. Your function should take one string input and return one output of any type. To get type hint, just make sure your function has type annotations.
4. Using a lambda expression. The type inference may or may not work depending on your expression, so if it doesn't just write it as a function with type annotations.

## Configuration Sources
Configuration sources are how your main `Config` class knows where to get its data from. These are totally extensible so that you can read in your configuration from wherever you like - from a database, from S3, anywhere that you can write code for.

You supply your configuration source to your config after you've instantiated it, but **before** you try to read any data from it:
```python
config = AppConfig()
config.add_source(my_first_source)
config.add_source(my_second_source)
config.read()
```

This is bad practice, but if for some reason you do add further config sources after it's been read, you'll need to clear any cached values in order to force re-reading of the config. You can do this by
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
source = EnvironmentConfigSource(prefix="XYZ")
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
The most basic source, entirely in memory, and also useful when writing tests.
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
An abstract base class `ConfigSource` is supplied. You should extend it and implement the method `get_config_value` as demonstrated below, which takes a section name and key name, and returns either a `str` config value, or `None` if the value could not be found. It should not error if the value cannot be found, `Config` will throw an error later if it still can't find the value in any of its other available sources.

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
        for v in self.data.values():
            assert type(v) is dict

    def get_config_value(self, section_name: str, key_name: str) -> Optional[str]:
        # Extract info from data which we read in during __init__
        if section_name not in self.data:
            return None
        return self.data[section_name].get(key_name, None)
```

## Contributing
Ideas for new features and pull requests are welcome. PRs must come with tests included. This was developed using Python 3.7.

### Development setup
1. Clone the git repository
2. Create a virtual environment `virtualenv venv`
3. Activate the environment `venv/scripts/activate`
4. Install development dependencies `pip install -r requirements.txt`

### Running tests
`pytest ./test`
