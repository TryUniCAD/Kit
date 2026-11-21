# Strict cache-free reading of a selected-empty first boss

Task `B04-SW2026-BLIND`, PR #121. The default strict reader with B-rep enabled
now projects the selected existing-body mode of a single cache-free,
forward blind rectangular boss. The implementation joins the actual linked
`moExtrusion_c` schema 1 root, its sole profile parent, the active depth
parameter and the actual Front sketch frame. The atomic mode word is
`f544 = 1` with absent `f548` and consumed/output pointers, empty managed
and ghost body collections and no partition or equation. The existing
create-state flags, dimension checks, geometry-owner census and planar
four-line loop validation also apply. This identifies a first new solid with
zero eligible previous solids. Scope zero still reaches the ordinary create
definition. [Static selector and archive ownership](SdkWarmNestedLeaf2026.md#explicit-existing-body-scope-on-the-first-solid) ·
[Native feature owner](../../../src/convert/adapters/solidworks/Core/TypedResolved/Geometry/CheckPrismBoss.py)

The new value of the existing neutral `ScopedExtrusionFeature.ScopeMode`
is `first_creator`. It requires empty selected and affected prior-body
lists, one active `create` feature, a single result body linked to it and
no earlier solid operation. Its driver is the actual positive finite
length parameter for the single blind end. The direction is through the
profile plane's forward normal. Additional picks, offsets, drafts and
reverse or secondary ends refuse. The existing `explicit` mode continues
to require selected body IDs. A retained native profile-axis marker
remains source evidence alongside the sketch. The typed first creator
omits a feature scope selection because no prior body was picked.
[Portable feature](../../../src/interchange/Features/ScopedExtrude.py) ·
[Neutral timeline and driver checks](../../../src/interchange/document/Validation/FirstScopeErrs.py)

## Disclosed measurements

The confirming native authority is `FirstCreatorScopeAcceptance01.json`
at SHA-256 `90d4d1836492f49fd2d6c99a122664c5be918d128dcd1c604a589d2ea724fa21`.
SOLIDWORKS 2026 SP05.2 build 34.5.2.0604 recorded 16 independent processes
and four healthy controls over both paired lifecycles and selection
access. The direct selected-body count was unavailable at `-1`. With
selection access, each selected-empty case had scope enabled, AutoSelect
false, zero prior bodies and an absent array. The comparison controls
exposed one actual selected body. The direct count and the runtime
AutoSelect observation remain distinct from the persisted scope word.
[Combined native and saved typed receipt](../measurements/2026/FirstCreatorScopeAcceptance01.json) ·
[Count after selection access](../../../Documentation/Gotchas/Conversion/Solidworks/Model/Extrusion/FirstCreatorScopeCountAfterAccess.md)

| Rectangle | Initial dimensions in mm | Edited depth in mm | Initial and edited volume in mm³ |
| --- | --- | ---: | --- |
| Centred | 40 × 20 × 8.37 | 11.625 | 6696 and 9300 |
| Translated | 37 × 29 × 12.5 | 9.875 | 13412.5 and 10595.875 |

Four fresh SDK processes independently read one exact generated file and
its own immutable edited derivative per process. For each of the two
All/Selected cold pairs, the full neutral feature, sketch, parameter,
selection, support, body and B-rep projections compare exactly after
unwrapping only the scoped feature definition. Each worker independently
compares actual oriented surface and solid integrals against the model
and the previous native measurement, including bounds, area, volume,
centre and 6-face/12-edge/8-vertex topology. The linked D1/D2 sketch
constraints, D1 boss driver, dimension label points and their separate
native-ID owners survive the comparison. Seven typed-wire contrasts
reject alternate flags, stored pointers, an extra parent and a reversed
end. Eleven portable contrasts cover invalid scopes and operations,
earlier solids, unsupported selections and direction, and altered
driver ownership. The legacy positive explicit-scope constructor is a
separate control. [SDK readback receipt](../measurements/2026/SdkColdFirstCreatorScopeRead01.json)

The same workers compare all four actual native-saved edited caches
against native geometry and the separately measured output atom, partition
marks and edited depth. The linked archive keeps the stored scope word
and absent wrapper. The cold comparison's baseline projects the
native-saved definition as an ordinary join. A later saved read proof
independently recovers the selected-empty typed create state and preserves
the original saved geometry. Metadata-only SDK reads and public
SOLIDWORKS writing stay outside this cold scope. The receipt adds zero
new native processes, original-source transfers or held-out cases.
[Later saved projection](FirstCreatorSavedScope2026.md)

## Replay

From the isolated checkout run the audit with the exact disclosed native
packet directory and an unused output file.

```sh
python3.14 -I -B re/tooling/sw2026/nested_publication/MeasureColdCreatorScope.py \
  DISCLOSED_FIRST_CREATOR_PACKET --output NEW_RECEIPT.json
```

The packet manifest SHA-256 is
`c8addf29032d630b2513ceae9f5d00a7bd5e0f56f578c619079d16bfe30a690f`.
Each process verifies the disclosed raw inputs before it denies file
reads and runtime access during in-memory SDK work. The standalone
JSON codec preserves the exact full neutral document through strict
stream and path reopening. Both previously authored neutral models
also preserve the mode through ordinary registry JSON path and stream
writing with no dropped scope. Intact native models carry native-only
feature records and still refuse a normal registry conversion without
touching either destination. [Reproduction tool](../../tooling/sw2026/nested_publication/MeasureColdCreatorScope.py)

The later saved-scope work qualifies the two edited selected-empty
derivatives through their actual active configurations and retained
partitions. [Saved reader qualification](FirstCreatorSavedScope2026.md)
