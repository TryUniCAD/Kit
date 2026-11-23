# Ordinary Hole Wizard archive ownership, 2026

Task `B04-SW2026` in PR #121. This record binds the ordinary Hole Wizard model classes and their serialized owners in SOLIDWORKS SP05.2. The [receipt](../measurements/2026/HoleWizardArchiveOwners01.json) pins original PE function spans and the disclosed Git corpus. The [source protocol](HoleWizardSource2026.md) has passed installed-metadata verification. Native source capture, a complete typed read and writer construction remain open.

## Exact owners

The original AMD64 `sldmodu.dll`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`, has preferred base `0x4b140000`. Each row binds the current [2026 map](../../data/Serialization/SerializeMap2026.json) to its actual vtable cell at `+0x28`, original exception-directory bounds and RTTI.

| Runtime class | Serialize address range, end exclusive | Confirmed role |
| --- | --- | --- |
| `moHoleWzd_c` | `0x4bb137f0–0x4bb152ac` | Ordinary Hole Wizard history. Its base call at `0x4bb1381d` reaches `moBaseHoleWzd_c` |
| `moBaseHoleWzd_c` | `0x4b3c92c0–0x4b3c933c` | Shared Hole Wizard base. At `0x4b3c92e1` calls `moBodyFeature_c::Serialize`. Its extra word is gated to versions `0x2f46..0x2f67` |
| `moSketchHole` | `0x4bb1f380–0x4bb1f499` | Simple hole, with `moCut_c → moExtrusion_c → moSingleSketchFeature_c` lineage |
| `moHoleWizardInfo_c` | `0x4b400b70–0x4b40199f` | Separate `su_CObject` role reached by the optional radial display `f10a8` in the existing grammar |
| `moAdvHoleWzd_c`, `moHoleSeries_c` | `0x4b39f0a0–0x4b39f150`, `0x4bf45c70–0x4bf46289` | Distinct advanced and series variants, outside this scope |

The ordinary RTTI chain is `moHoleWzd_c → moBaseHoleWzd_c → moSketchedFeature_c → moBodyFeature_c → moAtomFeature_c`. The existing [research grammar](../../tooling/sw2026/serial/defs/ResolvedFeatures.py) already describes the ordinary record. Its current-version base flattening matches the observed call path. Source reachability, current descriptor schema, optional owners and the complete record still need verification against native 19000 bytes.

## Model bindings

| Owner | Static finding | Source qualification |
| --- | --- | --- |
| `moHoleWzd_c.f814` | Signed archive word. The exported `getExitType` at `0x4b2bceb0` returns that exact member as internal `gcEndSpecType_e` | Partial. Compare the retained value to both disclosed through-all definitions before deriving an enum rule |
| `f818`, `f820` | The store path uses the object and f64 operators at `0x4bb138e9` and `0x4bb138fa`. The typed constructor at `0x4bf70ae0` stores its reference and double arguments there. The archive has a reference-substitution gate | Partial. The retained end/reference and double values require current sources. The selected placement face must be joined through its actual support owner |
| `f830`, `f838` | Two ordered CStrings. `getDiameterDepth` compares the actual model-dimension handle name to `f830` at `0x4bf85fa1` and `f838` at `0x4bf86035`. Those matches select the diameter and depth handle roles | Partial. The selected profile, handle name and original-value override must be measured. No fixed `D1` label follows |
| `f84c`, `f850` | The ordinary store emits separate signed words. Diameter and counterbore helpers branch on `f84c`. The actual `setHoleType` at `0x4b291f00` binds `f850` to internal `moHoleWzdHoleType` | Partial. Compare both internal fields to native subtype and catalog getters in the measured cases |
| Position and section | The ordinary vtable resolves `+0x2660` to the position-profile accessor and `+0x2668` to the section-profile accessor. Their shared profile dispatch `+0x1a58` receives zero and one respectively. Both accessors resolve the sketch through the resulting profile object at `+0x368` | Partial. Bind the actual two profile objects, position geometry, native external face references and workpiece owner in the current saves |
| Section dimensions | The ordinary subtype helpers can retrieve section-sketch display list indices 0 for through diameter, 2 for counterbore diameter and 3 for counterbore depth with head clearance. They read each actual display's model handle and its value. A separate branch consults `fAD8` through vtable `+0x2740` and nonzero scalars `fB08`, `fAE0` or `fB40`. `GetCounterBoreDepth` conditionally subtracts `f878` | Partial. Confirm the selected branch, real handle and physical geometry for each disclosed original and edit. The memory fast paths provide no generative defaults |

`f814` and `f850` belong to separate native enums. The registered COM `EndCondition` and `Type` numbers in the [API receipt](../measurements/2026/HoleWizardInstalledApi01.json) describe the Automation properties. Their relationship to stored internal values needs a current native source measurement. Catalog text, slot/thread branches, partition publication and the populated radial callout still need independent evidence.

## Disclosed file boundary

The scanner reads the pinned tracked Git objects through the deterministic research corpus helper and the production container and XML readers. It found 263 SOLIDWORKS part files, including 205 at archive 19000, one at 18000 and 57 at 14000. No 19000 file has a framed new class descriptor or keyword role for the scoped Hole Wizard classes. Twenty-one version-14000 parts have ordinary `moHoleWzd_c` descriptors in `Config-0-ResolvedFeatures`. The older corpus also contains 21 parts with a Wizard keyword role and four with advanced Wizard descriptors. Historical authorship and current source behavior remain unverified.

The exact historical camshaft contrast has SHA-256 `73f0b499c5829b5bfbdcdbb0700eee22e97c7ad6dc0a4d78c177c4d45ff5aa2c`. In its resolved stream the schema-one descriptor starts at offset 200524. Its KeyWords row is `HoleWizard` ID 221. The ordinary deterministic offline CLI emitted the corresponding feature as a `NativeFeatureDefinition`, with one profile ID 220 from the index and no driver IDs. The full read produced 434 unresolved items and `portable_complete=false`. Two fresh invocations on `cd20b8ea0c17ee29d48e1ee767f836be8e0fe4f5` reproduced the receipt SHA-256 `4563afce51c44634aec036e7e7b282517cacec38a9bcbc47158538557b3cd61c` and neutral SHA-256 `595e0fef93d0d39fc857570c81df0be56eec461da92e83609f6559d5920d84a3`. This is a historical control with no prospective family held-out credit.

The current [heuristic decode](../../../src/convert/adapters/solidworks/Core/Native.py) fills a literal termination code and gets its single child from XML. Its [detail builder](../../../src/convert/adapters/solidworks/Core/Reading/ReadAdapter.py) requires diameter and depth for the shared [simple hole definition](../../../src/interchange/Features/FeatureKinds.py). That representation has no Wizard catalog, counterbore dimensions or separate section and placement owners. A future typed projection needs the actual wizard subtype, catalog, end semantics, body selection, geometry and stable driver roles.

## Reproduction and next acquisition

```sh
python3.14 -I -B re/tooling/sw2026/hole_source/InspectHoleOwners.py \
  /absolute/path/sldmodu.dll \
  --check re/solidworks/measurements/2026/HoleWizardArchiveOwners01.json
```

The model DLL remains outside Kit. The scanner binds the whole input digest and exact PE function extents without exporting instruction or vendor payload bytes. The [static read](../../tooling/sw2026/hole_source/InspectHoleOwners.py) records a sanitized receipt. LLVM supplied bounded native instruction evidence after the shared REA bridge reported unresolved cleanup on its previous Hopper document.

Run the prepared native source bracket first. Compare the exact original and one-property edit for each design. Locate IDs and aliases across `KeyWords`, `Config-0`, `Config-0-ResolvedFeatures`, the header map and the owned partition. Feed new independent guest-authored cases into a prospective source lock only after the two disclosed cases establish the authoring route. Seal the neutral intents and actual native source hashes before starting any writer. Keep the protected payloads and observations guest-local. A future writer must generate the selected model, rebuild and perform independent geometry and live edit checks against those locked references.
