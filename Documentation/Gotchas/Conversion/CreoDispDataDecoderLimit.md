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

`DispDataTable` (`819` bytes on disk, `1138` declared) starts `1f 9d 10 e0 1e c5 73 29`, while the two that
work start `1f 9d 10 e0 00 c0 39 c3 e6 0b`. The decoder raises `CreoFormat` from `Compress.SelectCode` when a
code exceeds the current table size, so this looks like a code-width or table-reset difference rather than a
wrong offset: the row's slice and magic are correct, and `expanded` is larger than the stored size as
expected for a compressed row.

The defect is **latent** today: `DispDataTable` is display pipeline data and the adapter does not consume it.
It matters for a complete reader, and it would matter for any attempt to treat that row the way `FeatDefsDtm`
was treated.

## Workaround

None needed for document reading. Do not assume "the row is compressed and the magic matched, therefore the
decoder can read it" — check the row against `expanded`, and treat a `CreoFormat` from `Uncompress` as a
decoder limitation rather than corrupt input.

## Evidence

- `src/convert/adapters/creo/Compress.py` — `SelectCode` raises when a code exceeds the table size.
- `src/convert/adapters/creo/Toc.py` — `ReadSection` decompresses and verifies `expanded`.
- `re/creo/data-model/DataModel.md` — the decompressed field inventory of the two rows that do work.
