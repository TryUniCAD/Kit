# Check-prefixed helpers are collected as tests

## Expectation

A helper named `CheckPlanes` inside a test module only runs when the integration
test calls it with its subprocess report.

## Observed behavior

The repository's [pytest configuration](../../../../pyproject.toml) includes
`Check*` in `python_functions`.
The remote [model-builder workflow](https://github.com/TryUniCAD/Kit/actions/runs/43677223605)
ran the actual subprocess/container test successfully, then failed because pytest
also collected its `CheckPlanes` and `CheckSystems` helpers and looked for their
`Report` argument as a fixture.

## Workaround

Use a helper name outside the configured test prefixes, such as `AssertPlanes`,
or keep the helper in a support module.
Keep intentional test entry points under the configured names.
Do not change collection rules to hide an accidentally collected helper.
