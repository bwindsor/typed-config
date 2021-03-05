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
