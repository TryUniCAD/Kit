# `DispDataTable` does not decompress with the current Creo LZW decoder

## Expectation

Creo rows whose payload begins `1f 9d` are Unix-compress streams. `Toc.ReadSection` decompresses them and
checks the result against the directory's `expanded` column, so every such row should read back whole.

## Actual behaviour

Two of the three compressed rows in the empty control decompress exactly:

```text
SolidPersistTable    OK expanded 1788 (declared 1788) head e0 00 70 67 6c 5f 70 65 72 73
SolidPrimdata        OK expanded 301 (declared 301)   head e0 00 70 67 6c 5f 70 72 69 6d
DispDataTable        FAILS: CreoFormat: Creo compression code is outside the table
```

`DispDataTable` (`819` bytes on disk, `1138` declared) is the only compressed row that fails, and it is the
only one whose directory kind is `c`. Every row that decodes is kind `a` or `12`:

```text
ND:0:Model_L05_PX:1        kind a  -> ok 1662
ND:0:UnitSystemDef_L03:1   kind a  -> ok 907
ND:0:PDMTrail_L03:1        kind a  -> ok 1490
SolidPersistTable          kind a  -> ok 1788
SolidPrimdata              kind a  -> ok 301
THMB_IMG_MAIN              kind 12 -> ok 1653
DispDataTable              kind c  -> FAIL
```

The compression flags are identical for all of them (`maxbits 16`, block mode off), and the body is sliced at
the same `#<name>\n` line, so the failure is in the stream rather than in how it is located: with the current
decoder its third code is `302` against a table of `258`, which cannot follow a first literal of `224` in an
LZW stream.

The width-growth threshold was tested at offsets `0`, `-1`, `+1` and `-2`; the current `0` decodes six of the
seven rows and every other offset either breaks those six or still fails this one. So this is not an
off-by-one in the decoder: `kind c` payloads most likely use a different codec.

## Workaround

None needed for document reading. Do not assume "the row is compressed and the magic matched, therefore the
decoder can read it" — check the row against `expanded`, and treat a `CreoFormat` from `Uncompress` as a
decoder limitation rather than corrupt input.

## Evidence

- `src/convert/adapters/creo/Compress.py` — `SelectCode` raises when a code exceeds the table size.
- `src/convert/adapters/creo/Toc.py` — `ReadSection` decompresses and verifies `expanded`.
- `re/creo/data-model/DataModel.md` — the decompressed field inventory of the two rows that do work.
