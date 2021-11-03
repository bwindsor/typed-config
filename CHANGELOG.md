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
