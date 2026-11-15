# Creo AllFeatur masks are required and are per-class, not per-document

## Expectation

`AllFeatur`'s `cr_flags_xar` is a large opaque array of 32-bit masks (402 bytes in the first record).
Since the masks look like dirty-state flags, the natural assumption is either that the loader ignores
them, or that they are per-document state a fresh part can regenerate.

## Actual behaviour

Three assumptions were tested on the retained controls with `re/creo/tools/Subset.py` as the rebuild and
one Creo 2027.2 launch each.

**The field cannot be omitted.** Removing record 0's field header, its `f1 f8 80 fc` array introduction
and its 398 element bytes, plus the 398-element runs in the three replay records, shrinks `AllFeatur`
from `3478` to `1873` bytes with no occurrence of the name left. Creo exits with no `End` line and no
`dbg_err_crash`. So there is no default.

**The lane is not value-driven or size-driven.** Replacing the repeats with explicit copies of the same
values fails, re-encoding the same values canonically fails, all-`-1` fails and all-`0` fails, while a
one-byte change to a single value loads. The accepted form is the control's token shape with limited
freedom inside it.

**The vector is per feature class, not per document.** Across the two unrelated retained controls:

| Comparison | Result |
| --- | --- |
| datum planes 7 / 5 / 3 (class `923`) | identical to each other, in both files |
| empty control's 252-entry vector vs the ladder's first 252 entries | identical |
| csys (class `979`) vs a plane | differs at exactly 2 slots, `28` and `236`, the same in both files |
| ladder protrusion (class `917`) vs a plane | differs at 195 of 252 slots |

A datum-only part and a part with solid geometry produce byte-identical datum masks. So the vector is a
function of the class set, and the ladder's is the empty control's 252 values with 59 appended.

## Workaround

There is none that stays within the no-donor-blocks rule. The vector is ordered schema data read back
from vendor saves: stable across documents, but copied rather than computed. Generating it means either
decoding the bit semantics from the loader — where the 210 `.ddt` accessors cover only parenthesised
union members, and plain fields sit at compile-time struct offsets — or accepting a transcribed
per-class table as format knowledge.

Do not assume that "the values are the same in two files" makes them generatable. It makes them
*stable*, which is a different property, and it is exactly the property a captured table has.

## Evidence

- `re/creo/tools/OmitMask.py` — removes the field from every record and reports the resulting sizes.
- `re/creo/data-model/FeatureRecord.md` — full edit matrix, replay-form byte layout, per-class
  measurements.
- `re/creo/loader/FeatureStruct.md` — the model module, the `.ddt` registry, the accessor family.
- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — launch logs.
