# Ordinary version-19000 Config graph in the SDK

The SDK reads and serializes the complete exercised `Config-0` graph from native
field-order rules. The public reader retains its existing semantic projection.
Full linked-graph admission, fresh writer qualification, and C10/native acceptance
remain unfinished.

## Ownership and scope

Task `B04-SW2026-CONFIG`, owner `/root/flag_ownership`, delivery PR #121. The
parent owns Git publication, the vendor oracle, guides and registers. This
tranche depends on the shared archive object/map model, scalar/string/count/tag
codecs, the [header handoff](ConfigHeaderHandoff2026.md), and the separate
[CMgr grammar](CmgrBodyGrammar2026.md). Its exit is exact current-version Config
field/alias/map parity, real process verification and honest profile diagnostics;
it does not close the overall CAD goal.

The full [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md),
[RE instruction book](../../Playbook/README.md),
[loader chapter](../../Playbook/LoaderAnalysis.md) and
[writer chapter](../../Playbook/WriterModel.md) apply. Their stopping conditions
remain: “The first is success under every criterion on this page.” and
“The second is the end of the available context.” Missing grammar remains work.
No worker VM, CAD/COM, service, licensing or held-out access occurred. Original
licensed PE metadata was read without loading executable code. REA reported no
open target and a pre-existing cleanup-pending state; this worker neither opened
nor closed a shared analysis target.

## Provenance and classification

The target is SOLIDWORKS 2026 SP05.2, executable build `34.5.2.0604`, ordinary
archive version `19000`. Field rules were authored from the existing current
native loader/serializer knowledge, not from saved values or offsets. The
[scalar census](LinkedGraphScalarConstruction2026.md) records the disclosed
12-file dependency union. Important proof sources are:

- [Model construction](ModelConstruction2026.md) and [Config anatomy](ConfigZero.md)
- [Ordinary occurrence ownership](OrdinaryOccurrenceConstruction2026.md)
- [Common part owners](CommonPartOwners2026.md)
- [Annotation native field order](AnnotationArchive2026.md) and its exact JSON record
- [Material and visual owners](MaterialDisplayArchive2026.md)
- [Framework counts](MfcCountArchive2026.md)
- [Context chains and string maps](ContextAndStringMapArchive2026.md)
- [Native runtime descriptors](ConfigRuntimeDescriptors2026.json)

The source-backed layouts add 129 owner/helper declarations to the existing
46-layout shared body registry. Availability is distinct from actual use. The
12-file check executes 153 Config body schemas in each direction. The five
separately decoded ModelHeader owners are `moHeader_c`, `moLogs_c`, `moStamp_c`,
`moExtObject_c` and `moExtObjectList_c`; with those prerequisite reads the original
Config-load union is 158. Store covers Config bytes alone and remains 153.
The registry does not claim that every available branch was exercised.

Confidence is confirmed for reproduced structure on the disclosed paths and
for the directly read native descriptor metadata. Field semantics, legal model
domains, derived cache neutrality and fresh construction retain their existing
partial or unqualified status. This grammar supplies no saved field defaults.

## Framing, identity and map handoff

`ReadConfigMut` and `WriteConfigMut` use the existing `ArchiveNode`,
`RuntimeClass`, `ArchiveMaps`, `MapSnapshot` and body field DSL. There is no second
object representation, captured field program or production research import.
The version must be exactly integer `19000`; the root must be a concrete current
`moPart_c` or `moAssembly_c`. The complete stream must have no tail.

Each direction starts its own map at one. Root class/object allocation happens
before the model's direct-reference boundary. `HeaderRefNodes` selects the exact
already-decoded header self object, then directory children in order.
`BindNodesMut` allocates those object identities without tags or bodies and sets
the Config base to the resulting counter. It does not copy header map indices or
seed from CMgr. The measured parent and child bases are five and four
respectively for this cohort; these are outcomes of selection/allocation, not
universal constants.

`ConfigGraph` retains its root, the original header, frozen map membership,
actual base, archive context and usage report. Map snapshots preserve node
aliases and cycles. `WriteConfigMut` returns new bytes and the resulting graph
state; section lengths, tags, reference indices and collection lengths derive
from the modeled graph. Mutable/lazy field mappings remain owned by their nodes.

CMgr remains an independent map-one graph. `MakeLinkContext` takes that explicit
manager graph and the Config graph and derives `model_is_part` from the actual
root plus `cmgr_f658` from the manager's raw field. It never substitutes Config
state for that manager word or adds manager objects to the continuous
Header→Config→Resolved map. Resolved loading is a subsequent, unpromoted tranche.

## Field operations

| Operation                | Current rule and limit                                                                                                                                           |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Section                  | Read u32 byte length and require exact consumed length; store computes the prefix from actual emitted fields                                                     |
| Direct references        | Bind exact header object aliases at the model boundary; inline drawing framing is excluded                                                                       |
| Counted arrays           | Retain source count words where their interpretation matches the modeled row length; otherwise compute the count; existing ten-million repetition limit remains  |
| Separate lengths/repeats | Read the explicit field before its guarded rows; store derives length and uses that computed value for subsequent branches without mutating lazy source fields   |
| Packed ghost count       | Signed i32 word splits into arithmetic high nibble and low 28-bit count; store composes the flag nibble and modeled object count                                 |
| Shadow writes            | Preserve separate native wire occurrences under `field#tag`; existing builders can provide the base field when a shadow is absent                                |
| Runtime normalization    | Keep `field#wire` independently; unchanged runtime projections reproduce it, while edits select a new scalar; native normalization never becomes a fresh default |
| Part caches              | Explicit zero-through-two typed mass/bounds entries; nonempty missing classes fail closed rather than becoming residual bytes                                    |
| Directly owned object    | Decode the complete named body with no new tag/map entry; missing closure fails explicitly                                                                       |
| Fixed native fields      | Exactly 16 bytes per declared field; report owner, field, declared/observed length and completion; no variable opaque body/tail operation exists                 |

The fixed fields are model `f784`/`f7a4`, whose constructor initialization is
recorded in the model ledger, and four GUID field positions in the block-manager
and preferred-map grammar. Their contents remain source/model values. Fixed
width does not prove GUID meaning for the model fields, semantic classification
or a valid neutral value for arbitrary use. No preserved field content becomes
a writer constant.

Ordinary external features retain their measured parent and archive-mode guards.
CMgr's null-reference profile remains unchanged. Config occurrence records require
the concrete owning `moReference_c`, matching `f44`/reference ID, and the exact
`f4f8` backlink. The backlink is checked after the whole root completes because
its containing field is not assigned until the nested read returns. Missing or
inconsistent ownership rejects admission; the codec does not repair it.

## Class descriptor correction

The initial SDK profile assumed schema one for the color-table runtime class.
The first independent process sweep reproduced 9/12 streams and rejected the
three native children at `moFeatColorTab_c schema 0`; this was an SDK admission
failure, not a native application failure.

The pinned `sldmfcu.dll` export
`?classmoFeatColorTab_c@moFeatColorTab_c@@2UCRuntimeClass@@A`, ordinal 4394,
points to `0x3ce6d490`. Its name pointer is `0x3cc6e008`, object size is `0x10`,
and the u32 schema word at `+0xc` is zero. The first 16 metadata bytes have
SHA-256 `12c0061a96c36a4161136c111b5784a593a8cc70eaf41b1071aab8f0c3a95668`.
The already pinned serializer remains `[0x3c7f2460,0x3c7f2667)`, SHA-256
`74de57684ecd82558d92bc20ee43d9f9ea65c8aa2d4d2e998f675a1ee4397e25`.

The metadata-only [descriptor record](ConfigRuntimeDescriptors2026.json) binds
106 exported records across the exact model, MFC-support and archive modules.
103 are serializable; those registered native schema words define the concrete
profile. The abstract component/feature/model-feature records have schema
`0xffff` and remain available only as inherited body grammar, not concrete tag
admissions. No exported runtime descriptor for `moDrViewLabelData_c` was found
in this bounded three-module search; its shared base layout remains available,
without concrete tag admission. `moUnitsTable_c` metadata is owned by the MFC
support module despite the model module's imported serializer entry.

## Actual callers and compatibility

The normal SDK adds `solidworks.typed_configuration_graph` metadata after its
existing reader completes. It reports complete grammar or an explicit unavailable
diagnostic, actual map/header information, and separate manager context. It
always reports `full_linked_graph=false` and
`resolved_body_codec_promoted=false`. Existing semantic projection and read-only
adapter registration remain unchanged.

The real research `ConfigPart.load_config` and `store_config_state` delegate to
`ConfigBridge` on the declared profile. The bridge retains research `Obj` nodes
through the existing node-factory boundary, the original header source record,
map aliases/base and archive flags. Unsupported profiles may still use the old
typed research path, with `sdk_ordinary_config.admitted=false` and the failed SDK
usage/diagnostic kept separately. No production fallback exists. Incomplete
framing or malformed known fields are not silently admitted.

The no-tail diagnostic, early versions, unknown concrete classes, unproved
constructors, inline drawings, nonordinary native DB mode and unmodeled dynamic
subclasses remain outside this profile. Full linked semantic admission, C10,
materials/appearance editability and fresh native writer acceptance remain with
the parent goal.

## Verification

The parent executed the frozen 121-path source overlay independently. All 12
Config streams were literal-equal after SDK read/store, with exact map boundaries
and header aliases, separate CMgr context, 72 malformed rejections and 24 modeled
name/array edits. Both directions reported 153 exercised body schemas and 30
fixed-native-field observations across the cohort. No CAD application was run.

The raw `ConfigSdkVerify02/ConfigReadWrite.json` SHA-256 is
`9d973ae02d67d3c90d42809f1dfeb4c5b0e881ebf76f353fb5b7f0bc73c20649`.
Its source manifest SHA-256 is
`18eaece764c1f612e2f790986f6d63af6c5a9542eeb06abbc252f01ee4ccdedc`.
The final receipt records which subsequent bridge/integration checks actually
passed and binds their sources separately. No earlier result is transferred to
later changed code. The worker ran source/AST, formatting, typing and policy
checks only under the current direct no-local-test instruction.

The subsequent frozen 133-path bridge check reproduced all fields, aliases,
positions and stored maps for all twelve files. Its load union is exactly 158;
store is 153. The independently executed permanent process regression generated
a neutral part/assembly pair under the no-runtime-input-read guard and passed
both real CLIs, normal SDK child metadata and the explicitly unadmitted-tail
case. It added four modeled edit round trips and twelve malformed rejections.

The same source also passed 36 linked Config/CMgr/Resolved stream comparisons
and six MatesList comparisons, with complete phases and no used provisional or
missing schemas. The generic RoundTrip CLI has no MatesList plan; its retained
failed-plan diagnostic earns no acceptance credit. The six successful mate
checks used the dedicated codec with the exact resolved map seed.

The sanitized [receipt](../measurements/2026/SdkConfigGraph01.json) binds those
raw reports, the source overlays, input identities and exact schema unions.
Bridge parity report SHA-256:
`4c22a7c87900d26593c5b00af08dc3d81e0300a5c9fa6120a4d34adca61a3900`.
Linked-core report SHA-256:
`90a23ff457e0168ccc1a42065baea91f1217a56452ab91eeb04858902d06f1fb`.
Dedicated mate report SHA-256:
`0bb64990df44fc3dc5f0ddf81cc03b4b1d6000eeafcc132c3e92efe4946a9f5f`.
These are structural source checks; no fresh vendor acceptance or held-out
qualification follows from them.
