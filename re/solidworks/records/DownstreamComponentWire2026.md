# Downstream component edge and vertex bodies in SOLIDWORKS 2026

**The selected ordinary version-19000 component wire bodies are statically bound. Complete recursive stream replay and native acceptance remain unqualified.** No CAD file or vendor process was opened for this tranche.

Task `B04-SW2026-DOWNSTREAM-COMPONENT-WIRE` belongs to `configuration_header`. Root owns the body codec, native oracle and PR #121 publication. The [numeric source ledger](DownstreamComponentWire2026.json) and [source-only receipt](../measurements/2026/DownstreamComponentSource01.json) retain exact original modules, full function bounds, class descriptors, Serialize cells and primitive bindings. The field rules extend the direct downstream archive grammar. [Archive grammar](DownstreamIdArchiveGrammar2026.md)

## Authority and dispatch

Original model DLL SHA256 is `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, preferred base `0x4b140000`. Original helper, geometry and archive DLLs are pinned separately in the ledger. No proprietary bytes or instruction listings are included.

| Concrete owner | Runtime descriptor | Primary table | Serialize target |
| --- | --- | --- | --- |
| `moCompEdge_c` | `0x4daddff0` | `0x4ce8f370` | `0x4bba5b20` |
| `moCompCompositeEdge_c` | `0x4daddf00` | `0x4ce8ef18` | `0x4bba54e0` |
| `moCompVertex_c` | `0x4dade260` | `0x4ce917c8` | **`0x4bba46c0`**, the exact common BEnt body |
| `moCompBEntRef_c` | `0x4dadde10` | `0x4ce8eac8` | `0x4bba46c0` |
| `moCompRef_c` base | `0x4cf68440` | `0x4ce90168` | `0x4bba6ed0` |

The concrete classes have runtime schema word `0x80000001`, ordinary wire schema 1. The CompRef base descriptor has schema `0xffff` and no CreateObject. Base calls do not emit another archive class/object header. Vertex's runtime `f128` is initialized but does **not** add a vertex wire word.

`moCompEdge` calls CompositeEdge, which calls BEntRef, which calls CompRef. CompRef calls `su_CObject::Serialize` at `swccu!0x31a3f030`. The call emits no ordinary body when archive bit `0x10` is clear. Its DB branch remains separate. The current tables and original exports establish the 2026 identities.

## Downstream eligibility is not an empty-body branch

BEntRef constructs the helper and checks whether serialization is allowed **before** calling the base. With a nonnull helper model at `+30`, it requires `IsKindOf(moFiledConcept_c)`. With a null model, eligibility comes from `hasCondition(0x02006607)` or helper integer members `+87c`, `+898`, `+8a4`, `+8b8` or `+8bc` being nonzero.

The last member is independently named `SerializingDownstreamIdData` by getter `0x3c778630` and setter `0x3c77bfd0`. Its direct test at `0x4bba474a` reaches `0x4bba4757` on the enabled path. Failure reaches **`0x4bba4d99`**, the nonreturning error tail through MFC ordinal 2342, followed by `int3`. An initial work-in-progress “empty body” interpretation was refuted by this complete tail inspection. The flag does not bypass a supplied model of the wrong kind.

The helper's `hasCondition` at `0x3c7ac130` returns `condition_word & mask` for a nonzero mask. With mask zero it tests equality to zero. Thus nonzero masks test any overlapping bit, not inclusion of every bit. The selected ordinary standalone profile has condition word zero, a valid actual model, downstream flag 1 and no adding-configuration fixup.

## CompRef base at effective version 19000

All scalar words are little-endian. The order is:

1. Archive object at `f58`. The actual component uses the generic `CObject` operator.
2. i32 `f68,f18,f1c,f20,f30,f70`.
3. i32 `f84`, followed by the embedded `moOldRef_c` body at `f88` when nonzero. Current native store explicitly forces `f84=0` before writing it.
4. i32 `fa0`, u32 `f34`, i32 `f48`, then four i32 words `f90,f94,f98,f9c`.
5. i32 presence, optional `moFacetedData_c` archive pointer at `fb0`.
6. i32 presence, optional CString `fb8`.
7. i32 presence, optional embedded `moCompRefInfo_c` virtual body at `fc0`.
8. i32 presence, optional embedded compact `mgXform_c` at `fc8`.
9. i32 presence, optional CString `fd0`.
10. u32 `f4c`, present from version `0x3ef6`.

The fixed scalar part is **80 bytes**, excluding the `f58` pointer, optional payloads and outer archive framing. The native store computes the five presence words from pointer nonnullness as 0/1. A present empty CString is distinct from a null CString owner. Embedded bodies above have no extra outer object tag. All per-field call addresses are in the ledger.

This is the selected current body. Current store writes fields for the current version while load contains historical gates. It does not justify a symmetric older writer or special nonzero-condition handling. Raw-wire preservation must not apply native store normalization to `f84` or presence words.

## Common BEnt suffix and vertex

After CompRef, the version-19000 suffix is:

| Order | Field | Representation |
| --- | --- | --- |
| 1 | Alias presence | u8 from `getAlias(NULL,false)` |
| 2 | `f08` alias | CString only when that byte is nonzero |
| 3 | `fe8` entity reference | Archive object pointer in either alias branch |
| 4 | `ff0` | Typed `moExtObject_c` archive pointer |

With no alias the reader explicitly checks a nonnull `fe8` against `moBEntRef_c`. The alias branch has no equivalent local RTTI check. Semantic edge/vertex constructors take the corresponding real `moEdgeRef_c` or `moVertexRef_c`. A null raw pointer can be consumed, but it does not prove a usable reference. The reader increments the referenced runtime refcount and performs owner/helper callbacks after consuming the wire fields.

`getAlias(NULL,false)` requires a nonnull alias pointer and nonempty text. An empty present alias or an arbitrary nonzero raw presence byte therefore need not survive a native save byte-identically. Raw replay preserves the presence word. Fresh construction derives the word from alias presence.

`moCompVertex_c` directly reuses this complete body. It must not be treated as a zero-field record merely because its most-derived class has no additional suffix.

## CompositeEdge suffix

At version 19000 the suffix always emits i32 flags `f188`, two embedded three-double points `f158` and `f170`, u32 `f18c`, a fixed signed i32 count, then that many ordinary archive CObject pointers from `f130`, in retained array order. These fixed fields occupy **60 bytes**, before row pointers.

When `(f188 & 6) != 6` and `(f188 & 8) != 0`, two more pointers follow: `f190` and `f198`, both constrained to `moCompCompositeEdge_c` and therefore permitting its actual subclasses. The generic row array has no corresponding concrete class hint. Counts, links and aliases come from the modeled graph. The archive writes row references and their count. A bounded codec should refuse negative or impractical counts.

The native store first calls `0x4b7dce00`. If flag 4 is set, drawing/view/facet validation may clear it, reset `f18c=0` and runtime `f1a0=-1` before emission. Full neutral derivation of that retained view/facet branch is not closed here. A raw codec does not perform this mutation. Load first supports flags at `0xa1a`, points/rows for flags 6 or from `0xfa3`, and the conditional pair from `0xabc`. All selected points and rows are present at 19000. These gates do not create an older-store qualification.

## Edge-only tails and identity domains

With ordinary condition word zero and a part model, `moCompEdge_c` adds **no fields** after CompositeEdge. Special conditions `0x21`, `0x200001` or `0x8000001` append i32 `f1ac,f1b0`. The read gate is version `0xa4a`. Those contexts remain unqualified for generation.

A drawing model appends four i32 words `f1b4,f1b8,f1bc,f1c0`, supported on load from `0x3352`. Outside detailing mode, store resolves a real `gcEdge_w`, calls `getDownstreamIdFromEdgeAttr`, then calls `gcEnt_w::getNodeId`, and passes **that node ID** to `setRefEntityPersistantID(3,node_id)` at `0x4bba5c6d`.

The exact setter is the **11-byte** leaf `[0x4b807270,0x4b80727b)`: it writes `f1b4[index]=value`. Index 3 therefore writes `f1c0`. The earlier downstream getter's return is not the argument stored by this call. This is a concrete separation of kernel node ID and allocated downstream ID. In detailing mode native writes the retained four words without that live-edge update. No drawing/native-order acceptance follows from this source fact alone.

## Constructor-time inputs and defaults

The default CompRef constructor `0x4b7e8390` explicitly clears its scalar state and optional owner pointers, sets `f90/f94/f98/f9c=-1`, and obtains `f4c` from the current-file-version getter. A component-taking constructor calls the actual component's virtual clone/copy boundary `+158` and stores the returned component at `f58`. The archive does not authorize replacing that result with an invented shared-pointer alias.

BEnt's semantic constructor `0x4b7e5dd0` stores the actual supplied entity reference at `fe8` and starts `ff0` null. It derives CompRef flags from the entity reference's runtime `+e8`. The rules transfer bit 4 or bit `0x10`, map `0x1000` to `0x2000`, and transfer or clear `0x40`. If the referenced actual body pointer at runtime `+80` is nonnull, `gcBody_w::getAtomId` supplies **both `f18` and `f1c`**. Both fields therefore retain the atom identity on this construction path. Special model branches can also assign `f48`.

Both composite constructors set flags/`f18c` to zero, child pointers null and runtime-only `f1a0=-1`, construct the owned row array, and call the default point constructor for both points. Original geometry leaf `[0x31dd3a20,0x31dd3a31)` initializes all three coordinates to zero. A deliberately empty modeled row list gives count `len(rows)=0`. The MFC ancestor body remains outside this proof. Edge factories/constructors clear the later edge fields before resolution/save updates. Vertex initializes `f128=0`, a runtime-only field here.

These are format/constructor facts, not captured defaults or a complete writer. A meaningful fresh reference still needs the actual generated component, matching entity reference, body atom, flags, source intent and any supported optional owners. No vendor-save row, kernel handle or native ID may be borrowed as a seed.

## Remaining evidence and verification

The nested pointers use ordinary class/object framing and aliases from the standalone map. Full recursive closure of `f58`, entity refs, optional owners and generic array rows must be admitted individually. Saved-cache replay and held-out evidence remain open. [Standalone map](DownstreamStandaloneMaps2026.md)

[The original-image verifier](../../tooling/sw2026/downstream/VerifyComponentWire.py) verifies full module hashes, every retained complete code interval, all five runtime descriptors and all five actual Serialize cells. It emits metadata only and executes no vendor code. The governing [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) and [RE playbook](../../Playbook/README.md) remain unchanged. The source-only verification covers the scoped native bodies above.
