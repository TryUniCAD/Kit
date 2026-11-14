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
counts and different membership. A chamfer part was attempted to supply one and the
journal failed before saving (`NXOpen.Body` exposes no `Edges` attribute, and the chamfer
builder needs an edge rule), so that comparison is not available yet.

## Consequence

The class table cannot yet be computed: the increment is uniform and small, but the
class constants and the offset rule are not derived, and no hash of the class name
reproduces an entry. It is now known to be a per-class-set constant table rather than
per-document data, which is what makes it cacheable and what would make a name to entry
table sufficient if one were derivable.

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
