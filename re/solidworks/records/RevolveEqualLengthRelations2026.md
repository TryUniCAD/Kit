# Square revolve equal-length relation owners in SOLIDWORKS 2026

Workstream `B04-SW2026-REVOLVE-ENDS/square-relation` belongs to the PR #121 takeover. It extends native sketch constraint ownership for ordinary rectangular revolutions. It depends on the [ordinary constructor](OrdinaryRevolveEndModes2026.md) and the [single total driver](../../../Documentation/Changes/Interchange/AngularRevolveTotalAngle.md).

In the first sealed end-mode comparison, both Two Directions cases and one Mid Plane case independently matched their recursive trees and measurements. The remaining Mid Plane native reference opened with one solid and zero errors or warnings. Its actual relation enumeration had five entries and the observer expected four, so the phase stopped before the corresponding candidate opened. Both controls passed and the aggregate reports zero qualified cases. [Original mixed receipt](../measurements/2026/SdkOrdinaryRevolveEndHeldout01.json)

A separate read-only probe on that unchanged original completed between two passing controls. Its phase SHA-256 is `de750e71eeabd97d10a28d5a9e277555fda0ad0c1aa95b6873c51fa00c1767a2`. The installed SwConst 34.0 library and actual COM relation bind code 14 to `swConstraintType_SAMELENGTH`. The two ordered solver owners are Line2 and Line1. Both are live contour segments. The independent primary unary group retains its four segment owners. [Native inspector](../../tooling/sw2026/InspectRevolveRelations.py) · [API relation type](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.ISketchRelation~GetRelationType.html)

## Disclosed source replay

Two separately authored squares use different planes, side lengths, axis locations, angles and direction modes. Eight native phases complete their source authoring, live edits, edited saves and fresh reopens between healthy controls. Their linked Config and Resolved streams replay byte for byte in two guarded workers. Both sources expose the same scalar layout with separately owned line references. [Guarded disclosed receipt](../measurements/2026/RevolveEqualLengthOwner01.json)

| Field or owner | Classification | Current evidence |
| --- | --- | --- |
| `dims.log_g2` `h1`, `h2` | Input links | Two ordered `sgLineHandle` objects bind to distinct live contour lines through their actual local indices. |
| `f80` | Format vocabulary | 14 for the equal-length relation. Independent COM enumeration returns `swConstraintType_SAMELENGTH`. |
| Owning lines' `f20` | Derived | Both lines carry two actual relation references, one from the unary group and one from the binary group. |
| `f90/f94/f98/fa0/fa4` | Common ordinary logical fields | Both disclosed sources store `2/0/0/65534/0`, matching the ordinary unary logical constructor's shared settings. |
| `f28/f48/f60/f108/ext1/ext2/ext3` | Absent owner references | Both recorded relation operands are local lines. The measured case has no driving value, alternate or external references. |
| `ff8/ffc/f100/f118/f120/f150` | Inactive values | Both sources store zeros. The complete row is re-emitted without any provisional body. |
| `f110/f114/f154` | Absent qualifiers | Both sources store `-1` throughout. |
| Common dimension base and `f50` | Shared constructor and unallocated ID | The normal base fields use the logical relation scope. Both sources leave the relation without a separate persistent dimension ID. |

The public portable relation name is `equal`. The constructor must emit it from the actual neutral relation, even when the endpoint coordinates already form a square. [Source author](../../tooling/sw2026/AuthorEqualLengthRevolves.py) · [Raw owner replay](../../tooling/sw2026/revolve/EndModes/AuditEqualLengthRows.py)

## Independent lock

Two further independent native squares complete their three source phases with both controls healthy in eight fresh processes. Their source author verifies the actual owned equal-length relation through the angle edits and the edited fresh reopen. The original Windows lock is preserved at SHA-256 `f083f56d7dad630ae2fbebda1c983ce06c8e5c935ace81317dc0f050b561cd53`. The held-out model and detailed receipts remain private until writer and comparison are frozen. [Pre-writer square source lock](../measurements/2026/RevolveEqualLengthSourceLock01.json)

## Generated native records

The shared constructor emits the actual ordered local pair from the
neutral sketch. The strict stream reader preserves both relation owners
and rejects unsupported binary records. Across both disclosed
inputs, the ordered operands and native embedded fields match, all 20
linked streams replay exactly and the fresh model-only workers make zero
external access attempts.

[Generated disclosure receipt](../measurements/2026/SdkSquareRevolveGeneration01.json)

The frozen SP05.2 comparison opens both disclosed generated squares
with zero errors or warnings. It compares the actual five relations and
their ordered operands, 175 recursive feature rows and 42 measured
quantities across seven original and edited states. Both controls pass
across ten distinct processes. Each edit survives save and fresh reopen.
[Native disclosure](../measurements/2026/SdkSquareRevolveDisclosedNative01.json)

The two pre-writer locked squares pass the same seven comparisons
using the frozen writer and method. Both generated archives load and
rebuild with zero errors and warnings. The original and candidate
preserve all five solver relations, the ordered equal-length operands,
the complete tree and the live D1 and D2 edits where applicable.
The independent native batch qualifies both cases in ten fresh
processes. The public registry still needs byte parity at its normal
output boundary.
[Independent native receipt](../measurements/2026/SdkSquareRevolveHeldoutNative01.json)

The next isolated comparison reuses those exact lifecycle receipts and reconstructs the measured bytes through the normal SDK publication boundary. The source files stay in custody. [Public parity method](SquareRevolvePublicParity2026.md)
