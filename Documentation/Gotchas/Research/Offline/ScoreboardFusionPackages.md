# F3Z scoreboard routing

## Expectation

Every pinned Fusion asset should contribute a decode or a native archive
refusal to the research scoreboard.

## Observed behavior

The public format registry has no `fusion.f3z` adapter. Scoring the pinned
`example1.f3z` through that registry produced one `AdapterNotFoundError`.
The existing Fusion research reader reached both archive checks and refused
the same bytes because partial mode could not find the active design stream.

## Workaround

Route F3Z through the existing Fusion research reader in the scoreboard.
Keep the strict and partial refusal reasons and use the public registry for
the existing public formats. Run [the pinned scoreboard](../../../Changes/Research/Automation/ReadScoreboard.md)
to inspect its result.
