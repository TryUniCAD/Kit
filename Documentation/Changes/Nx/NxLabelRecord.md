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

## Limits

- The label's meaning is unknown; it is free, not derived.
- The validated last byte is carried, so the record is only partly generated.
- `42 00` stays carried entirely, because both its varying bytes must agree.
