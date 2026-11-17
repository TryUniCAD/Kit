# Ordinary contextual components and framework string maps

The ordinary version-19000 wire paths for `moContextChainComponent_c` and
`su_CMapStringToString` now have current-build structural definitions. Native
model acceptance and the production promotion of the full body grammar remain
separate requirements. Earlier archive versions retain explicit provisional
owners.

## Identity and evidence boundary

The original images are SOLIDWORKS 2026 SP05.2 build 34.5.2.0604 and the pinned
MFC runtime already used by the framework-count investigation. Native instructions,
private captures and vendor images remain outside the repository.

| Image | SHA-256 |
| --- | --- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` |
| `swccu.dll` | `d5a8a3f3c9e4f108650242dab99ae8f9c9b8edb0e3fd2e04c185964f79d1ba7c` |
| `mfc140u.dll`, 14.50.35719.0 | `88beebf73667ab0d603355f54562aa9cf9316f4d585a40ec93430c6715ffc8d1` |

The worker inspected original PE imports, exports, exception records, class data
and exact instructions with LLVM. The retained MFC LLVM analysis view changes
seven header bytes to select a decoder and hide the empty-name export table.
All fingerprints and extents below use the original unmodified files. The
effective AMD64 MFC export comes from the immutable RuntimeView03 capture and
was independently corroborated in the new mapped-span run. The worker invoked
no target code. Root's separate owned-Python inspection loaded the generic MFC
runtime and inspected its code bytes, with archive methods and CAD APIs uncalled.

## Context component owner and field order

The concrete runtime descriptor at `0x4daf0fd8` names
`moContextChainComponent_c`, records native schema `0x80000001` and factory
`0x4c20e750`. Its base-class getter at `0x4c20e740` returns the chain-component
descriptor `0x4daf0fa8`. The concrete vtable `0x4ce9cb60` binds serializer slot
`+0x28` to `0x4c222af0`.

| Native function | Complete half-open span | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| Factory | `[0x4c20e750,0x4c20e77e)` | 46 | `04e23820630d6a4fd55a44a53c7fed79b9083109eca6d61fdcb6e6519ac681a4` |
| Default constructor | `[0x4b8279a0,0x4b827a06)` | 102 | `714ab8b2c3639a3c4e10b92654b8e5b06df906224d433a6e6583de0b2f180232` |
| Context serializer | `[0x4c222af0,0x4c2231bb)` | 1,739 | `b2145a5bfe81d93a66ac5f55a0bf000258b62c00a32685f7929d4eced499562c` |
| Delegated chain serializer | `[0x4c21b8c0,0x4c21bfac)` | 1,772 | `2168c75b8e3f00d0bc3200969a5e1af384d0aa48040c052725256fd6587758eb` |

The AMD64 exception data directory bounds these complete spans. The context body
includes its failure tails. Its ordinary wire order is as follows.

| Order | Existing field | Wire rule and native sites |
| --- | --- | --- |
| 1 | Base component and chain | Delegate at `0x4c222b70`. The proven 19000 chain body contains its component `owner` tag, `f20` chain tag and unsigned 32-bit `f30`. |
| 2 | `f40` | One typed `moExtObject_c` tag. Ordinary store call `0x4c222c18`; load call `0x4c222c8c`. The selected copied-object store calls the same operator at `0x4c222be3`. |
| 3 | `f48` | Signed 32-bit word for versions at least `0x38d`. Store gate `0x4c222c5b`, transfer `0x4c222c68`; load gate `0x4c222e2b`, transfer `0x4c222e39`. |

The two `f40` calls bind through imports to the typed `moExtObject_c` operators
in `sldarchiveu.dll`. The trailing scalar calls bind to the ordinary signed-long
operators in `swccu.dll`. At version 19000 these operations are active in both
directions. Base and embedded owners retain their existing verified guards and
graph identities.

The factory allocates `0x50` bytes and invokes the default constructor. That
constructor initializes the legacy name pointer at `+0x08` to null, the chain
at `+0x20` to null, the contextual file at `+0x40` to null and state at `+0x48`
to zero. The inherited chain serializer's old-name early return therefore does
not remove the modern chain fields. The shared modern component base does not
read a legacy name. These constructor observations describe runtime creation.
They supply no universal saved default or neutral-state acceptance claim.

## Runtime context and raw wire ownership

The context serializer temporarily changes the chain's runtime owner during
store. It clears that owner when it exists, either the chain has no manager or
the owner's virtual `+0x1a0` returns true, and condition `0x80000000` is absent.
It restores the prior pointer after the delegated chain serializer. With condition
1 and a nonnull contextual file, it creates a temporary `moExtObject_c` copy for
the `f40` tag and retains the temporary in the archive helper's cleanup array.
The raw wire graph owns the selected object identity explicitly.

Store forces runtime `f48` to one when any bit of `0x80000280` is present.
Earlier loads below `0x38d` initialize runtime `f48` to one without reading a
word. A modern load reads the word, then clears runtime `f48` when condition 1
is present, conditions `0x200000` and `0x08000000` are absent, and helper `+0x874`
is zero. Conditions `0x6000`, the internal filed owner and subsequent context
resolution govern later runtime work. Those paths restore owners and can
reconcile external features. They add no trailing archive fields to this owner.

The archive model keeps the actual raw `f48` and `f40` graph node. It reproduces
their wire values without applying runtime normalization or cloning them a second
time. A fresh builder still has to model its selected constructor, helper state
and canonical store behavior. The existing ordinary occurrence constructor rules
remain the builder authority.

[Prior chain/base proof](PlanarMateReferenceChains2026.md)

[Occurrence construction](OrdinaryOccurrenceConstruction2026.md)

## String-map dispatch and framework body

`swccu.dll` export 795 at `0x31a376d0` is the ordinary wrapper for
`su_CMapStringToString::Serialize`. Its complete eleven-byte leaf has SHA-256
`cb14f03d6d416c8ca84add01cfd920cd126b3ffe96f61146e5687406772bbd27`.
It returns without moving fields when native archive mode bit `0x10` at `+0x20`
is set. The clear branch reaches thunk `0x31a4c76d`, IAT `0x31a504b8`, importing
MFC ordinal 12804. This mode flag is distinct from research condition words.

The immutable RuntimeView03 mapped export table binds ordinal 12804 to AMD64
entry RVA `0x6bf870`. Its exact fourteen-byte fast-forward sequence has SHA-256
`734790583a36f03cea1366974c1f34bbbcc22b3724865c52b7058827d47f1f20`.
The relative target is RVA `0x5cca60` in the CHPE ARM64EC range. The raw ARM64
export RVA `0x195790` is a separate implementation and supplies no target identity
for this import.

| Reached ARM64EC function | RVA span | Bytes | Original and mapped SHA-256 |
| --- | --- | ---: | --- |
| Map serialize | `[0x5cca60,0x5ccc60)` | 512 | `55c4262d37a701fbb4aa9b92c69ffe91f9439bf3e799b2bd731ec10c020cfcfc` |
| Wide string read | `[0x35b750,0x35b9ac)` | 604 | `a69b336e63174fac8a1e8852f062b8b2dbf0dc03f797347537668457c357151d` |
| Wide string write | `[0x35b9b0,0x35ba00)` | 80 | `c95a956ba1c34a4473ed8d295d878bcc62ad14ea9bffabdd3eb4066a7ef1e526` |
| String-length read | `[0x556330,0x556564)` | 564 | `39c3f838fe3fff276cbce10e2f32c885ce446d6c86699e77a55b380c06bfe811` |
| String-length write | `[0x556570,0x55695c)` | 1,004 | `71d0f2b6c50cca434fd5bba1caca2025a937d514619b4f1ce98117662fb51500` |

Original ARM64 exception records and xdata length fields, or the writer's packed
unwind entry, bound every span. The matching metadata and hashes are retained in
the JSON evidence. These ranges include complete bodies and their in-range
failure tails or literal pool.

The map tests archive load bit 0. Store calls the already-proven framework
WriteCount at `0x180557980`, then traverses its buckets and associations. Each
row emits the key string followed by the value string. The two wide writer
calls are `0x1805ccac8` and `0x1805ccad4`. Load calls framework ReadCount at
`0x180557b30`, then reads two strings at `0x1805ccb70` and `0x1805ccb7c`, uses the
first for map lookup/insertion and assigns the second to its value. There is no
additional class tag or owner payload around this embedded map.

The shared schema preserves keys `n`, `items`, `k`, `v`, ordered rows and the
existing repetition limit. It uses `MfcCount`, with u16 then u32 then u64 escape
grammar, independently of the vendor count codec. Canonical Unicode map strings
use the existing shared CString framing within its nonnegative signed-32-bit
unit domain. MFC's additional length aliases retain their explicit unsupported
boundary. The source code introduces no map values, defaults or opaque spans.

[Framework count proof](MfcCountArchive2026.md)

[CString framing boundary](CStringArchive2026.md)

## Classification and verification

`VisualRefs` selects the verified context-component body through its existing
version-19000 helper. Other versions pass through a provisional owner.
`MfcMaps` likewise selects the ordinary version-19000 framework string-map body,
while `ConfigPart` retains the former provisional representation under an
explicit unverified-version owner. Both directions preserve the same field keys.
DB archives and fresh map-population semantics remain outside these declarations.

Root's mapped-span inspection ran from committed source
`3e119ff913c5229e8a66a460426e54208a7438cd`. The AMD64 process and effective
module view passed identity checks. Ordinal 12804's resolver equaled its mapped
export, and all five complete captures were literal-equal to the pinned raw
bodies. The worker independently rehashed those captures. The probe released its
owned MFC reference and recorded archive invocations and native acceptance false.

The disclosed A17–A19 and three generated pairs retain exact Config, CMgr,
Resolved and mate bytes. Their six typed projection CLI outputs remain identical
to the pinned prior implementation. Strict source admission passes the 36 selected
Config/CMgr/Resolved streams and the six mate streams through their existing
separate owner entry point. Each reached load/store snapshot has an empty
provisional and missing inventory. The full production body loader remains the
next implementation dependency.

The first private strict-run attempt requested MatesList from RoundTrip's plan
table, which has no mate plan. It was retained as a command-setup failure. The
final check uses RoundTrip's supported three streams and the actual AssemblyMates
reader/store for the separately framed mate lists. It changes no stream plan or
qualification requirement.

The process receipt and final source hashes accompany this record. Existing
native discovery controls established source custody. The current native maps
in these controls are empty. This work proves their archive grammar and effective
code identity, while populated-map model behavior, constructor state and held-out
writer acceptance need their own controlled measurements.

[Sanitized native and process evidence](../measurements/2026/ContextAndStringMapArchive01.json)

The governing criteria retain “There are two acceptable stopping conditions.
The first is success under every criterion on this page. The second is the end
of the available context.”

[CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md)
