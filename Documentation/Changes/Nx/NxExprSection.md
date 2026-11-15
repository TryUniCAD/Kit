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

## The order array only has to be a set

Mutation of `dim40`'s order array, each loaded in NX 2506:

```text
rotated by one                        loads   bodies 1  volume 23999.999999999996
replaced by 1..24 in sequence         loads   bodies 1  volume 23999.999999999996
reversed                              OPEN_FAILED
every entry set to 1                  OPEN_FAILED
```

So the array is validated as a **set of ids**, not as an order: rotating it is accepted and
so is the plain sequence `1..N`, while a reversal (which breaks the id-to-object pairing) and
a collision are not. A writer can therefore emit `1..N` and needs no identifier scheme.

That removes the last unknown in the expression section assembly.

## The order array carries ids, not indices

`dim40`'s section 2 carries 24 objects and an order array of 24 entries:

```text
[1, 3, 5, 4, 6, 7, 11, 22, 21, 20, 19, 18, 17, 25, 23, 13, 12, 28, 24, 27, 26, 8, 9, 10]
```

the values run to 28 for 24 objects, so they are object identifiers rather than indices, and
the identifier scheme is not decoded. A composer has to produce that array, which means one
more unknown beyond the layout: the id each object receives.

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

## The preamble is two functions of the object count

Comparing five fixtures, the first 24 bytes of the section middle are:

```text
part           objects  byte 7  objects-5  byte 8  ceil(objects/6)
empty.prt            6    0x01          1    0x01                1
empty_expr.prt       7    0x02          2    0x02                2
var_sph.prt         10    0x05          5    0x02                2
dim40.prt           24    0x13         19    0x04                4
var_two.prt         42    0x25         37    0x07                7
```

So `02 02 02 02 02 02 02`, then `objects - 5`, then `ceil(objects / 6)`, then the flag run,
then the four byte version pointer. The run is four bytes for the six object shape and seven
for every other, and the twenty-four and forty-two object shapes also carry a word at offset
48 (`0x55c` and `0x611`), which the eight and ten object shapes leave zero.

`ExprPreamble(Objects, Pointer, Extra)` emits it, and reproduces all five fixtures byte for
byte:

````text
empty.prt  empty_expr.prt  var_sph.prt  dim40.prt  var_two.prt   identical True
``` Both counts follow from the object count, which
`ExprObjectCount` already gives, so the preamble is generated rather than carried.

## The default group pair is constant, the group record is not

Two of the objects a dimension part adds are decoded:

```text
02 02 01 02 41 04 0f "Default Group" 00 04 0f "Default Group" 00   37 bytes
```

`ExprSection.GroupPair()` emits it, and it is identical in `dim40` and `var_two`, so it is a
constant rather than part data.

The following record is decoded as a transport, not as a selection. It opens
`00 3f 00 00 01 <n>` and then lists NUL-terminated values, each prefixed by a length byte
equal to the text length plus two; the count byte is the item count plus one. A record with
no items stops after `00 3f 00 00`:

```text
02 02 04 0f "Default Group" 00 00 3f 00 00 01 03 04 34 30 00 04 32 30 00
                                                        ^^ ^^^^^ ^^ ^^^^^
                                                        |  "40"  |  "20"
                                                        count    length 4 = 2 + 2
```

`ReadGroupValues` reads the list and `GroupRecord` writes it, reproducing all ten fixtures
byte for byte:

```text
empty_expr.prt  0 items            var_e4.prt     3 items  40, 20, 5
var_sph.prt     0 items            var_two.prt    3 items  40, 30, 20
var_cyl.prt     1 item   50        const_box60    2 items  40, 20
multi.prt       4 items  1 2 3 0.5 dim40          2 items  40, 20
var_named.prt   2 items  20, 40    var_formula    2 items  40, 20
```

What is still not decoded is **which** values appear and in what order. Two fixtures were
made for this question — a block whose middle dimension alone was edited (`var_mid`, `p1`
30 -> 11) and a block at different lengths (`var_big`, 100 x 50 x 25) — and both changed the
selection, which rules out a fixed positional rule:

```text
part      p0, p1, p2   value slots (decoded)   items written
dim40     40, 30, 20   40, 20, 30, 30, 40      40, 20             2 items
var_nmx   40, 30, 20   30, 30, 40, 20, 40      40, 20             2 items
var_named 40, 30, 20   20, 30, 40, 30, 40      20, 40             2 items
var_mid   40, 11, 20   40, 20, 11, 11, 40      40, 11, 20         3 items
var_big  100, 50, 25   50, 25, 100, 50, 100    50                 1 item
var_two   6 values     40,20,30,30,60,100,...  40, 30, 20         3 items
```

Four readings are now excluded:

- **positional** — `var_mid` lists all three where `dim40` lists two
- **all values** — `var_big` lists only `50`
- **value-order** — `var_nmx` and `dim40` hold the same values and names, and their value
  slots are arranged differently (`40,20,30,30,40` against `30,30,40,20,40`)
- **distinct slot values** — `var_mid` writes `11` while its slots hold `11` twice and `20`
  once, and `var_big` omits `100` and `25` which its slots do hold

Names do control the order when values agree (`var_named` reverses `dim40`), but the
selection itself moves with something internal to the model that value or name edits change
independently. So the group record's contents are model data that the writer cannot yet
compute, and `ExprMiddle` cannot emit this object for an authored part.

## The names lane is a hash-indexed slot map

The lane's frame is decoded; its slot placement is not:

```text
<exprs + 1>                                       head count
0f "EXP_lookup_exp" 11 "EXP_compare_exps"
10 "EXP_hash_string" 0d "EXP_hash_exp"            constant name block
01 21                                             split
<label map> 21                                    two byte tokens and 01 fill
<value map>                                       one byte per expression and ff fill
<exprs + 1> 21                                    terminator repeating the head count
```

The label map is a **slot map**, not a token run followed by fill: a slot holds one `01`
byte when empty and a token when occupied, and empty slots can precede occupied ones.
Observed token widths are two bytes (`8b xx`, `8c xx`), four (`c4 71 97 78`) and five
(`e0 66 05 90 fd`). The map's length is

```text
label map length = 32 + count + sum(len(token) - 2)
```

which holds on all seven fixtures — 36 for `dim40` (count 4, three two byte tokens), 36 for
`empty_expr` (count 2, one four byte token), 41 for `multi` (count 9, eight two byte tokens),
40 for `var_e4` (count 5, three two byte tokens and one five byte token). The value map is 31
slots holding one byte per expression with `ff` elsewhere.

Where each expression lands in those maps is hash-indexed, and that is visible directly:

```text
part             exprs  count  label map  value slots
empty_expr.prt       1      2         36  slot 24, four byte token at 24
var_sph.prt          1      2         34  slot 0
var_cyl.prt          2      3         35  slots 0, 1
multi.prt            8      9         41  slots 0, 1, 26..31
dim40.prt            3      4         36  slots 0, 1, 2
var_e4.prt           4      5         40  slots 0, 1, 2, 29
var_two.prt          6      7         39  slots 0..5
```

so the source's placement is a hash of the expression name and the token width varies with it.
Mutation showed the indices are free — `8c 00` to `8c 05` and swapping two both load — so a
writer may place its expressions from slot 0, which is what `var_two`, `dim40`, `var_cyl` and
`var_sph` already do. A lane emitter was attempted this turn and withdrawn: it assumed a dense
token run, so it read zero labels from `empty_expr` and could not round-trip it. Emitting the
lane needs the token-width rule as well as the frame arithmetic, and the width is not yet
derived.

## The emitter now builds its frame from the derived functions

`ExprMiddle` no longer hard codes its preamble and head tail; it calls `ExprPreamble` and
`ExprHeadTail`, so the six object shape is produced by the same functions the composer will
use. The write path is unchanged — payload identity, section 0 and section 2 differing-byte
counts are identical to before the refactor:

```text
part            section 0 differs  section 2 differs  payload identical
empty.prt                      342                  7              99.00%
multi.prt                      342                  6              99.02%
var_blank.prt                  343                  6              99.00%
const_box60.prt                346                  7              99.14%
dim40.prt                      346                  7              99.14%
```

## The writer composes the dimension shape

`RewriteMiddle` now runs for section 2 in `nx.author_sections`. It locates the middle by its
signature and table shape (a `02` heptad whose next byte is `objects - 5`, a table whose first
offset equals `start + 0x58 + 8n + 49`, and an order count equal to the object count), derives
`Dimensions = (objects - 6) / 6`, reads the lane, group items, slots and records from the source,
and rebuilds the middle with `ExprMiddleDim`. Six object shapes, and any section whose counts do
not fit, fall back to the previous slot rewrite.

Section 2 now differs from its source, for the first time:

```text
part             section 0 differs  section 2 differs  payload identical
empty.prt                      342                  7              99.00%
multi.prt                      342                  6              99.02%
var_blank.prt                  343                  6              99.00%
const_box60.prt                346                 48              99.05%
dim40.prt                      346                 48              99.05%
```

and every written part opens in NX 2506 with the expected geometry:

```text
rm_empty.prt bodies 0        rm_multi.prt bodies 0        rm_var_blank.prt bodies 0
rm_dim40.prt bodies 1  volume 23999.999999999996
rm_const_box60.prt bodies 1  volume 36000.0
rm_var_two.prt bodies 2  volume 48000.0
```

## The composed middle loads

The offset arithmetic of a dimension-shape middle is measured exactly on `dim40` and
`const_box60`:

```text
0x00..0x53   preamble: ExprPreamble(objects, pointer, extra) then zero padding to 0x54
0x54         object table, one absolute offset per object
+4n          order array, count then one id per object
+4+4n        version block, 49 bytes
then         the objects
```

`ExprSection.ExprMiddleDim(BaseOffset, Dimensions, Identity, Labels, Values, GroupItems,
Slots, Records, Extra)` composes a dimension shape from the shipped functions, and it
reproduces `dim40`'s middle exactly in **length** (1043 bytes) and in its **object table**,
differing only in the order-array ids and the occupancy map placement — the two fields mutation
showed to be free.

Spliced into the section with the pointer updated, both parts open in NX 2506 with the expected
geometry:

```text
cy_dim40.prt        bodies 1  volume 23999.999999999996
cy_const_box60.prt  bodies 1  volume 36000.0
```

An earlier attempt reported these as `OPEN_FAILED` and I recorded a "they do not compose"
conclusion for the order ids and the occupancy map. That was wrong: the cause was `Adopt`,
which located the middle as `pointer - 337` and so spliced at the wrong offset for a
1043-byte middle. `Adopt` now takes the middle length, and the earlier mutants (`ix_p_both`,
`ix_q_both_tail25`, `ix_r_rotdense`, `ix_t_both_tail52`) all load, which confirms the two
freedoms really do compose.

## The occupancy object depends only on the dimension count

The dimension shapes add an occupancy object the six object shape does not have. Dumping it
for every fixture:

```text
d = 0    absent (the six object shape uses a four byte lane instead)
d = 3    37 bytes  10 01 21 | ff ff ff | ids 43..51 | 10 21
d = 6    69 bytes  1f 01 41 | ids 43..60 | 22 41
```

`dim40` and `var_e4` carry **identical** objects even though one has a spare expression, so
the object is a function of the dimension count alone, not of the expression list. The opening
count is `5d + 1` (16 and 31) and the id range is `5d` long (15 and 30) in both, so two of the
three fields are derived. The closing count is 16 for `d = 3` but 34 for `d = 6`, which is not
the same function of `d`, and the marker byte differs (`21` against `41`), so the closing count
is not derived yet.

A third data point was obtained by committing **three** block features in one journal
(`var_d9.prt`, nine dimension expressions, 60 objects). Its occupancy object is 69 bytes, the
same length as `var_two`'s, and it settles the two open fields:

```text
part       d   objects  open  marker  close  ids  fe   map
dim40      3        24  0x10  0x21    0x10   15   0   32
var_two    6        42  0x1f  0x41    0x22   30   3   64
var_d9     9        60  0x2e  0x41    0x32   45   4   64
```

three relations now hold on all three parts, and the third was predicted before the fixture
was measured:

```text
open    = 5d + 1                     16, 31, 46
close   = 5d + count(fe) + 1         16, 34, 50   (predicted 50, measured 0x32 = 50)
marker  = map + 1                    33 = 0x21, 65 = 0x41, 65 = 0x41
map     = smallest power of two > 5d + 2     32, 64, 64
```

so the frame of the object is derived, and `ExprSection.OccupancyFrame(Dimensions,
Continuations)` plus `OccupancyMap(Dimensions)` emit it, matching the head and terminator of all
three parts:

```text
dim40    d 3  fe 0  map 32  head 10 01 21  end 10 21
var_two  d 6  fe 3  map 64  head 1f 01 41  end 22 41
var_d9   d 9  fe 4  map 64  head 2e 01 41  end 32 41
```

The map's **contents are free**, measured by mutation on `dim40` and `var_two`, each loaded in
NX 2506:

```text
map replaced by dense ids 43..51 then ff     bodies 1  volume 23999.999999999996
two ids swapped                              bodies 1  volume 23999.999999999996
whole map rotated by one byte                bodies 1  volume 23999.999999999996
a fe continuation moved to the map end       bodies 2  volume 48000.0
```

so a writer may place its ids densely from `0x43` with no continuations, and
`ExprOccupancy(Dimensions, Continuations)` does exactly that. Emitting it into four parts and
loading each:

```text
oc2_dim40        d 3  bodies 1  volume 23999.999999999996
oc2_const_box60  d 3  bodies 1  volume 36000.0
oc2_var_two      d 6  bodies 2  volume 48000.0
oc2_var_d9       d 9  bodies 3  volume 72000.0
```

What is **not** derived is where the `5d` ids land in
the map and where the `fe` bytes go: `var_two` writes `43 44 45 46 47 48 fe 49 fe 4a 4b 4c`
and `var_d9` writes four `fe` bytes at other positions, so the layout is hash-driven like the
names lane.

`ExprSection.ExprOccupancy(Dimensions)` returns the measured `d = 3` object,
byte identical on every fixture that has one, and raises for any other count rather than
extrapolating. That unblocks a three-dimension composer and nothing else.

## The names lane is emitted with writer-chosen slots

`ExprLane(Labels, Values)` and `ReadLane` now handle the slot map: a token's width comes from
its lead byte (`8b` and `8c` two bytes, `c4` four, `e0` five), empty slots are `01`, the map
runs `32 + count + sum(len(token) - 2)` bytes, the value map is 32 bytes, and the count byte
opens and closes the record. Re-emitting dense placement reproduces eight of eleven fixtures
byte for byte:

```text
identical     var_sph  var_cyl  dim40  var_mid  var_nmx  var_big  const_box60  var_two
not identical empty_expr (slot 24)   multi (slots 0,1,26..31)   var_e4 (slot 29)
```

The three that differ are the ones whose source places slots by the name hash, so byte
equality is the wrong test for them. Splitting uses the writer's own placement, so the test
that matters is an NX load, and all eleven lanes were spliced into their parts and opened:

```text
wl_empty_expr   bodies 0                     wl_multi        bodies 0
wl_var_sph      bodies 1  volume 523598.77    wl_var_cyl      bodies 1  volume 196349.54
wl_dim40        bodies 1  volume 24000.0      wl_var_mid      bodies 1  volume  8800.0
wl_var_nmx      bodies 1  volume 24000.0      wl_var_big      bodies 1  volume 125000.0
wl_const_box60  bodies 1  volume 36000.0      wl_var_e4       bodies 1  volume 24000.0
wl_var_two      bodies 2  volume 48000.0
```

so writer-chosen dense placement is accepted, including on the three parts whose source used
hash placement.

## The head tail is a function of the object and dimension counts

The head object ends in seven bytes that name the two ids following the last one used:

```text
part             objects  dims  tail
empty.prt            6      0   08 02 13 09 02 00 00
empty_expr.prt       7      0   09 02 13 0a 02 00 00
var_sph.prt         10      0   0c 02 13 0d 02 00 00
var_cyl.prt         14      0   10 02 13 11 02 00 00
multi.prt           14      0   10 02 13 11 02 00 00
dim40.prt           24      3   1d 02 13 1e 02 00 00
var_mid.prt         24      3   1d 02 13 1e 02 00 00
var_big.prt         24      3   1d 02 13 1e 02 00 00
const_box60.prt     24      3   1d 02 13 1e 02 00 00
var_e4.prt          25      3   1e 02 13 1f 02 00 00
var_two.prt         42      6   32 02 13 33 02 00 00
```

`ExprHeadTail(Objects, Dimensions)` emits `Objects + Dimensions + 2` and the next byte, and
reproduces all eleven records exactly, plus the fixed six-object middle, whose constant tail
is `ExprHeadTail(6, 0)`.

Mutation showed the pair is not reconciled at load — setting the ids to `objects+1`,
`objects+50`, and `1..N` together with an order array of `1..N` all load with bodies 1 and
volume unchanged:

```text
hd_next.prt       objects+1, objects+2       bodies 1  volume 23999.999999999996
hd_next_seq.prt   same ids, order 1..N       bodies 1  volume 23999.999999999996
hd_far.prt        objects+50, objects+51     bodies 1  volume 23999.999999999996
```

so the field is free as well as derived: the formula matches the source and any consistent
pair is accepted.

## The writer-chosen layout

`ExprSection.ExprLayout(Dimensions)` fixes the object order the writer will use, so the
composer does not have to reproduce the source's arrangement:

```text
d = 0        head descriptor names lane group record
d >= 1       head descriptor names occupancy group group-record
             then per dimension except the last: value plain plain value plain
             then the last dimension:              value plain plain plain plain
             then d records

d = 3  24 objects   5 value   10 plain   3 record
d = 6  42 objects  11 value   19 plain   6 record
````

`TestNxLayout` asserts the layout length and kind counts agree with `ExprObjectCount`,
`ValueSlotCount` and `PlainSlotCount` for one, two, three and six dimensions.
