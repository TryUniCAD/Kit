# Expression slot objects are rewritten from their handles

## Behaviour

`ExprSection.RewriteSlots` walks the object table of an expression section and rebuilds
every 18 byte slot with `SlotObject` and every 21 byte slot with `ValueSlot`, so the bytes
come from the encoders rather than the source buffer. It runs for section 2 in
`nx.author_sections`, after the anchor patch.

## Verification

Section 2 is byte-identical afterwards, as expected: the values are the same, so
re-encoding them reproduces the same bytes.

```text
dim40.prt         section2 differing 7   (the anchor only)
const_box60.prt   section2 differing 7
empty.prt         section2 differing 7
multi.prt         section2 differing 6
var_blank.prt     section2 differing 6
```

Writing and loading in NX 2506:

```text
ex_empty.prt       bodies 0
ex_multi.prt       bodies 0
ex_var_blank.prt   bodies 0
ex_const_box60.prt bodies 1  volume 36000.0
ex_dim40.prt       bodies 1  volume 23999.999999999996
```

## Limits

- This rewrites the slots only. The six fixed objects, the names lane, the records and the
  placement are still carried, so `ExprMiddle` has no `Dimensions` parameter yet.
- Provenance does not move: re-encoding identical values yields identical bytes.
