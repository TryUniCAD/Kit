# The nesting record is emitted with canonical heads

## Behaviour

The unvalidated nesting member of the `5f 01 04 01` family is parsed into segments and
re-emitted with every segment head written as `03`:

```text
02 02 ff 00 5f 01 04 01    frame
03 01 x15                  segment: head and leaves
11 01 x8                   a separator segment, previously 11
02 02                      terminator
```

`ObjectSection.RewriteNesting` rebuilds each nesting record from the leaf counts it
reads, so the bytes come from the writer rather than from the source buffer. It runs in
`nx.author_sections` with the other section-0 passes.

## Verification

Section 0 provenance moves, for the first time in several turns:

```text
part            before   after   payload identical after
empty.prt          340     342                    99.00%
multi.prt          340     342                    99.02%
var_blank.prt      341     343                    99.00%
const_box60.prt    344     346                    99.14%
dim40.prt          344     346                    99.14%
```

Writing and loading all five in NX 2506:

```text
nst_empty.prt bodies 0   nst_multi.prt bodies 0   nst_var_blank.prt bodies 0
nst_const_box60.prt bodies 1   nst_dim40.prt bodies 1
```

The change was first established by mutation: a leaf `01 -> 02`, a separator `11 -> 12`,
a head `03 -> 04` and the terminator's last byte each load, so the record carries no
structure NX validates.

## Limits

- The meaning of a `11` head is not known. Normalising it to `03` changes a display or
  settings record, not geometry, and only two bytes per part move.
- `TestNxNest` checks the parse, the rebuild and the canonical rewrite.
- Section 0 is still ~99% source bytes; this is two more.
