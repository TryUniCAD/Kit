# Native save end words differ from construction defaults

## Expectation

A defaulted auxiliary field in the end specification carries its constructor value in every native save.

## Actual behavior

The 2026 end-spec constructor initializes the auxiliary `f158` word to zero. Saved through-all cuts of the same feature family carry different nonzero words even while the cut has the same active termination semantics and null distance owners. The disclosed cases have separate native source and edited save records.

## Workaround

Use the actual active end types, direction flags and owners for portable intent. Preserve the saved word in the typed archive. Use the independently verified initialization rule for freshly allocated construction.

See the [disclosed projection and field record](../../../../../../re/solidworks/records/PublicThroughAllRead2026.md).
