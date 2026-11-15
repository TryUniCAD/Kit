# A CATProduct OSMX section is followed by more stream data

## Expectation

An OSMX archive is the whole stream: the symbol table starts at the offset stored at byte 100 and its
declared section length runs exactly to the end of the stream, so a section length that does not reach
the end means the stream is truncated or the offset is wrong.

## Actual behavior

That holds for `CATPart` streams and is what the reader enforced, but not for `CATProduct`. The
product structure stream carries an OSMX section and then keeps going: `Tilton_Set.CATProduct` has
`OSMX` at offset `176` of a `3976`-byte stream, `Brake_Pedal_Assembly - Backup 1.CATProduct` at `280` of
`31384`, and only the small summary streams start with `OSMX` at offset `0`. Enforcing the equality
rejected every real product stream with `OSMX symbol table length is inconsistent`.

## Workaround

The reader now accepts a section that ends before the stream does: it rejects only a section that
would pass the end (that is genuine truncation), and parses against the section, not the stream. After
the change all three `CATProduct` files parse their OSMX (`42`, `104`, and `41` symbols, including
`ASMPRODUCT`, `_PartNumber`, `_Component`, `_Source`, and `_RepresentedBy`), and the 27 `CATPart`
files still decode with the same five heuristic warnings.

The assembly tree itself is still not extracted: the `_PartNumber` and `_Source` attributes do not
appear in the `7c 07` blocks of the product stream, so the instance list is encoded in the
`CATProdCont` payload rather than the attribute graph.

## Evidence

- `src/convert/adapters/catia/Container.py` `ParseOsmx`
- `re/catia/examples/.CATProduct/` (three files, `42`/`104`/`41` symbols after the fix)
- `Documentation/Changes/Catia/CatiaNativeBrep.md`
