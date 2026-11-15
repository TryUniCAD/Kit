# A Creo section row with `1f 9d` must be decompressed before it is parsed

## Expectation

Some Creo PSB rows are Unix-compress streams and some are plain. Detecting which is a two-byte check on the
row's payload, so a probe that inspects a row's contents will decompress when needed and parse otherwise.

## Actual behaviour

The magic is **two** bytes, `1f 9d`. A check written as `Payload[:1] == b"\x1f\x9d"` compares a one-byte
slice against a two-byte literal, so it is `False` for every row: compressed rows then get parsed as if they
were plain, and the result is garbage tokens rather than an error.

Three rows in the empty control are affected — `SolidPersistTable` (`1125` bytes to `1788`),
`SolidPrimdata` (`235` to `301`) and `DispDataTable` (`819` to `1138`). Parsed without decompressing they
produce nonsense node names, and a probe that trusts that output would conclude the rows are opaque binary
when they are ordinary token streams.

The production code is correct: `Compress.py` checks `DataValue[:2] != b"\x1f\x9d"` and `Toc.py` uses
`BodyData.startswith(b"\x1f\x9d")`. Only ad-hoc probes are at risk.

## Workaround

Use `startswith(b"\x1f\x9d")` or a two-byte slice, and assert on the decompressed size against the
directory row's `expanded` column — a mismatch means the check was wrong, not that the row is opaque.

## Evidence

- `re/creo/data-model/DataModel.md` — the decompressed field inventory of both tables.
- `src/convert/adapters/creo/Compress.py`, `src/convert/adapters/creo/Toc.py` — the correct two-byte checks.
