# Only the feature section may be a stub in an NX payload

## Expectation

A payload section that only exists to hold derived or cached state should be
replaceable with an empty section, because the geometry stream carries the shape.

## Observed behavior

Replacing a section body with `OM\x01\x01` and loading the part in NX 2506 gives:

```text
section 4 stubbed   BODIES 1, VOLUME 36000.0, AREA 7199.999999999999
section 3 stubbed   fails to open
section 1 stubbed   fails to open
section 0 stubbed   fails to open
```

Section 4 is the feature record (`UGS::FEATURE_RECORD`). NX neither needs it to
open the part nor to measure the body, so it may be a stub.

Sections 0, 1, 2 and 3 must carry real content:

- section 0 holds the topology and the object classes
- section 1 holds the `UGS::CM_*` construction record
- section 2 holds the expressions
- section 3 holds the `UGS::OCC*` part and the save audit trail

A second trap is trailing data. The same stubbed payload opens when it ends at
the last section body and fails when two extra bytes follow it.

## Workaround

Generate sections 0 to 3 for the payload being written and stub only section 4,
ending the payload exactly at the last section body.

## Evidence

Stub ladder from `const_box60.prt`, one section body replaced per run:

```text
t4      section 4 only        loads, volume 36000.0
t34     sections 3 and 4      fails
t134    1, 3 and 4            fails
t1234   1, 2, 3 and 4         fails
t01234  every section         fails
```
