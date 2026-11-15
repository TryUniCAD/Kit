# Creo AllFeatur mask values are required, and the encoding is not the problem

## Expectation

`AllFeatur`'s `cr_flags_xar` is a large array of signed 32-bit values (402 bytes in the first record).
It reads like dirty-state flags, so the natural assumptions are that the loader ignores it, that a
default vector works, or that the tricky part is reproducing the byte encoding.

## Actual behaviour

The encoding is not the hard part. It is `f1` `f8 <count>` then run-compressed signed integers, and
`Author.CompactInt`, `Author.SignedInt`, `Author.SignedIntArray`, `Author.SignedIntElements` and
`Author.FlagValue` reproduce every one of the thirteen lanes in the two retained controls exactly,
definition and replay form alike. The full table is in
[the feature record page](../../../re/creo/data-model/FeatureRecord.md).

The values are the hard part, on three counts.

**They are required.** `re/creo/tools/OmitMask.py` removes the field from all four records — record
one's header, its `f1 f8 80 fc` array introduction and its elements, plus the element runs in the three
replay records. `AllFeatur` drops from `3478` to `1873` bytes with no occurrence of the name left. Creo
exits with no `End` line and no `dbg_err_crash`. There is no default.

**They are validated.** Every value `-1` fails, every value `0` fails, and one value `-1` → `-2`
loads. The two natural "no state" vectors are both rejected.

**They are not a per-class constant.** The same class `923` carries `252` slots in the empty control and
`311` in the ladder, the ladder varies from feature to feature (`311`, `278`, `0`), and the ladder's
protrusion differs from its own datums at `195` of `252` slots. The leading `252` values do coincide
across the two documents, so the lane grows like an append-only per-field table as the document's schema
grows — but its length is per feature and per document.

## Workaround

There is none that stays within the no-donor-blocks rule, and two tempting shortcuts are traps:

- **Do not conclude that the lane is token- or size-constrained.** That was my own earlier error: two
  rejected candidates were malformed by my encoder, and a value-preserving re-encode at `471` bytes
  loads fine. A hypothesised `0x1a0`-byte cap from the accessor family's `size(kind)` values is
  disproved by that same launch.
- **Do not treat the vector as a per-class table.** It is derived state that varies per document and per
  feature. Transcribing one document's vector would fit exactly one document, which is the donor-data
  failure mode rather than a workaround.

The remaining question is what computes the vector.

## Evidence

- `re/creo/tools/OmitMask.py` — removes the field from every record.
- `re/creo/tools/LaneCap.py` — value-preserving re-encode at a chosen size.
- `re/creo/data-model/FeatureRecord.md` — encoder table, the 13-lane verification, slot-count survey,
  edit matrix.
- `re/creo/loader/FeatureStruct.md` — `.ddt` registry and why its accessor route is closed.
- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — launch logs.
