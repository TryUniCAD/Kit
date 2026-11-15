# The small mark record is emitted with a writer chosen marker

## Behaviour

Four section-0 records in every fixture share one frame:

```text
02 02 41 00 38 01 03 02   <5 bytes>   <terminator>
```

The five byte payload is mostly zeros and carries at most one `81` marker; the terminator is
`00` or `01`. `ObjectSection.MarkRecord` rebuilds such a record with the marker written as `82`
and the terminator as `01`, and `RewriteMarks` applies it to every matching record. It runs in
`nx.author_sections` ahead of the nesting pass.

## Verification

Field mutation in NX 2506, measured before the emitter was written:

```text
81 marker -> 82                      loads
a 00 slot -> 01                      loads
14 byte trailing flag flipped        loads
```

so the marker and the terminator are both free, which is why a writer may choose them.
Writing all five fixtures and opening them:

```text
mk_empty.prt bodies 0      mk_multi.prt bodies 0      mk_var_blank.prt bodies 0
mk_const_box60.prt bodies 1 volume 36000.0
mk_dim40.prt bodies 1 volume 23999.999999999996
```

Section 0 provenance moves by four bytes per part:

```text
part             before  after
empty.prt           342    346
multi.prt           342    346
var_blank.prt       343    347
const_box60.prt     346    350
dim40.prt           346    350
```

## Limits

- Four records and four bytes. The marker's meaning is not known; it is free, not derived.
- The remaining 119 carried records in `dim40` are unchanged, and the class table is untouched.
