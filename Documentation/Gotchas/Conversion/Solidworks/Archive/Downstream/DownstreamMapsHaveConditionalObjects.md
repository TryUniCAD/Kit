# Downstream maps have conditional object framing

## Expectation

A counted key/value map emits an archive pointer tag for every key, including key zero, and the loaded map can be saved without normalization.

## Actual behavior

The exact 2026 `moDownstreamIdData_c` maps at runtime `f340`, `f380`, `f3c0`, `f400` and `f440` do not use that uniform framing. Store writes the key and emits the `uniqueIdInfo_c` object only if the runtime value pointer is nonnull. Read consumes that object only if the key's unsigned 32-bit value is nonzero. Zero-key and null-pointer presence must agree for a canonical native store/load pair.

A nonzero key followed by a null archive tag can be consumed by the raw reader, but native reconstruction skips the null result. It copies and destroys nonnull temporary unique-info records. The final point map consumes its point even for a zero key and then omits that runtime association. The integer set similarly sorts and deduplicates wire rows. Native reconstruction is therefore not a universal identity operation on the raw typed wire graph.

## Workaround

Preserve explicit wire rows, conditional object-tag presence and aliases in a raw codec. Keep native reconstruction as a separate modeled operation. Fail closed when a writer cannot satisfy the native key/value condition; do not add a null tag where no object is framed, discard a row silently, or claim a normalized save is byte-identical. These are fixed i32 counts, so neither shared variable-count grammar applies.

The [full field/context record](../../../../../../re/solidworks/records/DownstreamIdArchiveGrammar2026.md) and numeric original-PE spans supply the proof. Native malformed-row behavior and complete standalone replay remain unmeasured; no production codec is admitted by this note.
