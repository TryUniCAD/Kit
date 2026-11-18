# SDK explicit ordinary planar groups

Task `B04-SW2026-ASSEMBLIES-C10`, owner `/root/assembly_occurrence`, delivery
PR #121. This is an internal constructor extension before the original A20/A21
evaluation. Those specifications, native files and detailed observations remain
sealed. The [evaluation protocol](SdkOriginalPlanarMateEvaluation2026.md) retains
the separate source-freeze and native acceptance requirements.

## Model and constructor scope

`MakePlanarGroup` consumes one actual generated `PartCandidate`, independent
`AssemblyInput`, a complete tuple of direct `OccurrenceIn` values, an ordered
tuple of `GroupMateIn` relationships and one actual fixed occurrence index.
Each relationship has two `PlaneEndIn` selectors containing a direct occurrence
index and actual child principal datum axis. Names, endpoint order, component
count, fixed anchor and distance are explicit authored inputs.

The factory uses the existing fresh assembly, header, actual child target,
occurrence, wrapper, datum-time, positive distance, dimension and serialization
constructors. It adds no reference or dimension family. The first profile
requires initially satisfied aligned planes, the same principal axis on each
endpoint, a visible resolved rigid external shared child, and positive signed
unflipped distance. It rejects unsupported state before publishing bytes.

The group may contain more than two direct occurrences. The anchor may be the
first, last or another actual member, and a particular relationship need not
include it. Every endpoint must still refer to its own actual direct occurrence
and selected child datum. One generated definition and one directory record
remain shared by all occurrences.

## Shared construction and field rules

The prior pair interface delegates its occurrence publication to
`PutPartRefsMut`, then returns its original two references. The complete group
uses that same publication directly. Directory users, ordered `f68` body rows,
`f1560`, reversed direct CMgr rows, fresh configuration activity and both fresh
header activity counts derive from the actual component tuple. Parent bounds
fold each transformed child box and its independent sphere in native order.
`RecordMateMut` shares the unchanged configuration/header allocation and
creation-log update between the pair and complete group paths.

Low-level mate validation now obtains the complete actual direct list through
`ReadMateOccs`. It checks its length fields, actual containing owner, distinct
object identities, schema-one IDs, allocation and matching fresh header/config
activity. Prior mate wrappers must resolve to members of that same complete
list. The selected pair remains exactly two distinct actual occurrences. The
existing factories retain distance-before-mate allocation, per-mate endpoint
ordinals, the assembly-wide wrapper counter and the one actual fixed anchor.

These changes generalize previously traced ordinary operations. Their native
authority remains [planar input translation](PlanarMateInputTranslation2026.md),
[wrapper write state](PlanarMateWrapperWriteState2026.md),
[distance construction](PlanarDistanceMateConstruction2026.md),
[ordinary occurrences](OrdinaryOccurrenceConstruction2026.md) and the shared
activity/bounds records. No saved stream, row, template, field program or
case-specific constant is used.

## Independent reference arithmetic

The first independent comparison identified a one-ULP convention difference
for the unrelated -29 degree Z rotation. The SDK retained the normalized third
axis; the research frame recomputed it from the final two tangents. Only
generated transform, bound and plane-cache words differed. The product writer
was unchanged. The independent reference adapter now retains its mathematically
computed normalized basis, including the placed-datum input. It reuses the
independent research vector operations and does not import SDK geometry.

The original failed snapshots remain private and immutable. This is an exact
comparison-adapter correction, not new native acceptance or a newly established
vendor-wide floating-point rule. [Specific gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/ReferenceBasisCanDoubleCrossNormal.md)

## Frozen process proof

[Sanitized receipt](../measurements/2026/SdkPlanarGroupsConstruction01.json) binds
raw result `e2f664a081f6219678a6311001b0853f2702393ade63bb7f8ce5e52cfb099c2e`
and source manifest
`753f64e4222ee9172b24d65abd02cbd2469254b5bf865f1a085c39276791f162`.
Source was copied and hashed before executing any candidate and remained
unchanged throughout the proof.

Six unrelated neutral cases cover 2, 3 and 5 components, both first and last
anchors, positive driving distance, reversed endpoint order and relationships
whose two participants exclude the fixed anchor. Each uses the real dimensioned
rectangle child, is generated twice in distinct guarded processes, and matches
every complete parent/child stream and container byte from the independent
mathematical research composer. All linked production codecs round-trip.

Eight further processes reject a missing component endpoint, duplicated
participant, cross-axis datum pair, duplicate feature name, zero or wrong signed
distance, absent anchor and unsupported suppressed-state field. They emit no
bundle. All 12 prior ordered and 18 prior single-mate bundles remain exact
through both their original constructors and the explicit group pair interface.
Both prior recursive layouts retain every complete generated file byte.

The frozen proof has 142 independently identified successful workers, eight
additional rejecting invocations and 1,740 typed stream round trips. Runtime
input file reads, SDK imports of research implementation, native launches and
held-out input reads are zero. Scoped static checks pass. The permanent tests
exercise complete stdin/file generation in fresh interpreters; they are not
constructor mocks or unit tests.

No public writer is enabled and no new native or held-out acceptance is inferred
from these process checks. A controlled disclosed generated multi-component
native replay and the fully frozen original-case evaluator remain required.
