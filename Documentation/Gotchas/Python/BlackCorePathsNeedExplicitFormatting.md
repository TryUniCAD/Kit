# Core paths need explicit Black formatting

The repository Black force-exclusion expression `(examples|modules|re)/` also matches the `re/` suffix of a directory named `Core`. Passing explicit files under `Core/` can therefore report that no Python files are present and exit successfully without formatting them.

For a bounded explicit production-file check, preserve the configured Black rules and override only that path exclusion with `--force-exclude '^$'`. Verify that the expected source count is processed. Do not count a no-files result as a successful format check. Research paths remain exempt in their normal repository workflow.

The [cold-circle record](../../../re/solidworks/records/SdkColdCircleRead2026.md) distinguishes the first no-files attempt from the actual 17-file formatting check.
