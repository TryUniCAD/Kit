# CATIA parameter names live in relation formulas

## Expectation

A parametric `CATPart` stores each parameter as a named object, so a decoder can pair a name such as
`d_dia` or `d1` with the `0xe6` double that holds its value and produce a name-to-value table.

## Observed behavior

Measured with `convert.adapters.catia.Parametric` over the five vendor samples in
`re/catia/examples/parametric/`:

- Every sample declares exactly one relation input, and its name is `LENGTH`:
  `RelationNames` returns `('LENGTH',)` for all five. The name only appears inside the relation
  formula symbol `(#1_ :  #In LENGTH) : LENGTH`, not as an attribute key.
- Attribute blocks do carry dimension names — `ISO_1207` has `d_dia`, `dk_nom_head_dia`, and
  `n_nom_Slot_Width`, and the other screws have `d_dia` — but the block value list is
  `int <id>, ref <4 bytes>` and never contains a double. The id varies per occurrence (`d_dia` has 4
  distinct signatures in `ISO_1207`, 17 in `ISO_2010`), so it indexes something rather than carrying
  the number.
- The doubles sit in separate `7c 05` objects that carry a single attribute named `MAvalue` and no
  name of their own. `ISO_2338` object `52` holds `50.0`, object `75` holds `0.8`.
- The washer's symbol table has no `d_dia`, `d1`, `d2`, or `h`. Its only parameter name is `LENGTH`,
  with the relation `(#1_ :  #In LENGTH) : LENGTH` and the expression `0.375*#1_`. So the ISO 7089
  washer's `8.4`, `16.0`, and `1.6` are present as doubles but their names are not in the file.

## The reference payload is not an object number

Each dimension attribute carries `int <id>` followed by a 3-byte (`e8`) or 4-byte (`e9`) reference.
Those payloads were tested against the object numbers read from every `7c 06` header:

```
ISO_2338_PARALLEL_PIN   object numbers 88    reference payloads 381  56 distinct
ISO_1207_CHEESE_HEAD    object numbers 243   reference payloads 1107 88 distinct
ISO_7089_WASHER         object numbers 84    reference payloads 358  58 distinct
```

the most common payload is `c01737` (21, 125, and 26 occurrences), and the frequent ones all end in
the same byte `0x37`. resolution rates:

```
interpretation     pin     ISO_1207
u32 little-endian  0.000   0.000
u32 big-endian     0.000   0.000
u16 at offset 0   <=0.02   <=0.02
u16 at offset 1   <=0.02   <=0.002
u8 at each offset  <=0.59   <=0.94
```

the only `u8` offset above chance is the constant trailing byte `0x37` (55), which lands in the object
set only because object number `55` happens to exist. the tag-difference encoding does not fit either:
of the 56 distinct payloads only 6 even begin a valid tag, and none of them consume the whole payload.

so the reference is not an object number, a `u16`, a `u32`, or a tag array. it is a container tag that
resolves through a save-order tag table, and that table is not in `MainDataStream`, `SurfacicReps`, or
the OSMX object graph this reader parses. binding a name to a value therefore needs either the tag
table or a vendor dump, not another scan of these streams.

## Workaround

Read the names from the relation formulas and the values from the `MAvalue` objects, and treat the
mapping between the two as unknown:

```python
from convert.adapters.catia.Parametric import AttributeValues, RelationNames
```

`RelationNames` returns the `#In` inputs of every relation formula and `AttributeValues` returns every
`7c 07` attribute with its decoded values. Do not build a name-to-value table from them: the
dimension block identifies the attribute kind, and the reference it carries is what names the owning
object, which is not resolved.

## Evidence

- `src/convert/adapters/catia/Parametric.py`
- `tests/convert/catia/CatiaNativeTests.py` (`TestParamName`)
- `re/catia/FeatureGraph.md`
- `Documentation/Changes/Catia/CatiaNativeBrep.md`
