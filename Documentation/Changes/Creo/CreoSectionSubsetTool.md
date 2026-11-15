# Creo section subset tool

## Change

Adds `re/creo/tools/Subset.py`, a research-only container rebuild for PSB parts. It reconstructs a
part from its own directory and rewrites every row, every `NEXT_TOC_ENTRY` link, and every section
offset after sections are removed, replaced, blanked, or reserved in place.

It is the instrument behind the section-requirement bisection: it lets a caller ask Creo which parts
of a container are load-bearing.

## Behaviour

`Build(DataValue, Base, Drop, Replace, KeepSpace, Blank)`:

| Parameter | Effect |
| --- | --- |
| `Drop` | remove the row and its bytes; later sections shift down |
| `Replace` | substitute a body; the row keeps its name, its length is recomputed, the checksum is recomputed, and the follow-on gap becomes `#\n` |
| `KeepSpace` | remove the row but keep its byte extent as filler, so every later offset is unchanged |
| `Blank` | keep the row and its declared length, write `#` bytes over the body |

Every mode was validated against the retained vendor control. With no changes the rebuild is
byte-identical: `Build(src, base, set(), {}) == src`, `81539` bytes.

Layout rules the tool encodes, all measured:

- sections are physically ordered and each is followed by its own gap bytes, usually a literal `#\n`
  line that is excluded from the stored length;
- the directory is a chain of tables joined by `NEXT_TOC_ENTRY`, whose offset is the next table and
  whose length is that table's size (`81 * (rows + 1) + header`);
- column 7 is `-1` for kinds `9`, `11`, `b` and for `EMPTY_SPACE_FOR_REUSE`, `2` for kind `12`, and
  `1` otherwise;
- a row beginning with `#` is padding and is skipped, so removed rows can be filled rather than
  deleted when the row count must stay fixed;
- the first checksum column is `sum(stored body) & 0xffff`;
- the file ends with `#END_OF_UGC`.

Regions are delimited by table positions: the sections referenced from a table are not necessarily
physically after it, so a row's gap must be capped at its region end rather than run to the next row
in the same table.

## Use

```bash
PYTHONPATH=src python3 re/creo/tools/Subset.py re/creo/oracle/empty/solid_start_part_mmks.prt \
    /tmp/out.prt "Notes,IndentTag"
PYTHONPATH=src python3 re/creo/tools/Subset.py <part> /tmp/x.prt "?"
```

The second form lists section names.

## Result

Dropping the two table-3 sections (`IndentTag`, `FeatRefData`) still loads in Creo 2027.2.
Dropping any single model section (`Notes`, `PipeInfos`) or the display group fails with
`cannot be retrieved`, and blanking bodies fails with `Could not retrieve part`. See
[the required section set gotcha](../../Gotchas/Conversion/CreoRequiredSectionSet.md).

## Limits

- Research only. `src/` does not import it.
- It does not author sections; `Author.py` does that.
- `Replace` recomputes the first checksum only. The second checksum column is copied, because its
  meaning is still unidentified.
- `KeepSpace` filler bytes are `#`, which is a valid padding byte but not a section body.

## Documentation

- [Required section set gotcha](../../Gotchas/Conversion/CreoRequiredSectionSet.md)
- [Generative author](CreoGenerativeAuthor.md)
- [Container findings](../../../re/creo/container/Container.md)
