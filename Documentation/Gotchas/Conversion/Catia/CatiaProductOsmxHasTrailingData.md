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

The assembly tree itself is still not extracted. In `Tilton_Set.CATProduct` the product OSMX holds
15 objects, `15` records each of `7c 05`, `7c 06`, `7c 07`, `7c 09`, and `7c 0a`, plus one each of
`7c 04`, `7c 08`, `7c 0b`, and `7c 0c`. The attribute blocks are keyed by numbers up to `0x51` while
the section holds only `42` symbols, so they use the same numeric attribute-id space as the CATPart
early attributes.

The instance data sits in the `7c 09` records, not the `7c 07` blocks. Every instance record begins
`14 00 e5 2e 00 00 00 11 03 55 8c 3c 65 00 00 31 0c 67 0c 08 <reference> 00 00 02 <id> 07 00 00 00
05 00 09 0<level> 00 00 00 00 0c ... 04 <parent> 08 0c 67 <child>`, where `0x0c` is the `_Source`
symbol, `0x04` is `ASMPRODUCT`, `0x05` is the product name (`Tilton`), and the `0<level>` byte runs
`02`, `03`, `04` across siblings. Decoding the tree means decoding that relation, which is a separate
piece of work from the B-rep acceptance terms and cannot be vendor-verified in this environment.

## Evidence

- `src/convert/adapters/catia/Container.py` `ParseOsmx`
- `re/catia/examples/.CATProduct/` (three files, `42`/`104`/`41` symbols after the fix)
- `Documentation/Changes/Catia/CatiaNativeBrep.md`
