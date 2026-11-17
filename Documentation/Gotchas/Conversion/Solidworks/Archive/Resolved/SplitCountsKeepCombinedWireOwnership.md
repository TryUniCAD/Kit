# Split counts keep combined wire ownership

## Expectation

Every high-u32/low-u32 count can use the same model keys as two separately
persisted scalar fields.

## Actual behavior

The ordinary mate-group `f4e8` collection writes the high u32 followed by the low
u32, but its research model retains one `f4e8#count` value. Other shared array
rules retain two independently named source words. Reusing their key ownership
would add a spurious low-word field and lose the combined wire count identity,
even when a zero-count byte comparison happens to pass.

## Workaround

Keep wire framing distinct from field ownership. The combined mode reconstructs
`(high << 32) | low` under the single count key. Its writer derives the count from
modeled rows and emits high then low. The existing separately named split mode
remains unchanged. Both retain the existing ten-million repetition bound.

This is a source-grammar finding, not a new array default or native acceptance
result. See the [resolved ledger](../../../../../../re/solidworks/records/ResolvedBodyGrammar2026.md)
and [change entry](../../../../../Changes/Solidworks/Archive/SolidworksTypedResolvedGraph.md).
