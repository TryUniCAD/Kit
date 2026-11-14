# NX object model section bodies cannot be transplanted between parts

## Expectation

Because a payload is a directory of sections and the section index is fully
remapped when bodies change length, moving a section body from one part into
another should produce an equivalent part.

## Observed behavior

It produces a file NX will not open. Two parts with the same section count and
the same total payload length still fail:

```text
empty.prt payload, bodies taken from empty_expr.prt   same 36682 bytes
NX 2506                                               fails to open
```

A section body carries payload-absolute references and part identity, so a body
copied from another file points at the wrong places even when the layout math is
correct. Only a body generated for the target payload, with its own header,
pointer and lanes, is valid.

The same limit applies to a naive global pointer remap: rewriting every four byte
value that equals a moved boundary corrupts unchanged bodies that merely happen
to contain such a value.

## Workaround

Generate the section body for the payload being written, as
`re/nx/tools/ExprBuild.py` does, then splice it with
`PayloadBuild.ResizePayload`. Replacing a generated body is supported; replacing
a foreign one is not.

## Evidence

```text
empty.prt bodies replaced by empty_expr.prt bodies   NX fails to open
generated expression body spliced into empty.prt    STATUS 0, EXPRESSION kit_len 12.5
identity replacement on four real parts             byte identical
```
