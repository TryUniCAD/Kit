# Ordinary perpendicular mate reader ownership in SOLIDWORKS 2026

The disclosed D01 and D02 source and edited pairs pass the same guarded SDK reader. D02 was released after the D01 rule freeze. PR #121 integrates this reader. The measured evidence covers source readback and exact MatesList re-encoding.

Task `B04-SW2026-MATES-PERPENDICULAR`, owner `assembly_occurrence`, delivery PR #121. Scope is one solved perpendicular mate between two resolved direct occurrences of the same ordinary part, with one fixed occurrence and actual principal-plane references. Dependencies are the current linked ModelHeader/Config/CMgr/Resolved/MatesList codecs, independently loaded child configurations, the existing ordinary wrapper rules and the source protocol. Exit requires independent family source locks, a generative implementation and held-out native open/edit/rebuild/synchronized-save/fresh-reopen acceptance. That exit remains open. [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [RE playbook](../../Playbook/README.md) · [Source protocol](PerpendicularMateSourceProtocol2026.md)

## Source custody

Only D01 under source packet03 was used for this initial method. Its packet SHA-256 is `9fdfff4ee0fc960dbb70ec3058d4ac6652ba5413caf7171aa119d5b4500b4a41`. The synchronized baseline and edited files are independently hash-bound in the [sanitized receipt](../measurements/2026/PerpendicularMateDisclosedRead01.json). The saved native observation manifest has SHA-256 `0d0783ba55f61d192e30b317a54def4784a0941ed4e6e63561e6f9e92bf9fbcd`; the disclosed lock record has SHA-256 `790993adaca4d876db3e3574d7bded68e3474ca937b57f1101283933a073f584`.

Five native process creation identities qualify the before, author, fresh source reopen, fresh edited reopen and after phases. Each public progress record passes, binds that packet, records zero writer output and identifies executable SHA-256 `3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`, version `34.5.2.0604`. The native source has two bodies. Its live edit changes child depth from 9.1 to 14.3 mm and rotates the floating occurrence by 21.7 degrees about the fixed Front normal, preserving perpendicularity. It is an already-valid pose edit, not an invalid-angle solver-correction experiment. Root performed the native phases; the reader work started no native process and accessed no sealed source.

## Exact native framing

The concrete schema-one `moMatePerpendicular` uses the shared `moMate2Geoms_c` body at archive version `19000`. It adds no new current-store tail in the existing shared serializer evidence. The complete MatesList continues the actual resolved object map; a counter alone is insufficient. The SDK overlay supplies the explicit concrete schema/base alias and concrete virtual dispatch entries. Those shared codec registrations also permit exact re-encoding of an already parsed perpendicular source graph. They do not construct a new perpendicular mate from neutral input. Generic tag/map/string/primitive algorithms, generative constructors and public writer admission remain unchanged.

The original `sldmodu.dll` SHA-256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. Perpendicular primary table `0x4cfa2278` and parallel table `0x4cf9fe10` bind the following identical archive slots. [Reproducible numeric bindings](PerpendicularMateReadBindings2026.json) · [Collector](../../tooling/sw2026/CollectPerpendicularReadEvidence.py)

| Slot | Exact target | Existing shared rule |
| --- | --- | --- |
| `+0x3e8` | `0x4bb2a650` | `moFeature_c.SerializeXmlData` |
| `+0x3f8` | `0x4c03e170` | `moNode_c.getIdForXmlDataExtracter` |
| `+0x4b8` | `0x4c17a7b0` | `moConcept_c.SerializeLWData` |
| `+0x4c0` | `0x4c17b570` | `moConcept_c.SerializeResolvedData` |

The inherited bit-8 update getter/setter at slots `+0x230/+0x238` also bind `0x4b28e090/0x4b30f9f0`, matching the separately documented node lifecycle. The receipt records exact module, table and function-fragment identities, not proprietary code listings. The earlier REA attempt met a retained foreign Hopper owner; original-PE inspection supplies these exact bindings. No task-owned Hopper document remains open. [Original construction evidence](PerpendicularMateNativeSource2026.json) · [Lifecycle rule](CoincidentMateLifecycle2026.md)

## Field reconciliation

The shared wire encodings and field order remain owned by their existing codec schemas. The values below are observations of the same D01 design before and after its native edit, never writer constants or captured field programs.

| Owner/field | D01 source → edited | Meaning, confidence and read guard |
| --- | --- | --- |
| Mate `f08` | `26 → 26` | Actual persistent mate ID; independently matches native `IFeature.GetID` and the header allocator. Confirmed source identity |
| Mate `f3b4` | `0 → 0` | Internal alignment, separate `u16`. The native perpendicular command passes zero instead of translating an explicit alignment. Neutral alignment is `unknown`, with the exact internal code retained as an attribute. Confirmed code and source |
| Native `IMate2.Alignment` | `2 → 2` | Different API enumeration. This is observer evidence, not a stored value inferred from `f3b4`. Confirmed source observation |
| Mate `f3b8` | `1 → 1` | Independent `u16` solver result. The overlay admits the measured solved state only; the complete solver domain remains open |
| Mate `f0c` | `256 → 256` | Independently bound feature update bit. It does not represent suppression or solver status |
| Mate auxiliaries | Empty/null ordinary owners, `f488/f490` empty | The overlay retains existing complete-profile guards and rejects auxiliary data |
| Resolved `f410` | Two ordered plane wrappers | Each real `moCompRefPlane_c` reaches a `moChainComponent_c` owned by the actual assembly; its one-hop chain aliases the inherited external record and occurrence backlink |
| Occurrence IDs | `24,25`, unchanged | Independently match native component IDs. Actual child `Default` configuration, file identity, creation fields and update stamps are required |
| Resolved wrapper `f08` | `166 → 194`, both endpoints | Actual child header update, also required at the real occurrence. Derived identity, not a copied parent update |
| Detached wrapper `f08` | `105 → 106`, both endpoints | Actual containing parent header update. The overlay rejects a stale detached epoch and requires Config-0 |
| Resolved `f74/f78/f7c` | `(26,0,0)`, `(26,1,1)` | Actual mate owner and assembly wrapper IDs/order. Shared uniqueness and persistent-ID checks remain active |
| Selected `f3c8` | Keys `0,1` | Separate detached selections, each through a unit component retaining the actual parent owner. They do not replace resolved occurrence references |
| Detached wrapper owner triplet | `(-12345,-12345,-12345)` | Existing unregistered-wrapper sentinel rule, guarded independently of resolved IDs |
| Detached datum reference | `ff0=(-1,2592000)`, `f9c=2/3` | Unallocated anonymous plane with the original real datum ID. Confirmed existing construction rule and source |
| Resolved datum reference | IDs `2/3`, creation epoch `1794529625` | The overlay computes the comparison from the actual child header creation log through the existing `DatumTime` reader; the observed epoch is not embedded in SDK source |
| Principal kind | Front `3`, Top `2` | Derived from the real canonical child datum frame through the existing `ReadDatumFrame`, independent of its display name |
| Detached inline plane | `moRefPlane_c.f08=-1`, `moAbsoluteRefPlnData_c` | Its world point/normal must match both the detached and resolved wrapper. Resolved references retain no inline plane |
| Rigid status `f50` | Resolved `2/1`, detached `0/0`, unchanged | Saved runtime observations only. No cold construction rule or solver transition is inferred |
| Fixed/solve words | `(f408,f400)=(1,4),(0,3)` | Existing independent fixed/solve owners, matching native fixed state. They are not mate alignment or `f3b8` |

The real source endpoint order is Front on occurrence24, then Top on occurrence25. The edited second normal is `(-0.36974675727382933,0.9291325715340562,0)`; its origin stays `(0.1237,0.0181,0.0269)` m. The fixed endpoint normal stays `(0,0,1)`, so their dot product remains zero. The reader independently transforms the actual child datum with the rigid occurrence placement and checks the saved plane cache before checking perpendicularity. Its existing coordinate tolerances remain `rtol=1e-10, atol=1e-12`; the orthogonality residual uses `atol=1e-10`. No tolerance was loosened for this source.

Saved selection text changes its parent display suffix from `Assem1` to the saved parent name. Typed admission uses real identities and geometry; that text change is not an occurrence or datum rename. [Selection-string boundary](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Assembly/SelectionStringsDoNotDefineMateEndpoints.md) · [Alignment enum gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Assembly/PerpendicularArchiveAlignmentHasItsOwnEnum.md)

## Private SDK overlay and verification

The baseline is exact SDK revision `f35eb89a6ba16443f9e987009a7b10b45b114a0b`, 4,238 Python files. Eighteen scoped SDK paths add nine files and change nine existing files; the complete frozen current source has 4,247 Python files. No `Core/Adapter.py` or public registry edit is required. The initial proof freezes these changes in the private overlay. The integration then adopts its exact eighteen SDK paths. Perpendicular generation retains a separate qualification boundary. The historical freeze's `writer_source_changed=false` field refers to that construction/public-writing boundary; the explicit shared codec class admission is part of this reader tranche.

Private source freeze SHA-256 `47aa5d22d3a158653f8b3e8bff35c28a9e2dcd8b44286713028504e8217bfa1d` precedes the later D02 disclosed read. Initial final process receipt SHA-256 is `8727d29c62ce4e092a6ba924ef561ef6edae60a584855e48b6d95ce5eb594d63`; full source-manifest SHA-256 is `2cc14a36c08b397ceca2e45c529fa11ae513fa69d48d38a6456868d4a06abdda`. The [public receipt](../measurements/2026/PerpendicularMateDisclosedRead01.json) has SHA-256 `1e852e42253fde64ad8d31f9da08e7709f8752b9e2721a3e7ed75d29ec0de609`.

The [process coordinator](../../tooling/sw2026/CheckPerpendicularReader.py), [complete linked/public auditor](../../tooling/sw2026/AuditPerpendicularReader.py), [diagnostic preparer](../../tooling/sw2026/PreparePerpendicularReadFaults.py) and [sanitized publisher](../../tooling/sw2026/PublishPerpendicularReader.py) reproduce the record. The proof used 80 fresh Python launches:

- Two actual D01 parent/child audits retain whole mate stream bytes, object-map aliases, empty-list framing and fourteen codec negatives each, then compare normal public endpoints, placements, configurations, fixed anchor and three real child driving lengths with native observations
- Six older disclosed coincident, parallel and positive-distance linked streams retain exact bytes and aliases
- Eighteen old normal/deferred public comparisons and four D01 child/deferred comparisons retain their exact baseline results, including the previous deferred errors
- Twenty-six malformed or contradictory physical diagnostic copies refuse typed admission, followed by one healthy unmodified repacked reader control

The source MatesList is 3,085 bytes, SHA-256 `ffc2c67234252fd2974965cf08eeef92841746c4c3ebc6edb2365fd8b8c4691d`. The edited stream is 3,421 bytes, SHA-256 `f36b2bbbcd7327bb0361aca375b6cf349f983b19ce76c898021e2f390f7ab884`. Both continue map168 through196, reproduce identical bytes and contain no missing/provisional schema or opaque/native-byte field. The larger edited graph includes its actual rotated matrices and longer selection strings; no fixed offset or fixed stream length is assumed.

Diagnostic copies include wrong internal alignment, unsolved state, unqualified feature word, auxiliary text, detached order/owner/datum/epoch/geometry/sentinel, wrong actual owner/mate ID/configuration/datum/creation/kind, duplicate wrapper ID, stale child update, contradictory plane geometry, duplicate mate, trailing/truncated data and wrong map seed. A failed typed attempt retains the already valid legacy inventory with an explicit `unsupported` status, or the ordinary format parser rejects it. No diagnostic is reported as typed success. These repacks are research copies, not generated writer output or native acceptance.

Black, Ruff, strict Mypy, Pyright and steering pass on all eighteen paths. Pyright reports zero source diagnostics and the three existing unrecognized repository setting names. The donor scanner reports no recorded payloads in the 4,247 frozen source files. Remote CI is a separate parent-owned gate.

The reader is intentionally limited to container4/archive19000/schema-one, a complete resolved map and actual child data. `include_brep=False` and `include_tessellation=False` were used; no claim is made about a new B-rep decoder, assembly mass calculation or full CAD conversion. Other perpendicular source layouts, unsolved starts, optional help data, nested/face/axis references, flexible occurrences, mixed mate groups and further releases remain outside this evidence. [Adjacent-release qualification](AdjacentReleaseQualification.md)

## Separate D02 regression after the D01 freeze

Root subsequently released only packet05 D02. The exact disclosed lock record SHA-256 is `bf16c18d8224dd2b03ffa9f484d6b7130ef33f3fe12ba21f3f7698f01d08e105`; its `source_manifest_sha256`, `3ac958f4c1f8c1a7062b7e3750f2fea651da46c0762f585f6a4baca418c27d74`, identifies `SavedAuthor.json`, not the lock record itself. All five source native phases pass with distinct creation identities and both healthy controls. No H slot, source specification or private inspection was read.

The already frozen SDK and auditor pass both D02 source and edited native pairs without any code change. [Separate regression tool](../../tooling/sw2026/CheckPerpendicularReaderCase.py) · [Separate publisher](../../tooling/sw2026/PublishPerpendicularCase.py) · [Sanitized D02 receipt](../measurements/2026/PerpendicularMateDisclosedD02Read01.json)

The native endpoint order is Top on occurrence24, then Right on occurrence25, despite the opposite authored selection order. The actual wire `f410` references and detached keys match that native order. The second occurrence is fixed: its `(f408,f400)` is `(1,4)` and resolved wrapper `f50` is 2; the first has `(0,3)` and `f50=1`. This additional observation confirms that the earlier `[2,1]` rigid-status sequence is not a positional constant. It is not a cold-state construction rule.

Both nontrivially rotated saved layouts keep internal alignment 0, solved state 1, API alignment 2 and zero auxiliary help records. The actual Top/Right principal kinds are 2/1 and child datum IDs 3/4. The source stream is 3,589 bytes, SHA-256 `04667bf015365fbc0fa2b4efe583a9242ce7951abeb5def77e4a3d34676f575c`; the edited stream is 3,757 bytes, SHA-256 `05b51f6f6335dde347b219b31690d9f91fdd405dcb7057d85dd064990cc77191`. Both retain map168→196 and exact typed byte/alias identity with no missing/provisional/opaque fields. Actual ordered endpoints, configurations, rigid poses, fixed state and all three child driving values match native observation through the unchanged reader.

The two-worker regression receipt SHA-256 is `9aade77d515551ccdb2d1d286524895e1d3a2a44e8dec74b3d40eca1814f7d74`, binding the original pre-D02 source freeze and D01 proof. Its sanitized publication has SHA-256 `da4fcbfe0e694db4bea8e8b5f7ab82af04462ac604a98b112687848831a36f37`. The initial D01 receipt and tools remain unchanged. D02 is an additional disclosed regression; genuine held-out qualification and generated perpendicular acceptance remain open.

## Integrated reader

Six fresh workers open the D01, D02 and D03 source and edited pairs on the integrated checkout. Each worker checks exact MatesList re-encoding and aliases, ordered native occurrence and datum references, the fixed anchor, actual component poses and three driving child lengths. The [integrated receipt](../measurements/2026/PerpendicularMateReadIntegrated01.json) binds the eighteen adopted SDK source files and the original rule freeze. The [Packet05 source receipt](../measurements/2026/PerpendicularMateSourcePosition05.json) records both pre-writer held-out locks without disclosing their source contents.
