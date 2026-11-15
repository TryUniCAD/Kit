# The Creo replay encoder takes its field spans from the stream parser

## Expectation

`StreamParser` and `Author.ReplayOf` are independent: the parser reads a part, the replay encoder writes a
positional copy of a definition. So a parser improvement should not change emitted bytes.

## Actual behaviour

`Author.ReplayPieces` builds a replay by walking the definition with `StreamParser` and recording the byte span
that each `ReadField` call consumed:

```python
    def ReadField(Descriptor) -> object:
        Start = Parser.Reader.Position
        Node = Original(Descriptor)
        Spans.append((Descriptor.name, Definition[Start : Parser.Reader.Position]))
        return Node

    Parser.ReadField = ReadField
    Parser.Run()
```

Every emitted byte therefore comes from a span the parser decided. Changing how the parser consumes a record
changes the replay, and the replay is what Creo validates.

Measured directly: teaching the parser to skip a replay element opener (`e2`/`e3`) before a scalar field, and to
step one field back for the vendor's `f2 <selector> <opener>` form, made the vendor's `segtab_ptr` decode exactly
(`3827` of `3827` bytes, `pointid` `[[0,1], [1,2]]` instead of `[[0,1], []]`). It also changed the generated
`AllFeatur` payload from `1876` to `1871` bytes, and the 47-row generative part that had loaded twice was then
refused:

```text
!15-Nov-26 12:13:48  Start C:\Mac\Home\Documents\creo-authored\gen_rows.prt
std.out: Sld_Features
          first_feat_ptr
           idtab_ptr
            srf_id_tab_ptr
```

Reverting the parser restored `1876` bytes and the part loaded twice again:

```text
!15-Nov-26 12:24:23  End   C:\Mac\Home\Documents\creo-authored\gen_rows.prt
!MT_CUST - Applied settings for mode # 1 : MT Part Solid
```

## Workaround

Treat parser and replay as one unit. Any change to `ReadField`, `ReadValue`, `ReadArray` or the selector handling
in `Run` must be re-verified by a Creo launch of the generated 47-row part, not just by `Verify.py` and the
reader's own counts, because the replay bytes move with it.

If a parser fix is only needed for reading (for example, to recover the sketch's segment topology for research),
give it a separate entry point rather than changing `ReadField` for every caller.

## Evidence

- `re/creo/tools/Verify.py` — the ledger that did *not* catch this: all 16 checks still passed with the broken
  replay, because `AllFeatur`'s size assertion was the only hint.
- `Documentation/Changes/Creo/CreoGenerativeAuthor.md` — the measurement above.
- `src/convert/adapters/creo/Author.py` — `ReplayPieces`.
