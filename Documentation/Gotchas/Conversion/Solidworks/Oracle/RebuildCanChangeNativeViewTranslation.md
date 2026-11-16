# Rebuild can change native view translation

## Expectation

A SOLIDWORKS-authored part that preserves its explicit camera through save and
fresh initial opening also preserves it through the next forced rebuild.

## Actual behavior

The first tree-source attempt's reversed two-direction Top-plane boss preserved
its initial saved pose, then failed the unchanged translation comparison after
the fresh rebuild and geometry snapshot. The first translation component was
`0.007068387670026221` against the originally requested `-0.003173`.
The mid-plane source and both batch controls passed. Cleanup left no CAD process
and kept all licensing process identities unchanged.

The [failed source receipt](../../../../../re/solidworks/measurements/2026/TreeSourceAttempt01.json)
retains the original error and both source outcomes. No generated writer output
was involved. This observation does not establish which native rebuild or query
operation caused the change, nor a general translation formula.

## Workaround

Keep the source failure and its original target. Do not loosen the comparison,
adjust the expected pose or count the failed source as accepted. The first pair
is ineligible as fresh unseen evidence. For the separate bounded folder-topology
question, author different independent ordinary blind inputs before the writer
change. Mixed-end rebuild/view behavior remains unfinished research.
