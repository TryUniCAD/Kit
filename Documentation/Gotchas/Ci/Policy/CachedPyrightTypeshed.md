# Cached Pyright typeshed lookup

## Expectation

Invoking the cached pinned Pyright package should find its bundled standard-library declarations without contacting the package registry.

## Actual behavior

During PR #273's Windows static checks, registry lookup was unavailable.
Invoking a cached package's internal `dist/pyright.js` through the package-store links failed to locate its typeshed fallback, producing thousands of unknown-standard-library errors.
These errors did not establish defects in the checked source.

## Workaround

Prefer the cached package's public `index.js` entry point.
If invoking its internal entry point, pass `--typeshedpath` pointing to that same pinned package's `dist/typeshed-fallback` directory.
The corrected Pyright `1.1.414` invocation reported zero source diagnostics on the scoped comparison process files.
Keep the configured interpreter and repository configuration unchanged.

This was static checking only; it did not execute comparison tests.
