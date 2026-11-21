# Assembly warning 32 does not identify its producing document

## Expectation

An assembly regeneration warning identifies an unsolved parent mate, or follows the exact cached-update predicate previously proved for a part.

## Actual behavior

The exact 2026 build has separate part, ordinary assembly and shared-policy publishers of internal API code 128. The common API translates that code to warning 32. The ordinary assembly publisher has its own selected-configuration request path. Its model query uses `moNode::needsUpdate`; the part's additional cached-update branch is a different concrete method. A mate-group update query participates in assembly scheduling, but its result is not proved equivalent to a serialized unsolved-mate word.

## Workaround

Record the actual API publisher caller and receiver/path during an unchanged open. Keep child and parent update state, mate state and policy separate. Do not clear flags, change ask policy or fit a saved stamp to suppress the warning. [Exact source map and replay](../../../../../../../re/solidworks/records/AssemblyNeedsRegen2026.md)
