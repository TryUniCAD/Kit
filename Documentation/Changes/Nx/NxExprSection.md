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

The count rule does not extend to the slot order. Measured slot by slot, value slots are
not grouped per expression:

```text
dim40   n=3   15 slots, value handles at positions 8, 11, 12, 13, 14
              6450 5450 5e50 5e50 6450
var_two n=6   30 slots, value handles at 11 of 30 positions
```

`dim40` has five value slots for three expressions and `var_two` ten for six, and the
positions are not the `n` value plus `4n` plain split the count suggests. The values appear
scattered, which matches the hash ordered arrangement measured earlier when renaming
expressions moved the handles between slots.

The three-dimension fixture's 135 byte names lane shows where the placement lives:

```text
04 0f EXP_lookup_exp 11 EXP_compare_exps 10 EXP_hash_string 0d EXP_hash_exp
01 21
8c 00 8c 01 8c 02           one token per expression, in order
01 x29
21
53 54 55                    three slot markers
ff x29
04 21
```

Mutation of those tokens, each loaded in NX 2506:

```text
8c 00 -> 8c 05                  loads
8c 00 and 8c 02 swapped         loads
53 54 55 third byte -> 56       OPEN_FAILED
53 54 55 first byte -> 44       loads
```

So the per-expression index tokens are free labels and the slot marker group is only partly
structural. That means **the placement is not validated**: a writer may order the objects
itself, as long as the lane's indices agree with the order it chose. Byte equality with
`dim40` therefore is not the right target for a composer — loading with the geometry intact
is. They are not decoded, and a composer needs
them, so the six fixed objects are emittable but the twenty-four object shape is not yet.

So a composer can be written for the six fixed objects but not yet for the slots: their
order follows the expression name hash, and that hash is not derived.

That was confirmed without a new fixture, by renaming the three dimensions in an existing
part (`var_named.prt` is `dim40.prt` with `p0`, `p1`, `p2` renamed to `length`, `width`,
`height`) and comparing the value word positions:

```text
dim40        ---- ---- ---- ---- ---- ---- ---- ---- 6450 ---- ---- 5450 5e50 5e50 6450
var_named    5450 5e50 ---- 6450 ---- ---- ---- ---- 5e50 ---- ---- ---- 6450 ---- ----
values unchanged (40.0, 30.0, 20.0) but positions moved
```

The same values sit in different slots after a rename, so the arrangement follows the
**name**, not the value.

A further measurement separates the two candidates:

```text
dim40        p0=40 p1=30 p2=20   ---- ---- ---- ---- ---- ---- ---- ---- 5064 ---- ---- 5054 505e 505e 5064
dim50        p0=50 p1=30 p2=20   ---- ---- ---- ---- ---- ---- ---- ---- 5069 ---- ---- 5054 505e 505e 5069
dim60        p0=60 p1=30 p2=20   ---- ---- ---- ---- ---- ---- ---- ---- 506e ---- ---- 5054 505e 505e 506e
var_formula  p0=40 p1=20 p2=20   5054 5054 ---- 5064 ---- ---- ---- ---- 5054 ---- ---- ---- 5064 ---- ----
```

`dim40`, `dim50` and `dim60` share names and differ in `p0`'s value, and their positions are
identical. `var_formula` shares the same three names but has `p1 = p0/2`, so `p1` and `p2`
hold the same value, and its positions are completely different. So placement is not a
function of the name alone, and not of the value alone: it changes when two expressions
come to hold equal values, which is what the five slots for three expressions keeps
pointing at.

The count itself follows `2n - 1` on both large fixtures:

```text
dim40     n=3   15 slots   5 value slots   2*3-1 = 5
var_two   n=6   30 slots  11 value slots   2*6-1 = 11
```

with the remainder being plain slots, `3n + 1` of them (`10` for `dim40`, `19` for
`var_two`). A third fixture settles what `n` counts. `var_e4.prt` is a block plus one spare expression
(4 expressions, 3 dimensions):

```text
var_e4   objects 25   slots 15   value slots 5   positions 8, 11, 12, 13, 14
```

`6 + 6n` would predict 30 objects and `2n - 1` would predict 7 value slots; the measured
figures are 25 and 5. So the rules count **driving dimensions**, not expressions:

```text
objects      6 + 6d      d dimensions    3 -> 24, 6 -> 42
value slots  2d - 1                       3 -> 5,  6 -> 11
plain slots  3d + 1                       3 -> 10, 6 -> 19
```

and a spare expression that drives nothing adds a single object rather than six. The value
slot positions are also identical across every 3-dimension part measured: `dim40`,
`dim50`, `dim60`, `const_box60` and `var_e4` all place them at 8, 11, 12, 13 and 14.

`dim40` already refutes value sharing as the explanation for the count: its three
dimensions are all distinct (`40`, `30`, `20`) and it still carries five value slots, holding

```text
505e 30.0    505e 30.0
5054 20.0    5064 40.0    5064 40.0
```

so the duplicates are `40` twice and `30` twice while all three expressions hold different
numbers. Whatever produces five slots for three expressions, it is not two expressions
sharing one value — `var_formula` (where `p1` and `p2` are both 20) was the only case where
that reading fitted, and it does not fit the fixture with distinct values.

Standard hashes were tested against the measured positions and none reproduces them:

```text
occupied slot positions   dim40 {8, 11, 12, 13, 14}   var_named {0, 1, 3, 8, 13}
candidates                xxh32, crc32, fnv32, md5, sha1
moduli                    13, 15 and 16
result                    no candidate matches either set
```

Note also that three expressions occupy **five** slots, so the placement is not one bucket
per name either way. `ExprObjectCount(6 + 6n)` fixes how many slots exist but not where
they go, and reproducing the placement needs the name hash the kernel uses.

Other feature families do not obey it — `var_sph` with one sphere expression carries 10
objects and `var_cyl` with two cylinder expressions 14, against 12 and 18 from the rule —
so the rule is specific to block dimension expressions.

## The six fixed objects of a three dimension part

Diffing `dim40` against `dim50` — same names, one value different — isolates what is
constant in the fixed objects:

```text
obj 0  head          27/26 bytes   identity and header differ
obj 1  descriptor    26 bytes      identical
obj 2  names lane   135 bytes      identical
obj 3  occupancy     37 bytes      identical
obj 4  group         37 bytes      identical
obj 5  group record  32 bytes      one byte differs: the text of the first dimension,
                                   34 -> 35, "40" -> "50"
```

so for a three dimension part the names lane, occupancy and both group objects do not depend
on the dimension values at all, and the group record carries the values as text tokens
(`04 34 30 00` is `"40"`). That is what a composer has to emit: four constant objects,
one head with the part identity, and one record whose text follows the values.

## Inventory functions

`ExprSection` now carries the measured counts as functions, so the composer has a
definition to build against rather than a note:

```text
ExprObjectCount(d) = 6 + 6d      3 -> 24   6 -> 42
ValueSlotCount(d)  = 2d - 1      3 ->  5   6 -> 11
PlainSlotCount(d)  = 3d + 1      3 -> 10   6 -> 19
```

and the identity `ExprObjectCount(d) == 6 + ValueSlotCount(d) + PlainSlotCount(d) + d`
holds, which is the object budget the composer must fill: six fixed objects, the value
slots, the plain slots and one record per dimension.

## Why a composer would not move provenance

The composer is specified, but composing it from the values the part already holds produces
byte-identical output: the slots carry the same handles, the records the same text, the
fixed objects the same constants. A rewrite of section 2 in place therefore cannot raise the
generated byte count in the way section 0's passes did.

Provenance in section 2 can only change by writing _different_ expressions, which is the
same thing as authoring a new part rather than rewriting one — and that is the neutral
document path `WriteNx` refuses because the class table cannot be produced.

So the composer's value is not provenance: it is that an authored part would have a real
expression section. It is worth building for that reason, and it is not a way around the
class table.

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
