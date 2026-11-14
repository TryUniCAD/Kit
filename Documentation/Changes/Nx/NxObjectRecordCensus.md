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
