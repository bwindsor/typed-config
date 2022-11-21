### v0.1.1
Bugfix for when multiple `group_key`s are used within a composite config.

### v0.1.0
Initial release

### v0.1.2
Read properties in parallel for faster config loading. This does require the `get_config_value` method of any `ConfigSource` object to be thread safe.
Fix types for `cast` property of `key`.

### v0.1.3
Revert changes from 0.1.2. Parallel was unhelpful.

### v0.1.4
Add some logging
Add `__repr__` method to `ConfigSource`

### v0.1.5
Add more `__repr__` methods in `ConfigSource`

### v0.1.6
Fix: don't cast default value

### v0.2.0
Refactor to use a `ConfigProvider` which can be shared as a provider between all `Config` objects

### v0.2.1
Add `replace_source` and `set_sources` methods on `Config` and `ConfigProvider` for easier manipulation of sources

### v0.2.2
* Fix typing on `@section` decorator. This was previously preventing IDE autocompletion. The return type of the decorator now uses a generic to indicate that it returns the same type as it is passed. This means that whether or not it is passed a `Config` subclass is no longer type checked, but it means that the returned class has all the correct properties on it, which is more important. 
* Add basic `repr` function to `Config`

### v0.2.3
Version bump to build after move from travis-ci.org to travis-ci.com

### v0.2.4
Version bump to build after move from travis-ci.org to travis-ci.com

### v0.2.5
Version bump to build after move from travis-ci.org to travis-ci.com

### v0.3.0
Add `post_read_hook` method which can be added to `Config` subclasses to allow parts of the config to be modified after it has been fully loaded

### v1.0.0
BREAKING CHANGE: The `key` function now expects keyword arguments and will not accept non-keyword arguments any more.
Make compatible with mypy. 

### v1.0.1
Remove `include_package_data=True` from `setup.py` to ensure `py.typed` is included in source distributions

### v1.0.3
Make type annotations pass string Mypy checking.

### v1.1.0
Remove pointless casting of `default` value, since the `default` should be provided already cast, and should have the same type as the return value of the `cast` function. The also means that the type of a custom `cast` function should only need to accept a string as input, rather than having to check for if it has already been cast.

### v1.2.0
Fix `ImportError` for `typing_extensions` on Python <= 3.7, by requiring it as a dependency. This is because `Literal` is used as a type. This did not become part of the built in `typing` module until Python 3.8.

### v1.2.1
Enable CI testing on Python 3.10 and 3.11. Use `sys.version_info` to help with imports as mypy plays nicely with this. 

### v1.3.0
Drop running tests on Python 3.6 since it is end of life.

### v1.3.1
As part of a solution for issue #12, add cast submodule with enum_cast helper function
