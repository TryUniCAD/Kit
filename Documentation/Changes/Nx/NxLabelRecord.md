# Three small families emit a free label byte

## Behaviour

Three two-record families in a body part share one frame and differ in exactly two bytes:

```text
02 02 43 00 47 04 04 01 c0 44 04 00 80 81 02 09 [16] 93 8a 03 [20]
02 02 45 00 ... same frame ...                     [16] 93 8a 03 [20]
02 02 3a 00 ... same frame ...                     [16] 93 8a 03 [20]
```

`ObjectSection.LabelRecord` rebuilds a matching record with byte 16 written as `00`, and
`RewriteLabels` applies it. The validated last byte is left exactly as found.

## Verification

Mutation in NX 2506, one field at a time, on the first record of each family:

```text
byte 16 -> 00, family 43    loads       bodies 1  volume 23999.999999999996
byte 16 -> 00, family 45    loads       bodies 1  volume 23999.999999999996
byte 16 -> 00, family 3a    loads       bodies 1  volume 23999.999999999996
last byte -> 00, 43/45/3a   OPEN_FAILED  (all three)
```

so byte 16 is a free label and the last byte is validated — the same shape as the `42 00`
family, where only the first of its two varying bytes is free.

Writing all five fixtures and opening them:

```text
lb_empty.prt bodies 0     lb_multi.prt bodies 0     lb_var_blank.prt bodies 0
lb_const_box60.prt bodies 1 volume 36000.0
lb_dim40.prt bodies 1 volume 23999.999999999996
```

Section 0 provenance in the body parts moves 350 -> 362 differing bytes; the body-less parts are
unchanged at 346/347 because they do not carry these frames.

## The validated byte correlates with the record index

For the twelve records that share this frame in a part, the last byte plus the record's index in
the object table is constant:

```text
dim40.prt    12 records   last + index = 76
var_two.prt  12 records   last + index = 82
             12 records   last + index = 83
empty.prt     0 records
```

so the byte counts down with the record's position, in two groups of twelve for a two body part.
That is a real correlation, and it suggested the field is a countdown a writer could shift.
Two tests reject that reading, both refused by NX 2506:

```text
one record's last byte changed            OPEN_FAILED
all twelve last bytes recomputed with K = 80   OPEN_FAILED
all twelve last bytes recomputed with K = 70   OPEN_FAILED
```

so the value is validated against something the countdown does not capture — the countdown is a
correlate, not the rule. It stays carried, and only the label byte at offset 16 is generated.

## Limits

- The label's meaning is unknown; it is free, not derived.
- The validated last byte is carried, so the record is only partly generated.
- `42 00` stays carried entirely, because both its varying bytes must agree.
