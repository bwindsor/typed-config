### v0.1.2
Read properties in parallel for faster config loading. This does require the `get_config_value` method of any `ConfigSource` object to be thread safe.
Fix types for `cast` property of `key`.

### v0.1.1
Bugfix for when multiple `group_key`s are used within a composite config.

### v0.1.0
Initial release
