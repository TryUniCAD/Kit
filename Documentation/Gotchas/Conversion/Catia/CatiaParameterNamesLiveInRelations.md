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
