# Managed analysis can remain missing

## Expectation

An active managed code-quality configuration and a Python change ensure that
the corresponding analysis appears on the pull request.

## Observed behavior

On PR 142, head `2ec6c91a3bad613858f6bca66fb47d60786c20fd` targets
`codex/solidworks-2026-native` at `0a515f4f9030876d06a9e18f6eb369b3d135e59a`.
Its exact synthetic merge is `0a94cf2fd25e1f8ad1838cac92a3c4cf3a5ffe19`.
The native-file process, compatibility, lint, typing and repository policy jobs
completed successfully. The aggregate remained pending because no managed
code-quality run or check exists on either analysis reference at the observation
point.

The read-only code-quality setup endpoint reports `state=configured`, with
Java/Kotlin, JavaScript/TypeScript and Python enabled, a standard runner and a
weekly schedule. The managed workflow is active at
`dynamic/github-code-quality/codeql`. An absent run therefore does not establish
that setup is disabled.

The repository aggregator expects that managed analysis when its supported-code
predicate matches. It correctly remains pending without the required result.
Recent managed runs exist for pull requests targeting `main`; this correlation
does not prove that every other base branch is excluded. No branch filter has
been inferred from it.

Evidence: [PR 142](https://github.com/TryUniCAD/Kit/pull/142),
[aggregate run](https://github.com/TryUniCAD/Kit/actions/runs/43709808377), and
[passing native-file process](https://github.com/TryUniCAD/Kit/actions/runs/43709809670/job/132798700485).
The [setup API reference](https://docs.github.com/en/rest/code-quality/code-quality)
documents the separate read-only configuration endpoint.

## Workaround

Inspect the exact head and merge references, the managed workflow inventory and
the current setup independently. Preserve the pending requirement until the
provider delivers the required result or its scheduling is resolved through an
authorized repository owner. A passing job from another pull request, an older
head or a different validation phase is not the missing result.

This observation did not change repository settings, workflow conditions,
allowlists or required checks.
