# Ordinary revolve mid-plane and two-direction end owners

Task `B04-SW2026-REVOLVE-END-MODES`, PR #121. The takeover
owns the native source locks, oracle and delivery. This research starts
at aggregate `19e2e99aa8269dd0687e7edd332ca16671982190`. Its exit
is an exact build-scoped wire and geometry boundary for the two
additional angular modes. It depends on the
[ordinary revolve serializer](SdkOrdinaryRevolveArchive2026.md),
[angle handle ownership](OrdinaryRevolveSemanticOwnership2026.md)
and [principal-plane reader](PrincipalRevolveReader2026.md).

No production reader or writer code changed. The evidence uses
four newly disclosed matched controls, four earlier disclosed
one-direction controls and the licensed model module outside the
checkout. No sealed specifications, held-out originals or outcomes
were opened. Held-out and writer qualification remain separate.

## Modern archive mode

The matched Top-plane controls keep the same ordinary rectangular
profile, selected upward construction line and first angle.
The oracle is SOLIDWORKS 2026 SP05.2 `34.5.2.0604`. The end
mode reported by COM is the public `swRevolveType_e` in the
[installed type library](../v2026/evidence/RevolveAndConstraintTypeLibrary.json)
and [SOLIDWORKS API reference](https://help.solidworks.com/2026/english/api/swconst/SolidWorks.Interop.swconst~SolidWorks.Interop.swconst.swRevolveType_e.html).
The model feature's serialized `f820` stays zero on all four modern
saves. The mode lives in the actual `f8d8` end object.

| Disclosed source | COM Type | Feature `f820/f824` | End raw `f08/f0c/f10` | Actual angular displays |
| --- | ---: | --- | --- | --- |
| `EndSingle` | 0 | `0/0` | `1/0/0` | `f18` owns D1. `f20` is null. |
| `EndMidplane` | 1 | `0/0` | `0/6/0` | `f18` owns total D1. `f20` is null. |
| `EndTwo` | 2 | `0/0` | `0/0/0` | `f18` owns D1 and `f20` owns D2. |
| `EndTwoReverse` | 2 | `0/1` | `0/0/0` | The same two slots retain D1 and D2. |

All four have null feature-level `f808/f810` displays. Their
modern end serializer stores raw `f08`, two intervening
`f138/f13c` words, then actual end conditions `f0c/f10`.
References, offset distances, offset reversals and four display
references follow in the same order. The measured reference and
offset-display slots are null. Offset words are inactive on this
cohort. The [physical receipt](../measurements/2026/RevolveEndOwners01.json)
records actual words, object extents, stream hashes and owner identities.

The native getter `moRevEndSpec_c::getSingleEnd` at
`0x4c39ac10` returns effective one for `f0c=6`. It leaves the
stored `f08` untouched. The constructor can allocate both displays.
Rebuild cleanup at `0x4c3a7510` retains `f18` for primary end
types zero and six. It clears `f20` for Mid Plane or a raw single
end. The two-blind-end branch retains its second display. The
secondary getter at `0x4c396120` returns zero for the measured
null Mid Plane slot. That value does not denote a stored driver.

Two distinctions matter for construction. The old
[stepped-pin and slab observations](RevolvePinMidplane.md)
precede the pinned SP05.2 corpus. Their zero-angle observation
does not establish the modern `f20` owner. The pinned
[private authoring constructor](OrdinaryRevolvedBoss2026.md)
accepts a separate private type discriminator and can set
`f820`, including values one and two on its own paths. The
modern native saves above all store zero in that field.
[Modern end mode gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/RevolveWireModeUsesEndSpec.md)

## Live angle ownership

For both measured slots, the actual
`moDisplayAngularDim_c.f850[0].o` is a local
`moFeatureDimHandle_c`. Its `ff0` is an `AngleDim_c`.
That dimension's `f28` is the actual `moAngleParameter_c`.
Its name comes from the owned name node and its radian value
comes from `f58`. Feature-level display slots, presentation
coordinates and the public secondary getter cannot substitute
for that chain. Native display selection at `0x4c396320`
selects `f18` or `f20` by side irrespective of reversal.

D1 is `1.714785990084429` radians with actual dimension ID
27 in all four files. The two-direction files also have D2
`0.7592182246175333` radians with dimension ID 28. Those
IDs are observed allocation results. The two displays,
handles, dimensions and parameter objects are distinct.
Both two-direction senses completed independent D1 and D2
edits and fresh reopen in this disclosed acquisition. The
first Mid Plane pass reached a live D1 edit; concurrent
report access interrupted that run before the edited save.
Recovery uses the same immutable original digest and is
recorded separately by the oracle owner. Both bracketing
controls passed.

## Signed sweep and support

In the model module, the sweep uses the actual feature's
`+0x1788` axis virtual at `0x4c39b5c5`. The exact
`moRevolution_c` vtable maps it to `0x4c3964f0`, which
resolves `f830` and negates the selected unit axis when
`f824` is nonzero at `0x4c396524`. D1 and D2 retain
their independent slots and positive values.

| Mode | Interval around the effective axis | Exact calculation sites |
| --- | --- | --- |
| Single | `[0, D1]` | D1 from the live forward display. |
| Mid Plane | `[−D1/2, D1/2]` | Half at `0x4c39b7ac`, exact literal 0.5 at `0x4cd9a3c0`. Pre-rotation about the negated effective axis calls `mg_RotateAtPoint` at `0x4c39b7e3`. |
| Two Directions | `[−D2, D1]` | D2 at `0x4c39b873`, sum check and calculation at `0x4c39b8b0/0x4c39b8e2`, and D2 pre-rotation at `0x4c39b91a`. |

The reversed two-direction case mirrors the partial annulus about
its sketch plane in the matched cohort. Relative to the original
raw axis, its physical interval is `[−D1, D2]`. The same
angular span preserves volume and surface area. The signed
transverse centre-of-mass coordinate distinguishes the two
directions. A future acceptance run should compare all cap
boundaries and signed mass-centre components as well as the total
span. Nonblind reference owners and full-turn Mid Plane or
Two Directions require their own source and lifecycle evidence.

The [static pins](RevolveEndModesStatic2026.json) bind exact
module, mapped ranges, imports and REA evidence identities.
The original instruction offsets and independent REA views agree
on the serializers and cleanup. The signed dataflow follows
the original PE and its named imports. The external raw
views remain outside the repository.

## Existing SDK boundary and reproducible check

All four disclosed sources exactly re-emit the linked Config
and Resolved streams through the current typed grammar.
Eight fresh workers complete 16 comparisons with identical
repeat reports and zero runtime file, process, library or network
access. The actual same-model sketch parents, construction
line handles, local rectangle and Top support frame are valid
on all four. The existing linked owner reader admits the
one-direction file and stops on the three other files in
`ReadRevAngle` with `ordinary revolve requires one active
blind angular owner`.

```sh
python3.14 -I -B re/tooling/sw2026/revolve/EndModes/AuditRevEndOwners.py --asset /path/to/disclosed.SLDPRT --sha256 SHA256
python3.14 -I -B re/tooling/sw2026/revolve/EndModes/PinEndModeRanges.py /path/outside/checkouts/sldmodu.dll
```

Current `AngularRevolve` symmetric intent requires two distinct
positive parameter identities and `GetAngleSpan` checks two equal
half angles. Mid Plane needs one actual editable total D1.
A neutral extension must preserve that single driver and compute
its half angles for geometry. D2 must remain a distinct active
parameter only for the measured two-direction case. The existing
one-sided constructor and writer keep their current admission.
The current cold geometry builder also assumes an interval starting
at zero. Use the actual signed interval and real line incidence in
any future owner-driven geometry.
[Independent line-incidence limitation](../../../Documentation/Gotchas/Conversion/Solidworks/Model/Revolve/RevolveContoursNeedLineIncidence.md)

## Generative construction and disclosed native proof

The shared writer consumes the one total driver or both independent
positive drivers and uses the rules above to write the end spec. Each
active display receives its own parameter, value and retaining handle.
The display cache at `f5b0` is derived from its own live radian value.
The primary angular display retains base `f1018=0x18`. The secondary
branch adds bit `0x4`, observed on both reversal senses of the matching
native saves. For the same pair, the keyword index has D2 then D1 in
forward orientation and D1 then D2 in reverse. These are derived
display and index values. The active end slots define the ordered
driver ownership independently. [Guarded writer receipt](../measurements/2026/SdkOrdinaryRevolveEndBuild01.json)

Four model-only candidates re-emit all 40 typed streams exactly and
the path and named-stream preparations agree. The native evaluation
opens each cold with one solid, changes each active angle independently,
saves and reopens the edited derivative. Fourteen paired observations
match 19 ordered top-level feature rows and 84 mass-property values
to six significant figures. Both controls pass across ten distinct
processes. [Native disclosure](../measurements/2026/SdkOrdinaryRevolveEndNative01.json)

The independent locked lifecycle and recursive tree comparison govern
registration of the new end modes. [Pre-writer source lock](../measurements/2026/RevolveEndHeldoutSourceLock01.json)
