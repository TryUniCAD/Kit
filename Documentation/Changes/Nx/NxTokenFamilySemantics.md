# The token family's numbers are not model geometry

## Behaviour

No writer behaviour changed. This entry records what the `02 02 ?? 00 35 ??` family's
decoded numbers control, which is what a derived emitter needs to know.

## What was measured

The 62 byte record in `const_box60.prt` carries three `100.0` handles and one `360.0`
float word. Each was rewritten with the now-derived encoders and the part loaded in
NX 2506, reading mass properties back:

```text
part                      bodies  volume
const_box60 (source)           1  36000.0
three 100.0 -> 200.0           1  36000.0
360.0 -> 720.0                 1  36000.0
both changes                   1  35999.99999999999
```

So changing those values by 2x leaves the solid, its volume and its body count
untouched: the numbers are display or annotation metadata, not model geometry, and NX
does not reconcile them against the body on load.

That matters because it means the family can be emitted with values the writer chooses,
the same way the label families were, without changing what the part measures — the one
thing that has to stay true is that the values are internally consistent with the rest
of the section, which the earlier mutation work already showed is not enforced.

## Verification

```text
sm_v100to200.prt   part units 1  bodies 1  volume 36000.0
sm_f360to720.prt   part units 1  bodies 1  volume 36000.0
sm_both.prt        part units 1  bodies 1  volume 35999.99999999999
```

`ValueWord` and `FloatWord` reproduce the original words exactly, so the mutants differ
from the source only in the fields named above.

## Limits

- This is a measurement entry; no writer pass emits the family yet, so section 0's byte
  provenance is unchanged.
- Volume is the only invariant checked. A display-only difference would not appear in
  mass properties, so the claim is that these fields are not geometric, not that they
  are invisible to the user.
