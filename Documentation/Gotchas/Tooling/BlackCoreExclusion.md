# Black can exclude Core paths

A direct Black command can report success without checking Python files under a `Core/` directory.

The `force-exclude` expression in [pyproject.toml](../../../pyproject.toml) contains `re/` without a path boundary.
That alternative also matches the end of `Core/`.
An explicit file argument does not override `force-exclude`.

For an affected file, run Black through standard input from the repository root:

```sh
black - < src/convert/adapters/solidworks/Core/Adapter.py
black --check - < src/convert/adapters/solidworks/Core/Adapter.py
```

The first command prints formatted source without changing the file.
Apply that source to the same file, then run the check command.
Black still uses the repository configuration.

PR 204 exposed this behavior when direct formatting left Core source unchanged, while standard-input formatting changed that source.
The review follow-up used Black 26.10.1 through standard input and checked the resulting files.
