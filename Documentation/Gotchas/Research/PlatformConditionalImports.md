# Platform aliases can hide conditional imports from Mypy

## Expectation

A platform guard should keep Windows-only imports outside a Linux type check.

## Actual behavior

Mypy did not recognize guards using the imported platform value or the `System` module alias.
It reported missing Windows attributes even when runtime execution could not enter those branches.
Local imports also remained subject to semantic analysis before function control flow excluded their branch.

## Workaround

Use the canonical `sys.platform` expression for platform checks understood by Mypy.
Place platform-specific imports in module-level conditional branches.
Keep their uses inside the matching explicit function branches.
This also prevents Windows checks from reading POSIX-only signal imports.

Focused checks with pinned Mypy 2.4.1 passed for seven changed files with both Linux and Windows targets.
These static checks do not establish native process behavior.
See [Mypy's platform-check documentation](https://mypy.readthedocs.io/en/stable/common_issues.html#python-version-and-system-platform-checks).
