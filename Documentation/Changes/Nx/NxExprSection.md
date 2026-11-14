# The writer emits the expression section of a part without expressions

## Behaviour

`convert.adapters.nx.ExprSection.ExprMiddle` builds the 337-byte expression
section middle (section 2) for a part that carries no expressions, from named
fields: the flag lane, the body relative pointer to the version block, the zero
run, the six object offsets computed from the object sizes, the order array, the
version and `SYSTEM` block, the head object with its anchor, the descriptor whose
references are all absent, the four `EXP_*` system names, the empty occupancy
lane, the default group record and the group record.

`nx.author_sections` regenerates section 2 when it carries six objects, and only
patches the anchor identity otherwise.

## Verification

The generated middle reproduces the source byte for byte when given its identity:

```text
empty.prt  base 0x268  len 337  identical True
```

Writing through the adapter and opening in NX 2506:

```text
exp_empty.prt        sections 1, 2 and 3 generated, section 0 copied
                     unloaded 0  bodies 0
exp_const_box60.prt  unloaded 0  bodies 1  volume 36000.0  area 7199.999999999999
```

`TestNxExpr` checks the length, the pointer, the computed object table, the order
count, the version tag, the head object, the generated identity and the
short-identity guard.

## Expression-bearing shapes

For a part whose expressions are block dimensions the object inventory follows a rule
rather than the feature:

```text
objects = 6 + 6n          n expressions
dim40, const_box60   n=3   24 objects
var_two              n=6   42 objects
```

which is the six fixed objects (head, lane descriptor, names lane, occupancy block,
default group, group record) plus, per expression, five property slots and one record.
That is the same 5:1 ratio measured earlier, now expressed as a count.

Other feature families do not obey it — `var_sph` with one sphere expression carries 10
objects and `var_cyl` with two cylinder expressions 14, against 12 and 18 from the rule —
so the rule is specific to block dimension expressions.

## Limits

- Only the six object shape is generated. A part with expressions carries 7 to 42
  objects depending on the feature, and those are not emitted. The block family's count
  is now known (`6 + 6n`) but the per object contents are not, so nothing is emitted for
  it yet.
- Section 0 still comes from the source part, so no part is written without a
  source document yet. It is document independent for a part without a body
  (fifteen bytes differ between two such parts, all path, base name and identity),
  but its 27032 byte class dictionary has to be derived rather than copied. Its
  body is now mapped as five regions (780 + 856 + 852 + 49 + 24495 bytes) that
  recompose byte for byte. All 214 records were blanked one at a time and loaded:
  only five one-byte records (112 to 116) are tolerated when invalid, so 209 of
  214 records must be emitted correctly. Truncating the graph to 4, 20 or 100
  records, and mutating a class identifier in the header, are also refused.
