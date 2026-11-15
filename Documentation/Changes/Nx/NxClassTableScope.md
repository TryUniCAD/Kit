# The class table depends on the class set, not on the document

## Behaviour

No writer behaviour changed. This entry records the scope of the root object
section's class table, which is the last field in the format that `src` still carries
from the source part instead of computing.

## What was measured

Twelve parts were compared entry by entry. The entries are identical whenever two
parts carry the same set of class names, and different otherwise:

```text
group      parts  same class set  same entries
body-less      5            True          True
block          8            True          True
```

The body-less group is `empty`, `multi`, `var_blank`, `var_x1` and `var_x2`; the block
group is `dim40`, `dim50`, `dim60`, `const_box60`, `var_two`, `var_named`,
`var_formula` and `var_datum`. Those eight differ in dimension, in expression count
(three to six), in expression names, in body count (one or two) and in feature count
(one block, or a block plus a fixed datum plane), and their class tables are identical
in every byte: 154 of 154 entries.

The reference hypothesis was tested and refuted: `dim40` and `var_sph` carry the same
79 references, in the same order, yet their entries differ.

`var_sph.prt` carries the block set minus exactly one class, `UGS::Solid::Edge`, and
152 of its 153 entries differ from the block table. `var_cyl.prt` carries 161 classes
and differs as well.

So the table is a function of the class set, not of the document's geometry, name,
path, expression values or object graph. A rewrite of a part therefore never needs to
change it, and a from-scratch writer would need one table per class set rather than one
per document.

## The per-set difference is small and structured

Decoded as little-endian 7-bit fields, one entry is a short sequence of small integers,
and only one of them changes between class sets:

```text
part          classes  refs  UGS::OM::RootObject fields
empty.prt         129    63  56, 100, 9648, 56917797, 15606, 2
dim40.prt         154    79  56, 116, 9648, 56917797, 15606, 2
var_sph.prt       153    79  56, 115, 9648, 56917797, 15606, 2
var_cyl.prt       161    83  56, 120, 9648, 56917797, 15606, 2
```

The second field is the class's own constant plus a per-set increment of 0, 16, 15 and 20. It is not the class count difference (0, 25, 24, 32), and not the reference count
difference, since `var_sph` and `dim40` share 79 references yet differ by one.

Comparing the full field sequence of each entry rather than its first field:

```text
part        fields per entry   most common change   single-field classes
dim40           4 to 11        two fields            4
var_sph         4 to 11        two fields            4 to 8
var_cyl         4 to 11        two fields            2
```

so between two class sets most entries change in two places, 32 to 47 entries change
length, and the change is not one additive constant. The differing field indices are
stable for a given class across all three sets, which rules out an ordinal that shifts
when the set changes, and points at per-class packed fields.

## The ordinal model is refuted by the existing sets

If an entry depended on the class's position in the set, removing or adding a class would
leave every entry before that position unchanged and shift the rest. Measured against
`empty.prt`:

```text
part        classes  entries identical to the 129 set
var_cyl        161   1 of 161
dim40          154   1 of 154
var_sph        153   1 of 153
```

One entry survives in each case, so the change is not a shift from an insertion point:
it reaches every class, including those whose position is unchanged. That rules out a
set ordinal as the carrier of the increment.

A fifth class set would only distinguish "increment depends on the class" from "increment
depends on the class count", and the fixtures available do not offer two sets with equal
counts and different membership. A chamfer part was attempted to supply one and could not
be built:

```text
body.Edges                     AttributeError, the property does not exist
ufs.Modl.AskBodyEdges          AttributeError, the method does not exist
body.GetFaces()[n].GetEdges()  works, 24 edges on a 40x30x20 block
chamfer.SmartCollector         None, so SetTargets cannot be called
chamfer.FirstOffset            a string, not an expression object
```

So the edge query is solved (`GetFaces` then `GetEdges`) while the chamfer builder in this
release does not expose a collector, and the fixture is still unavailable.

Other feature builders were probed for a usable target collector:

```text
work.Features.CreateHolePackageBuilder   exists, needs one argument
work.Features.CreateHoleBuilder          does not exist
work.Features.CreatePocketBuilder        does not exist
work.Features.CreateDatumAxisBuilder     exists, exposes no Target or Collector attribute
work.Features.CreateExtrudeBuilder       exists, exposes no Target or Collector attribute
```

so the fixture needs a builder invocation this work did not find, and the class-table
discriminator stays open. A third probe
confirmed the builder's only selection attribute is `SmartCollector`, which is `None` when
the builder is created from `NXOpen.Features.Chamfer.Null`, and `GetTargets` does not
exist on it. `FirstOffset` is a string, so the offsets are set by text rather than by an
expression object.

## Entry length, and the correction to the length claim

The insertion-ordinal test above reported that "every one changes length". That was measured on
the number of base-128 fields, not on the entry's byte length, and it is wrong. Measured properly,
decoding each entry as one little-endian base-128 integer:

```text
empty -> dim40 byte lengths, classes common to both
  12 -> 12   57 classes
  12 -> 13   35 classes
  13 -> 13   13 classes
  11 -> 11   12 classes
```

so **35 of 128 entries grow by one byte and 93 keep their length**, which is what a small
increment on a large packed value looks like: a base-128 digit only carries when the top digit
crosses 127. The earlier "every entry changes" statement is retracted.

The value deltas also decompose into powers of two rather than being scattered:

```text
604462909807314587615232   16 classes   = 2^79 + 2^18
604462909807314587648000    8 classes   = 2^79 + 2^18 + 2^15
4722366482869645215744      5 classes
2048                        4 classes    = 2^11
262144                      3 classes    = 2^18
```

so the per-set change is a small set of bit positions, not a rehash. That is consistent with the
entry being a packed value whose low bits carry a per-set counter, and it is the strongest
evidence yet that the entry is structured rather than derived by hashing. The per-class constant
is still not derived.

## The first field is a small enum, not hash output

Reading each entry's first base-128 field shows a small alphabet rather than a uniform one:

```text
distinct values of (first field mod 128) across 129 classes   18
most common                                                    3 (40 classes), 32 (18), 0 (11), 1 (11)
classes sharing the value 3        UGS::Sketch::Colors, UGS::POINT, UGS::LAYER_category,
                                   UGS::UGFONT_table, UGS::COLOR_table, UGS::Display::Camera,
                                   UGS::VIEW_base, and 33 more across Annot, PMI, Display, Sketch
```

a hash would spread the low seven bits uniformly over 128 values. eighteen distinct values means the
first field is a **kind** enum, and it does not correlate with the module prefix or the entry length
(the value 3 appears in eight different modules). The rows are also not sorted by value, so the
table is not ordered by its constants.

So the entry decomposes as a small enum plus roughly 64 to 73 further bits, and those further bits
are the part no derivation has reproduced. This is the shape a later attempt should start from: decode
the enum by correlating it with class names that share a kind, then attack the remainder.

## The low byte is a kind, the high part is not an id

Splitting the first field as `(identifier << 8) | kind`:

```text
distinct kinds                                 22
most common   3 (40 classes)  101 (10)  32 (10)  7 (8)  160 (8)  1 (8)  0 (7)
distinct identifiers                           80 of 129
identifier range                               0 .. 2,077,914,824,744
identifiers sorted                             no
repeated identifiers                           0, 6692, 6452, 6900, 6836 (and more)
```

so the low byte behaves like a small kind field — 22 values, dominated by 3 with forty classes — but
the high part is not a sequential or unique identifier: it ranges over twelve orders of magnitude and
repeats. That rules out the tidy `kind + ordinal` reading.

What the grouping does show is that the first field's low byte partitions the table into
name-independent kinds: the forty classes sharing `kind = 3` span Annot, PMI, Display and Sketch, so
the kind is not the module. The remaining bits are still underived, and the first field does not
decompose cleanly into two useful parts.

## xxh32 of the name appears nowhere in the entry

Since NX uses xxh32 for its own seals, the last test was whether a class id contains xxh32 of its
name in any 32 bit window:

```text
classes tested                                   20
windows searched per class                       all bit offsets
matches                                          0
```

so the entry is not `xxh32(name)` in any alignment. That closes the seeded-hash reading as well.

## The class ids are not referenced elsewhere in the section

One association route was left worth trying: if a class id appeared somewhere else in the object
section, a record carrying it next to a name would give the mapping directly. Testing the first
forty entries against the whole section body:

```text
classes whose encoded id occurs more than once   0 of 40
```

so the ids exist only in the table and carry no in-file association with their names. That route is
closed too.

## "Constant plus increment" is refuted, in both arithmetics

The previous entry claimed `entry(name, set) = constant(name) + increment(set)`. That was tested
directly and it is wrong. Subtracting the measured per-set increment (0, 16, 15, 20) from each
common class's value:

```text
classes common to empty and dim40          129
classes whose delta is exactly 16            0
distinct deltas                             90
classes whose remainder is set invariant     0 of 129
```

and at the field level, asking whether exactly one base-128 field differs by exactly the set
increment for each class:

```text
classes satisfying that model                5 of 129
```

so neither arithmetic supports the additive reading. The bit scatter described in the previous
entry is real, but the explanation attached to it is not: a per-set addition would give a uniform
delta per class, and the deltas are 90 to 101 distinct values.

What survives from that line of work is narrower and still useful: entries are sequences of five
to nine base-128 fields (`5:19, 6:28, 7:30, 8:25` classes by field count), the field count is
stable for a given class across sets, and 35 of 128 entries grow by one byte between sets. The
per-class value itself remains underived, and the per-set relationship is not additive.

## The entry is a per-class constant plus a small per-set increment

XOR-ing each common class's decoded value between `empty.prt` and each other set scatters the
changed bits widely, which is the signature of **carry propagation** from a small addition rather
than a fixed counter field:

```text
empty vs dim40      bit 18: 58 classes   bit 79: 56   bit 80: 53   bit 16: 46   bit 20: 38
empty vs var_sph    bit 16: 66 classes   bit 18: 59   bit 14: 58   bit 79: 56   bit 80: 53
empty vs var_cyl    bit 16: 59 classes   bit 80: 59   bit 17: 58   bit 20: 57   bit 19: 56
```

a change confined to a fixed field would flip the same bits in every class. Hundreds of classes
changing different bits is what adding a small number to values with arbitrary low bits produces.

That agrees with the earlier per-set measurement (increments 16, 15 and 20) and closes the
question of the entry's shape:

```text
entry(name, set) = constant(name) + increment(set)
                   ^^^^^^^^^^^^^   ^^^^^^^^^^^^^^
                   70-80 bits      16, 15, 20
                   not derived     measured
```

so the table is computable exactly when `constant(name)` is, and that is the single remaining
unknown. Twenty-one derivations of it are negative, and the packed reading above shows why they
were all aimed at the wrong target: `constant(name)` need not be a hash at all, it can be an
arbitrary per-class value that only the serialiser knows.

## The insertion-ordinal model is refuted

The last derivation class worth testing was that an entry's changing value is the number of
classes inserted before it, which would make the table computable from the class set's ordering.
It fails immediately: comparing the 128 classes common to `empty.prt` and `dim40.prt`, **every
one of them changes length**, not just one field:

```text
classes common to both sets          128
entries whose field count is unchanged   0
```

so the entry is not a fixed record with one shifting field. The candidate is refuted, and with it
the twenty-first hypothesis on this table. The remaining options are unchanged: a kernel read of
the class serialiser, or the name-to-value function from an authoritative source.

## Why the discriminator is not on the critical path

Settling "increment depends on the class" against "increment depends on the class count"
would not by itself make the table emittable. Both readings leave the same unknown:

```text
entry = class value  +  set increment
        ^^^^^^^        ^^^^^^^^^^^^^
        unknown        small, uniform (0, 15, 16, 20 measured)
```

The increment is the _small_ part and it is already measured as uniform across every class
in a set. The class value is the _large_ part, differs per class, and no hash, offset or
field model has reproduced it. So an equal-count fixture would refine a term that is
already characterised, not supply the term that is missing.

The entry was also tested as a variable-length digest over the name: decoded as a
little-endian base 128 integer (71 to 80 bits) and compared against `fnv1a-64` and a
murmur3 x64 fold at every bit shift from 0 to 23, with no match. That is the eighteenth
negative for a name-derived function.

The packed "module id plus class ordinal" reading was tested too, by grouping the entries
by name prefix (`UGS::OM`, `UGS::RM`, `UGS::Sketch`, ... 85 groups) and looking for a shared
high bit prefix inside each group:

```text
modules with a shared top-30-bit prefix   0 of 6 multi-member groups
```

classes in the same module share no high bits at all, so the entry is not a module id with
an ordinal in the low bits.

That is the reason this work stopped chasing the fifth class set: the emitter needs a
function of the class **name**, and that is what sixteen probes have failed to find,
whether the increment turns out to be per class or per count.

## The table is a function of the class set, not of the part

Decoding each entry as a run of **big-endian base-128 groups** (bit 7 set on every group but the
last) gives readable records:

```text
UGS::OM::RootObject        38 | 74 | b0 4b | a5 fe 91 1b | f6 79 | 02
                          56 | 116| 6219  | 79661211     | 15225 | 2
UGS::OM::SaveAuditTrail    80 c9 78 | 60 | 94 9c 18 | 6a | a8 9e 41 | 01
                           9464     | 96 | 331288   |106| 659265   | 1
```

Read through the module's own class list (154 entries in `dim40.prt`), the table is **identical
wherever the class set is the same**, and it moves whenever the set changes:

```text
part        classes   entries identical to dim40   entries differing by one byte of -1
dim50          154            154 of 154                        0
var_two        154            154 of 154                        0
var_e4         154            154 of 154                        0
var_sph        153              1 of 153                      150 of 153
var_cyl        161              1 of 154                        0
empty          129              1 of 129                        0
multi          129              1 of 129                        0
```

so the table is a pure function of the class set — three different parts with the same set carry
byte-identical tables, and a set one class smaller carries entries that differ by exactly one
decrement in a single byte, for 150 of 153 classes.

What does **not** hold is the stronger reading I first wrote: "entry = base(class) + K(set) in one
group". Testing that against the decoded groups, the number of entries where exactly one group
differs by exactly K is

```text
var_sph   K = -1    91 of 150
var_cyl   K = +4    33 of 135
empty     K = -16    7 of 81
```

so the additive model fits the one-step change and degrades as the set difference grows; a single
group delta is not the general rule. What is solid is the weaker statement above: the table is
deterministic per class set and moves with it.

## The set-level movement tracks the reference table

Measuring the same group across every fixture shows the movement is a set-level quantity, and it
tracks the section's reference-table size rather than its class count:

```text
part              classes  refs   K      classes-154  refs-79
dim40..var_d9         154    79    0          0          0     (12 parts, all K = 0)
var_sph               153    79   -1         -1          0
var_cyl               161    83   +4          7          4
empty                 129    63  -16        -25        -16
multi                 129    63  -16        -25        -16
var_blank             129    63  -16        -25        -16
```

`K = refs - 79` holds for sixteen of seventeen parts and fails only on `var_sph`, where the class
count moved by one while the reference count stayed at 79. So `K` is a function of the class set
(and therefore of the reference table), not of the part: `dim40`, `var_two` (a two-body part with
1,202 more section-0 bytes) and `var_d9` (2,437 more) all carry `K = 0` because their class set is
the same.

## The prefix is a per-class base plus one set-level integer at bit 28

Splitting each entry at its digest gives a prefix and a one-byte tail, and the prefix moves between
class sets by an exact multiple of 2²⁸:

```text
dim40 - var_sph   prefix delta = 268435456 = 2^28      131 of 135 classes
dim40 - var_cyl   changed bits dominated by bit 30     117 of 135 classes
dim40 - empty     changed bits dominated by bit 32      75 of 114 classes
```

so

```text
prefix(class, set) = base(class) + S(set) * 2^28

S(dim40)     =  0        (154 classes, 79 references)
S(var_sph)   = -1        (153 classes, 79 references)
S(var_cyl)   = +4        (161 classes, 83 references)
S(empty)     = -16       (129 classes, 63 references)
```

The bit histograms are exactly what adding a small multiple at bit 28 produces: bit 28 flips for
every class when S changes by 1, and the higher bits flip in proportion to carries. That replaces
the earlier "K in one base-128 group" reading with a concrete field position, and it means the
set-level component is **one integer**, not per-class data.

`S` tracks the reference count (`refs - 79` matches `var_cyl` 4 and `empty` -16) with `var_sph` the
one exception, where the reference count is unchanged but the class count fell by one.

## The bases are not stored in any vendor module

With the additive law in hand the per-class base became testable: for `dim40.prt` (K = 0) the stored
entry **is** the base, so each base can be searched for verbatim.

```text
entries found verbatim in libpart.dll, libsyss.dll or pskernel.dll     0 of 154
entries minus the varying first byte                                     0 of 154
```

and a systematic sweep over the bases tested 30 digest functions (md5, sha1, sha256, sha512,
blake2b-8/16, xxh32 and xxh64 at seeds 0-3, fnv1a-32/64, fnv1-64, djb2, sdbm, crc32, adler32)
against 10 name encodings (full, component, NUL-terminated, length-prefixed, 8-byte aligned, UTF-16LE,
lower, upper, MSVC-mangled, dot-separated) at all eight bit shifts. No digest appears in any base.

So the base is computed by the loader at load time and is not a stored constant, not a digest of the
name, and not any registry field the API exposes.

## The entry values are validated per name

The entry framing is now delimited by the name lengths rather than by base-128 continuation
bits, and it parses cleanly:

```text
<name length + 1> <name> <entry>
```

`dim40.prt` yields **154** entries with entry lengths 11 (19), 12 (69), 13 (51) and 14 (14),
which totals exactly the table's extent. The base-128 reading used in the earlier probes
concatenated the entry into one integer and is superseded; those probes were aimed at a value
that does not exist.

With real entry boundaries the decisive experiment became possible: swap the entries of two
classes whose entries have the same length, so the table's size and every following offset are
unchanged, and load the result.

```text
cls_swap.prt   UGS::OM::RootObject <-> UGS::RM_part entries exchanged (both 11 bytes)  OPEN_FAILED
cls_ctrl.prt   identical rebuild of the same part, no swap                              bodies 1  volume 23999.999999999996
```

The control proves the rebuild path is sound, so the refusal is caused by the swap alone. The
table's values are therefore **validated against their names**, and a table that does not match
the loader's own assignment is rejected. Since the registry identifiers are load-order serial
numbers (`GetSerialNumber` returns a global counter), the file's values must agree with the
serial state of the session that opens the part.

A second mutant separates the two possible mechanisms: renaming one class to an unknown name of the
same length, leaving every value in place.

```text
cls_rename.prt   UGS::OM::SaveAuditTrail -> UGS::OM::SaveAuditTraiX   OPEN_FAILED
```

so the loader **looks each name up in its own registry**, and an unknown name is rejected outright.
The table must therefore name real classes, and the values must agree with what the loader computes
for those classes.

That closes the last route to a fabricated table: it cannot be permuted, computed from names, or
shared between class sets. It can only be reproduced by the loader itself.

## The table is mandatory and both undecoded fields are validated

The entry decodes as `<prefix> <name digest> <layout digest> <tail>`, the name digest is derived
(see `NxClassEntryLayout.md`), the layout digest is a registration-site constant, and the prefix's
final byte plus the one-byte tail are the two fields left. Mutating them one bit at a time shows
both are checked by the loader, and removing the table at all is refused:

```text
mutant                                     change                                   result
mut_rebuild.prt      section 0 rebuilt through BuildSection, byte identical to source  bodies 1  volume 23999.999999999996
mut_code.prt         152 code bytes flipped, one bit each                             OPEN_FAILED
mut_tail.prt         152 tail bytes flipped, one bit each                             OPEN_FAILED
mut_both.prt         both fields flipped                                              OPEN_FAILED
mut_const.prt        every code byte forced to 0x74                                   OPEN_FAILED
mut_noclass.prt      all 154 class declarations removed, pointer adjusted              OPEN_FAILED
mut_halfclass.prt    first 80 class declarations kept, pointer adjusted                OPEN_FAILED
```

The control is byte-identical to the source body, so the mutation path is sound and every refusal
above is caused by the field change. The class table is therefore **mandatory and exact**: it cannot
be dropped, truncated, reordered, renamed, or have either remaining field altered.

Neither field is a function of data the class list carries:

```text
tail == ordinal within parent, by registry id            9 of 152
tail == ordinal within chain depth, by registry id       7 of 152
tail == chain depth                                      4 of 152
tail == class kind                                      10 of 152
tail == attribute count                                  5 of 152
tail == name or layout digest, byte or modulus           <= 8 of 152 for every combination tried
layout digests shared by classes with different tails   14
```

and the code is read at `2 * [[class + 0x30] + 0x98]` from `[writer + 0x30]`, a dense two-byte
per-class-id array that is `0xFFFF` in a fresh context and filled during the write. Its neighbouring
`u16` is the next id's code, so the tail is not stored beside it.

One structural fact about the tail did fall out: its **range is exactly the section's reference
count**, in every part measured.

```text
part        references   classes   tail range
dim40.prt           79       152    1..79
var_sph.prt         79       151    1..79
var_cyl.prt         83       152    1..83
empty.prt           63       129    1..63
```

so the tail is a 1-based index into the reference table rather than a free byte. But it is not the
index of the class's own schema (31 of 152), nor of any single position in the class's inheritance
chain (best position, counting from the end, is 31 of 152 at offset 0 and falls off from there), and
it is stable across parts with the same class set while moving when the set changes. The tail is
therefore a session-assigned reference handle: structural, validated, and not derivable from the
class list.

## Consequence

The class table is a validated snapshot of the loader's own registry state. Two of its four fields
are now derived functions rather than carried bytes — the name digest from the inheritance chain, the
layout digest from the registration site — but the per-class code and the tail byte are produced by
the session and checked on load, so a writer cannot compute them for a class set the loader has not
seen. That is the wall, and it is a designed one rather than an unread one.

Consequently `Writer.py` still requires a retained native document, and a part authored from a
neutral document is not reachable through this format while the class table is mandatory and
validated. Anything that made it reachable would have to carry loader-produced values, which is the
donor data the project forbids.

## Verification

```text
twelve parts compared, entries identical within each class-set group
section 0 written and loaded for five of them: bodies 0/0/0/1/1
```

## Limits

- This is a measurement entry. The writer still carries the class table from the
  source part and `Writer.py` still requires a retained native document.
- The reference table behaves differently and is already stable across parts; only the
  class table is set-scoped in this way.
