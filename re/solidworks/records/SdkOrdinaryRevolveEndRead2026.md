# Strict ordinary revolve end-mode readback

Task `B04-SW2026-REVOLVE-ENDS`, PR #121. The takeover owns the
underlying source qualification and Windows oracle. This tranche
owns the portable parameter contract and strict SDK read boundary.
Its baseline is `b18caa86c15d2c65ad95c9a572bbc9d06701da8c`.
It depends on the [modern end-owner study](OrdinaryRevolveEndModes2026.md)
and [earlier one-sided reader](PrincipalRevolveReader2026.md).

## Live parameters and sweep

`ReadRevEnd` recognizes the measured modern `moRevEndSpec_c` end-mode
words and follows the actual display to its local dimension and radian
parameter. The secondary display remains null for Mid Plane. The two
display chains and persistent dimension IDs must be distinct in Two
Directions. The selected construction line, its same-part sketch, the
canonical support frame and the positive live parameters remain part of
the same projection.

| Raw `f08/f0c/f10` | Neutral mode | Parameters | Interval about the effective axis |
| --- | --- | --- | --- |
| `1/0/0` | `one_sided` | `D1` in `f18` | `[0, D1]` |
| `0/6/0` | `symmetric_full` | Total `D1` in `f18` | `[-D1/2, +D1/2]` |
| `0/0/0` | `two_sided` | `D1` in `f18`, `D2` in `f20` | `[-D2, +D1]` |

Reversing Two Directions negates the effective axis. `D1` and `D2`
retain their roles. The historical neutral `symmetric` mode continues
to hold two distinct positive equal half-angle drivers. The new
`symmetric_full` mode keeps the single live total and derives both halves.

The cold reader uses the real ordered line endpoints. Each of the four
disclosed native contours uses active point slots `0, 1, 6, 7` and line
ordinals `0, 3, 2, 1`. The cold graph additionally checks that its allocated
angular nodes match the actual live display chains. Other ordinary root
checks still run. Reversed Mid Plane, full-turn new modes, expressions,
legacy display branches and nonblind end owners remain outside this path.

## Guarded evidence

The [SDK receipt](../measurements/2026/SdkOrdinaryRevolveEndRead01.json)
pins eleven fresh host workers per run, exact assets and resource
reads, reader source owners, and SDK document digests. Two full runs
produced byte-identical receipts. It checks the following.

- Four disclosed SOLIDWORKS 2026 SP05.2 originals pass strict saved and
  history reads. Each saved body retains its cache payloads, actual
  creator link and `OrdinaryBossRevolve` label. The linked profile
  independently reconstructs the same signed sector without cache input.
- Four independently generated model-only controls pass the normal
  strict cold reader and history read. The default cold path performs
  zero package layout reads and publishes no native B-rep payload.
  Forty stream digests match the operator's exact construction receipt.
- Both paths preserve the actual selected line and driver ownership.
  Their closed bodies have six faces, twelve edges and eight vertices.
  The probe independently computes all eight cap corners, bounds,
  area, volume and centre of mass from the disclosed authoring spec.
  It checks both bodies' cap corners, analytic carriers and four orbit
  trims, the computed geometry measures, and the recorded native volume
  and area. The
  analytic centre agrees with the recorded native centre. Centre of
  mass comes from those independent checks, while the SDK reports
  area, volume and bounds.
- Three existing generated one-sided controls and the matched saved
  one-sided control retain exact document digests in both reader views.
  The four neutral side modes round-trip their references through JSON.
  Fifty-one guarded contrasts refuse invalid end words, missing or aliased
  secondary owners, unsupported directions and spans, and changed
  angular map membership.

The host comparison started after the disclosed source captures. The
initial native Mid Plane lifecycle stopped after a report replacement
error. The [same-source recovery](../measurements/2026/RevolveEndSourceRecovery01.json)
passed with both controls. Geometry expectations use the original
successful author phase. The original failed result remains recorded.
This receipt records host SDK readback. Native writer and full
source-conversion acceptance require their own locked lifecycles.

```sh
python3.14 -I -B re/tooling/sw2026/revolve/EndModes/CheckRevEndRead.py \
  --discovery-root /path/to/disclosed/RevolveEndDiscovery01 \
  --generated-dir /path/to/generated/Assets
```
