# Principal-plane direction construction for local linear patterns

Task `B04-SW2026-LOCAL-LINEAR-PATTERN/principal-direction`, PR #121,
owner `/root/format_proofs`.
The shared pattern line constructor can build the selected-direction
member for the actual Top or Right plane of the generated joined stock.
The independently selected `moCompRefPlane_c` wrapper owns role 2 or 1
respectively. The containing pattern owns reversal separately. The
compiler keeps the existing angular role and native publication gate.
[CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) ·
[Writer model](../../Playbook/WriterModel.md)

## Direction, identity and chronology

`ReadPatDir` uses the actual version-19000 default datum's signed
principal frame and finite display borders. `DatumLine` computes the
four perimeter corners in native order, forms the reference point from
their average and derives the normal displacement and span. The plane's
display origin is a separate member from its geometric origin. Both
display axes must match the signed canonical frame. The display origin
must lie on the geometric plane. The resulting point retains the exact
native ordered arithmetic, including the one-ULP Top-plane case.
[Exact-build line resolver](LocalLinearPatternPlaneDirectionRule2026.md) ·
[Shared direction geometry](../../../src/convert/adapters/solidworks/Archive/Construction/Patterns/Direction/ReadPatDir.py)

`MakePatDir` verifies that the actual generated plane belongs to its
part, its persistent allocator and the canonical system inventory. The
new reference uses a separately allocated local unit component with that
same model owner. The declared select ID and both first creation logs
supply its historical reference. If both generated headers lack an
event for an actual principal default, the existing unset epoch rule
applies. The angular branch still needs explicit paired events matching
its creation input. The last-access word keeps its existing independent
model-header rule. [Selected reference constructor](../../../src/convert/adapters/solidworks/Archive/Construction/Patterns/Direction/MakePatDir.py) ·
[Registered header epoch rule](SdkHeaderEpochIntegration2026.md)

The disclosed rightward and reversed Top-plane cases each include the
native original, spacing edit and count edit on SOLIDWORKS 2026 SP05.2
`34.5.2.0604`. `D01X` selects Right Plane ID 4 and travels along
positive X. `D02Y` selects Top Plane ID 3 and uses the separate reversal
to travel along negative Y. Six isolated workers match the actual line,
reference, component and both headers. The workers re-emit both linked
Config-0 and ResolvedFeatures streams exactly. The original saves were
checked against the published source hashes before parsing.
[Disclosed source lock](../measurements/2026/LocalLinearPatternDisclosedSourceLock01.json) ·
[Exact placements](../measurements/2026/LocalLinearPatternDatumPlacement01.json)

## Independent neutral construction

Two fresh neutral model requests build different joined stocks using
the existing part system, seed, principal display and header constructors.
They supply only explicit dimensions, names, a selected principal axis
and a creation epoch. The Right direction uses the existing unset epoch
for its default datum. The Top direction binds two real generated
creation entries. The actual shared `f1288` field mask encodes the
computed reference after the generated stock's real Config-0 and
Resolved maps. A separate decoded owner graph re-emits the member
byte-for-byte. Both requests repeat in fresh guarded processes. The
geometry, references and map entries are compared independently. No
case-specific source values enter that generation.

Six authored contrasts refuse Front, an off-plane display origin,
empty display borders, a detached plane, mismatched headers and a
missing creation event on just one header. The two existing guarded oblique
publication runs reproduce both measured whole-file hashes, twenty
logical streams and 40 exact fresh or readback SDK publications. They
retain all 96 refusal results. The new proof invokes no CAD and reads
no protected originals. [Principal direction receipt](../measurements/2026/LocalPrincipalPatternDirection01.json) ·
[Existing measured oblique route](AggregateMeasuredLinearPattern2026.md)

```sh
python3.14 -I -B re/tooling/sw2026/linear_pattern/ProvePrincipalPatternDirection.py \
  --capture /absolute/path/to/LinearPatternSourcePacket03/DisclosedNative
```

The general research CLI lacks a construction-phase audit for a single
generated owner after two linked maps. The proof uses the existing
typed field actions and supervised fresh processes. It emits only a
numeric report. The principal D1/D3 display and catalogue, complete
principal pattern composition and separate native-tested output
qualification remain outside this delivery. No held-out or additional
native acceptance credit applies.
