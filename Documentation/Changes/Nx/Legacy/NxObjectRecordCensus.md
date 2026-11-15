# The root object section's record dictionary is measured

## Behaviour

No writer behaviour changed. The root object section was censused so the remaining
work is specified rather than estimated: every record was classified by length and
first four bytes, and whole record groups were regenerated to see which accept
generated content.

## What was measured

The three body-less fixtures carry the same dictionary:

```text
part            records  distinct shapes
empty.prt           214              116
multi.prt           214              116
var_blank.prt       214              116
```

The commonest shapes are `01 02 04 0b` at 21 bytes (18 of them), `01 02 04 03` at 13
bytes (13), `01 02 04 05` at 20 bytes (8), `03 11 03 01` at 46 bytes (8), and
`02 02 41 4d` at 27 and 34 bytes (5 each), so the section is a handful of families
rather than 214 unrelated blobs.

Regenerating a group at a time:

```text
trailing 00 01 00 zeroed in 18 records                     loads
12 byte id region after 02 02 ?? 4d zeroed in 14 records   OPEN_FAILED
same region with a position derived sequence               OPEN_FAILED
```

## Class identifiers

The per-document change in the class table was tested as a counter offset on a fixed
base per class name, and it is not one:

```text
128 of 129 shared classes differ between empty.prt and dim40.prt
no constant offset explains them, searched up to 4096
47 of the 129 entries grow by one byte     11->12, 12->13 and 13->14
differing digits are split: bytes 1 to 3 and bytes 10 to 12
```

so the entry packs two fields and one of them moves with the document. Further
measurement shows the scope is the class set rather than the document: seven parts that
differ in dimension, expression count, expression names and body count share one class
table byte for byte, and a part missing one class differs in 152 of 153 entries. See
[the class table change](NxClassTableScope.md).

## The `5f 01 04 01` family

Twelve records in `dim40.prt` share the frame `02 02 ff 00 5f 01 04 01`, spanning 10 to
4374 bytes:

```text
10     02 02 ff 00 5f 01 04 01 00 01
14     02 02 ff 00 5f 01 04 01 00 00 00 00 00 01
17     02 02 ff 00 5f 01 04 01 80 e4 ff 83 e8 83 e8 00 00
78 90 91 255 489 500 976 1353 4374   the remaining nine
```

The three small members end with `01` and carry runs of zeros, so they read as a count or a
flag with padding rather than as a token lane: the 17 byte member mixes two-byte tokens
(`80 e4`, `83 e8` twice) with a single `ff` and two zeros, which no single token walk
consumes. The largest member is 4374 bytes of mixed content.

So this family is not one grammar. It needs to be split into a small numeric shape and a
large mixed shape before any of it can be re-emitted, and that work is not started.

## What is left is a long tail, not a few families

Censusing by frame and length after the twelve decoded families:

```text
empty.prt  214 records  116 distinct frames+lengths
dim40.prt  250 records  146 distinct frames+lengths

commonest remaining frames are all decoded families
  01 02 04 x18 len 21   attribute        03 11 03 01 x8 len 46   pair
  01 02 04 x13 len 13   attribute        02 02 41 4d x5 len 34   instance
  01 02 04 x8  len 20   attribute        02 02 41 00 x4 len 14   slot family
```

The ten largest remaining shapes are `5f 01 04 01`, from 78 to 4374 bytes, and each is a
single record. Beyond them, 116 to 146 distinct frames for 214 to 250 records means most
remaining fus are one or two records apiece with their own layout.

So the section is now decoded where it was regular and the remainder is a long tail of
unique records. Reaching them means one grammar per record rather than one per family,
which is why the generated share has stopped rising even though the work continues.

## The 42 00 family is validated, so it stays carried

Three 26 byte records in a body part share a frame and differ in exactly two bytes:

```text
02 02 42 00 47 03 04 01 c0 44 04 00 c0 7f ff 02 09 [17] 93 8c 16 [21] ff ff 90 fe
record 1   17 = 0x25   21 = 0x3f
record 2   17 = 0x0a   21 = 0x3d
record 3   17 = 0x03   21 = 0x3c
```

Mutating each, one at a time, in NX 2506:

```text
byte 17 -> 0x30 in the first record     loads       bodies 1  volume 23999.999999999996
byte 21 -> 0x30 in the first record     OPEN_FAILED
byte 17 and 21                         OPEN_FAILED
byte 17 and 21 in all three records    OPEN_FAILED
```

so byte 17 is a free label and **byte 21 is validated**: it survives being rewitten only if the
value stays consistent with something else in the part, and the three source values are 63, 61
and 60 for three records. That makes this family the first one where a field is not free, and it
means the record cannot be re-emitted from a writer-chosen value pair without knowing what byte
21 must equal. It stays carried.

That corrects the trend I described in the previous entry: not every remaining family is
relabellable, and the count of generated section-0 bytes cannot be raised by working through the
census in order.

## Consequence

The trailing words are free, but the id regions are coupling: a single byte can
change and the part loads, while replacing the group does not. Emitting section 0
therefore needs an id allocator across the dictionary, which is the outstanding work
and the reason `nx.author_sections` still keeps those records from the source.

## Verification

```text
g_tail.prt      trailing words zeroed, 18 records   part units 1  bodies 0
g2_zero.prt     id region zeroed, 14 records        OPEN_FAILED
g2_seq.prt      id region generated, 14 records     OPEN_FAILED
objB_*.prt      five fixtures written and loaded    bodies 0/0/0/1/1
```
