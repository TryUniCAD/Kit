# Creo writer gap

## Current result

The adapter can replay a retained Creo source byte for byte.
It cannot author a new PSB part from a neutral model.

This is not a complete Creo writer.
The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) require a live feature tree, a solid body, measured volume and centre of mass, and a dimension edit that rebuilds.
None of those conditions is met for generated output.

## Why source replay is not enough

Source replay proves that the container and source digest survive a round trip.
It does not prove that Kit understands the authored records.
A neutral edit cannot be expressed by replaying the old bytes.

## Missing work

1. Decode the ladder's `dtm_id_tab` structure.
2. Decode the remaining `Sld_FeatDefs` records in `FeatDefs`; the first definition decodes through
   `ent_outl`, then the flat field-index approach stops at `0x3be`.
3. Decode the remaining geometry prototype lanes and the contour and topology references in
   `VisibGeom`; two plane prototypes and the first curve prototype decode, then the curve point
   array stops at `0x272`.
4. Map feature identity, parent links, dimensions, relations, and configuration overrides to the neutral model.
5. Prove which derived sections Creo recomputes after a feature edit.
6. Build a symbolic writer that recomputes every index, count, checksum, and derived section.
7. Measure a generated part in a fresh Creo process between healthy controls.
8. Change a driving dimension, rebuild, and measure the geometry change.

## Decoded so far

`re/creo/tools/TaggedStream.py` decodes the full `AllFeatur` feature chain of both controls:

| File | Feature chain |
| --- | --- |
| `empty/solid_start_part_mmks.prt` | `FRONT` (7), `TOP` (5), `RIGHT` (3), `DEFAULT_CSYS` (11, type 979) |
| `ladder/ladder1.prt.2` | the same four, plus `id 67` (type 923) |

The chain matches the model tree Creo shows.
The grammar is recorded in [the loader notes](../loader/Loader.md#tagged-stream-parser-status).
The empty control's `AllFeatur` now decodes end-to-end, including the footer
(`foot_first_feat_ptr = None`, `foot_layer_count = 0`) and the recursive `layer_list`.
The ladder's `AllFeatur` decodes the five features and the footer prefix, then stops at `0x130a`
on an `f8` array opener inside a scalar lane, which identifies a field-index misalignment in the
richer footer rather than a missing token. The empty control is unaffected.
`FeatDefsDtm` decodes the datum placement records through `ent_outl`.

## World-coordinate double encoding

`ent_outl`, `envlp`, and `outline` use the world-coordinate token lane, and the decode is
resolved. In the positional-outline/world lane, `46 <tail7>` reconstructs `40 <tail7>` (positive)
and `2d <tail7>` reconstructs `C0 <tail7>` (negative). The seven-byte sub-unit forms
`4f <tail6>` and `d5 <tail6>` reconstruct `3F <tail6> 00` and `BF <tail6> 00`. The `0x18` byte is
the one-byte 1.0 constant.

The empty control's `ent_outl` is `f9 02 03` (2x3) followed by
`46 6f ca 90 66 89 b9 7f e4 18 2d 6f ca 90 66 89 b9 7f e4 18`. It decodes to
`[254.33012701892218, 254.33012701892218, 1.0, -254.33012701892218, -254.33012701892218, 1.0]`,
a square in homogeneous coordinates. The ladder's `ent_outl` decodes to
`[186.8986780200836, -0.000125701882057086, 1.0, -156.82118748945425, -272.72085742045164, 1.0]`,
a rectangle in the sketch plane. The `VisibGeom` plane prototype's `envlp` decodes to
`[184.50782059963194, 86.06680966899467, -154.4303300690026, -115.65227549271083]` and its
`outline` to
`[184.50782059963194, 1.0, 115.65227549271083, -154.4303300690026, 1.0, -86.06680966899467]`.

Disproved hypotheses:

- ASCII hex string: `0x46` is a valid hex digit but `0x6f` is not, so the reader consumes one digit
  and fails.
- XOR mask to a valid hex string: no mask in `0..255` makes every byte a valid hex character.
- Raw 8-byte IEEE double in any byte window or byte order: no window gives a plausible outline
  coordinate.
- Two 4-byte floats per 8-byte group: only some halves are plausible, the rest are denormal or
  huge.
- Low-nibble hex string with `ugc_ieee_unformat_double`'s end-backwards byte order: the decoder in
  `re/creo/tools/PackedDouble.py` produces denormals (`1.4e-312`) for the empty control and huge
  values (`4.8e-154`, `-2.5e169`) for the ladder. The high-nibble variant is equally implausible.

The next decode target is the ladder's `dtm_id_tab` structure, then `Sld_FeatDefs`, then the
`VisibGeom` curve point array.

## One-feature ladder result

The first rung is authored and retained at `re/creo/oracle/ladder/ladder1.prt.2`.
It is a rectangle on `TOP` extruded as a solid with the default blind depth.
The paired empty control is `re/creo/oracle/empty/solid_start_part_mmks.prt`.

The ladder adds `FeatDefs`, `MdlRefInfo`, `IdsGenAllRepsDb`, `IdsGenSimpRepDb`, and `SldRegenRevInfo`.
`AllFeatur` grows by 4360 bytes and `VisibGeom` grows by 2868 bytes.
Those two sections are the next decode targets.
The section diff and the `DispDataTable` compression anomaly are recorded in
[the oracle notes](../oracle/Oracle.md).

## Next measurement

The next useful experiment is the second rung of the ladder:

- the same rectangle and extrude with a different depth;
- the same part with a second feature.

The second rung separates the depth parameter from the feature and sketch records.
The result must be recorded here before any writer field is promoted.

## Status

`vendor_loadable = False`
`application_usable = False`
`lossless = False`
`parametric = False`
