# Ordinary part system-tree projection in SOLIDWORKS 2026

Task `B04-SW2026-TREEPROJ`, owner `configuration_header`, delivery PR #121.
This slice depends on the linked version-19000 reader, the ordinary part
constructor and the existing [native part lifecycle](SdkBlindPartNative2026.md).
Its exit condition is a stable modeling timeline for the disclosed fresh/save
pair, an explicit presentation surface with honest identities and retained
persisted state, and process coverage for preservation boundaries.
The public writer remains disabled. The broader CAD goal remains unfinished.

## Cause and observed ownership

The original reader exposed 19 modeling rows for the fresh SDK part and 27 for
its native edited save. Both typed resolved streams contain the same 19 roots.
The controlled native lifecycle records the same 25-row COM tree for the fresh
and saved case.

The eight additional legacy rows do not represent eight new modeling steps:

| Owner/path | Fresh source | Native saved source | Interpretation |
| --- | --- | --- | --- |
| `moDetailCabinet_c.f60.list.items` | Empty | Two `moNotesAreaFtrFolder_c` nodes | Cabinet-owned note-folder head and end partner |
| Actual model `f1e0` / `moEnvFolder_c.f60.list.items` | Empty | One `moAmbientLight_c` and three `moDirectionLight_c` nodes | Environment-owned light presentation |
| Config root `f1018` | Absent | Empty inline `moSheetMetalMaster_c`, stored node ID -1 | Direct configuration state, not a new root |
| Config root `f13f8` | Absent | Empty `moPrtExplViewManager_c`, stored node ID 31 | Direct empty manager outside the measured feature UI |

The saved note IDs are 29 and 30. Light IDs are 25 through 28. These are
observations from the disclosed source, never production constants.
The cabinet moves from its ordinary construction position to immediately after
the document folder in the measured native presentation.
The environment is a shared Config/resolved alias; its saved members belong to
Config, not to a nearby resolved byte span.

The keyword cache also changes type spellings on save. In particular, it calls
the origin a `Sketch`, which changed the public neutral kind even though its
typed class remains `moOriginProfileFeature_c`. The admitted profile now derives
root type labels from actual typed classes and retains the original cached label
in `native_properties.solidworks_cached_type`.

## Native authority and confidence

The [reproducible source facts](SystemTreeProjection2026.json) pin original
SP05.2 modules and instruction-range hashes. The independently authored collector
is [CollectSystemTreeEvidence.py](../../tooling/sw2026/CollectSystemTreeEvidence.py).
No vendor listing or native binary is included.

| Source | Rule | Confidence and limit |
| --- | --- | --- |
| `sldmodu` `0x4c013af0`, `MakeNotesAreaAnnotationViewIfNeeded` | Checks the model context and existing notes area, finds the actual cabinet, then inserts the notes-folder pair into that owner | Confirmed source ownership and observed ordinary pair; arbitrary annotation populations remain outside this projection |
| `0x4bec0970` and `0x4bebfc20`, folder insertion | Creates a notes-folder head and delegates paired registration to the feature-folder owner | Confirmed for the ordinary pair |
| `0x4bec9e10`, `makePartner` | Stores reciprocal `f388` links and clears partner `f37c`; the head and end are distinct objects | Confirmed and checked against both saved nodes |
| `0x4becc360`, `registerToModel` | Registers nodes and names the end using `%s___EndTag___`, with a separate collision-number form | Confirmed format vocabulary; arbitrary unique-name collisions are not predicted |
| Notes name helper `0x4bec5f40` and English resource `0x73a9` | The base label is `Notes` | Confirmed vocabulary, English only |
| Light base-name helpers `0x4bc0cbb0` / `0x4bc0cbc0` and resources `0x3142` / `0x3140` | Base labels are `Ambient` and `Directional` | Confirmed vocabulary, English only |
| `0x4c019c60`, `createDefaultLights` | Obtains the named `Default` settings collection through session `Environment` and virtual slot `0x188`, then creates and attaches one light per actual entry | Confirmed that multiplicity and attributes come from session settings; a universal fixed four-light rule is refuted |
| Actual typed owner collections and the existing controlled native trial | Name, API type, parent and order match the measured 25-row ordinary presentation | Confirmed comparison for the disclosed pair; the universal insertion, caption and session-default policies remain partial |

The REA resource inventory is also bound by
`ev_7ba15aa4e0caa4fa740e4ce8f23a313101fe8cf32a87cec2780d85ee9a3c363e`.
The shared Hopper bridge refused a foreign retained session. The task closed its
metadata target and used original PE/LLVM inspection. No unrelated Hopper
process or document was closed.

The official [2026 Lighting help](https://help.solidworks.com/2026/english/SolidWorks/sldworks/c_Lighting_Overview.htm)
independently defines the standard lighting profile as one ambient and three
directional lights and states that scenes set the defaults. The implicit role
cardinality declares that documented presentation profile; it does not derive a
constant from one saved part. The pinned collection loop explains why the same
cardinality must not be assumed for arbitrary settings or authored scenes.

## Public representation and admission

`solidworks.typed_resolved_semantics.native_tree` contains the presentation
profile. It does not change the public neutral schema.

- Root rows use their actual native IDs and typed object owners
- Persisted note/light rows use actual IDs, containment, fields and object spans
- Implicit defaults use owner-role identities such as
  `sldprt:system:9:light.ambient`, with `native_object_id`, state and object span
  all null
- Empty direct managers retain their class, stored node ID, complete typed field
  state and exact configuration owner field; the inline master receives no
  invented object offset or archive-map index
- Runtime error, warning and suppression states are not inferred from raw flags

The stable timeline requires the concrete schema-one part, ordinary Config-0,
the measured single-profile blind-boss root sequence and actual environment
alias. The cabinet must occupy one of the two disclosed ordinary positions.
Every removed legacy row must bind to the actual default owned collection or to
an empty direct configuration helper. No generic caption or negative-ID filter
exists.

A custom layout, renamed/nondefault system children, populated manager, owned
dimension, unknown cached member field/type, authored helper caption or unmatched
legacy row leaves the existing timeline intact and sets
the presentation status to `unqualified`. A current unqualified research profile
that places `moNotesAreaFtrFolder_c` at top level is not promoted as a markup
folder. Older archive versions retain their existing reader path.

The English implicit profile matches the disclosed oracle session. It does not
claim the current application settings are encoded in an empty owner.
Arbitrary session policies, authored caption normalization, custom layouts,
runtime status flags, full native-tree parity and full linked semantics remain
explicitly unqualified.

## Verification and retained limits

The [reader receipt](../measurements/2026/SdkSystemTreeProjection01.json) binds
the paired process observations, source proof and integration execution.
The audit runner is
[InspectSystemTreeProjection.py](../../tooling/sw2026/InspectSystemTreeProjection.py).
It verifies input hashes against the existing native receipt, starts fresh public
SDK reader processes, compares the 25 name/type/parent rows in order, checks live
depth and actual persisted ownership, and confirms source immutability.

The modeling identity, name, neutral kind, type, order, dependencies, sketch and
parameter identities match across the fresh/save pair. The depth changes as the
native edit requires. The original 19/27 observation remains historical in
`SdkBlindPartNative01.json`; it is not rewritten.

The integration suite passes 15 child-process launches. It constructs two independent neutral prisms through the
guarded SDK factory, preserves three unowned rows resembling system helpers,
preserves an authored folder permutation and caption, and reads the older
version-18000 control through the real public API. The existing typed-depth,
stale-keyword and unsupported-tail process regression remains in the check.
The paired audit adds two public SDK reads, 150 ordered presentation-field
comparisons and 293 persisted scalar/partner checks. Three additional private
reader-input mutations of the disclosed save check unknown owned-member fields,
unknown owned-member type and an authored helper caption. Each retains the
existing 27 rows and the changed source metadata, rather than silently filtering
it. These mutations are reader controls, not generative writer artifacts.
No unit test, vendor process or held-out input is used.

This is a bounded reader projection, not a writer qualification, a complete
native feature-tree model or a new held-out acceptance result.
