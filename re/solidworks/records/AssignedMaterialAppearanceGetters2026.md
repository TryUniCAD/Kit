# Read-only assigned-material appearance getter packet

The protocol binds the two disclosed material A saves to the typed archive
evidence at revision a84a6578041643558e38c12910d405f24150babd. They share the
same native catalog identity 258 and selected-body SI density 2700. The
typed live part and selected holder have render IDs 7 and 7 on
D01 Author, and 9 and 8 on D02 Swap. The archived model color, classic
primary color and DSPBR albedo differ across the two saves. D01 separates
all three colors and is the discriminating observation. D02 tests the
different live and holder IDs and has overlapping color predictions.
[Archive receipt](../measurements/2026/AssignedMaterialAppearanceRead01.json)

| Disclosed phase | Original in retained NativeSourcePacket03 | SHA-256 |
| --- | --- | --- |
| D01 Author | Inspection/D01Corner/Author/Original.SLDPRT | 6f3683065b2e401812a52c03e8c9913d8ea76ff82444dd975a174977f3b5740f |
| D02 Swap | Inspection/D02Center/Swap/Swapped.SLDPRT | e1c79ba4b22508f465ee624a6fe2b41f04f5efdf60012c0ef909cbed1195ec23 |
| Both bookends | Control.SLDPRT | c0472f9f42bf473a9073adb997180040b7767dfae93310610f77cff9509bec57 |

The packet reuses five tools from NativeSourcePacket03, the prior passive
dialog observer, and a new standalone guest worker. It contains a job
manifest and seven Python files. The CAD files stay at their exact
disclosed source locators. The job pins their sizes and hashes, the
healthy ten-process disclosed author result, the two previous control
receipts, and predictions derived from the committed typed archive
receipt. The installer preflight checks the executable, three owning
modules, registered 34.0 API/constant libraries, requested invocation
shapes, and the specific-display-state selector. Every launched phase
also verifies the live x64 executable, version 34.5.2.0604, process ID
and creation time, clean opening, actual document identity and
write mode. [Installed fingerprints](../v2026/Manifest2026.json)

## Observations and interpretation

- The actual active configuration must be Default, with the matching
  sole display state, before and after observation. The first returned
  display state is active, and its API-returned name is passed to the
  documented specific-state enumeration. [Active display state](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IConfiguration~GetDisplayStates.html) [Specific-state renderer](https://help.solidworks.com/2024/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~GetRenderMaterials2.html)
- The part legacy property uses the exact IPartDoc getter already
  exercised in source authoring. Its nine slots retain RGB, ambient,
  diffuse, specular, shininess, transparency and emission. The
  IBody2 getter is scoped to the actual sole visible solid and is
  documented for a body other than the base body. A null, all-negative-one
  or nonnumeric reply is recorded as its own shape. Only a nine-value
  vector contributes numerical comparisons. A base-body observation
  leaves inherited body appearance unqualified. [Legacy property values](https://help.solidworks.com/2019/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IPartDoc~MaterialPropertyValues.html) [Body getter scope](https://help.solidworks.com/2020/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IBody2~MaterialPropertyValues2.html)
- Physical identity comes from the typed part and body assignment
  getters and independent selected-body IMassProperty2. The report
  distinguishes the assigned part material from the empty explicit body
  material. Rendering is measured once after the legacy observations.
  Every returned render material records its actual attached entities,
  color, roughness, public ID pair and resource locator. Attachments are
  resolved only through IUnknown identity against the opened model and
  its actual solid. An empty enumeration or unresolved attachment
  remains visible. [Render attachment](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IRenderMaterial~GetEntities.html) [Public render IDs](https://help.solidworks.com/2023/English/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IRenderMaterial~GetMaterialIds.html) [Primary color](https://help.solidworks.com/2025/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IRenderMaterial~PrimaryColor.html) [Roughness](https://help.solidworks.com/2021/english/api/sldworksapi/SOLIDWORKS.Interop.sldworks~SOLIDWORKS.Interop.sldworks.IRenderMaterial~Roughness.html)

RGB comparisons use normalized encoded channels and an absolute tolerance
of 1e-6 for archived binary32 rounding. Renderer comparison uses the
low three COLORREF bytes when the high byte is zero. Roughness and
transparency comparisons preserve the independently recorded archive
values. Exact filename equality compares string identity. It leaves
installed short-path aliases and resource identity unresolved.
GetRenderMaterials2 can allocate a live appearance-manager entry, so
each input opens fresh and read-only. The observer never clicks a dialog,
rebuilds, edits a dimension, toggles display state, or saves.
[Prior getter side-effect evidence](AppearanceGetterPersistence2026.md)

## Freeze and run

The research-only method commit is an immediate child of a84a6578
with the identical production tree. Supply its full revision to the
freezer. It checks the disclosed source authority and creates a new
shared AppearanceGetterPacket01 directory exclusively. It then verifies
the packed tools in a fresh host Python process.

```sh
python3.14 -B re/tooling/sw2026/materials/FreezeAssignedAppearanceGetters.py \
  /Users/odin/Documents/UniCAD/Oracle121Takeover/SdkNamedMaterial01/NativeSourcePacket03 \
  --revision FULL_METHOD_COMMIT
```

With the licensed oracle idle, its owner runs the frozen observer once
through the previously measured current-user Windows Python 3.12
interpreter, with the returned Job hash. This leaves user-site pywin32
available and does not cache bytecode on the shared packet.

```sh
prlctl exec --current-user 'Windows 11' py.exe -3.12 -E -B \
  '\Mac\Home\Documents\UniCAD\Oracle121Takeover\SdkNamedMaterial01\AppearanceGetterPacket01\Tools\ObserveAssignedAppearanceGetters.py' \
  run --job-sha256 JOB_SHA256
```

The local Windows lease is C:\KitAssignedAppearanceGetter01 and
must be absent before launch. The exact control, D01, D02 and trailing
control run serially, each with a fresh licensed process. If the first
control fails, candidates are withheld and the trailing control retains
its own check. Process teardown precedes each subsequent phase.
Original sizes and hashes are checked before and after observation
and again across all three files at completion. Only the aggregate
Result.json is printed. The individual COM call records, installed
type descriptors, raw values, filenames and diagnostics remain on the
guest. Exit 0 means the scoped observation completed under its controls.
Exit 3 retains incomplete or failed evidence. The observer measures getter
semantics only.
[Observer](../../tooling/sw2026/materials/ObserveAssignedAppearanceGetters.py) [Freezer](../../tooling/sw2026/materials/FreezeAssignedAppearanceGetters.py)

## Measured owner results

Four distinct processes passed on build `34.5.2.0604`. Both controls opened cleanly, both source hashes stayed intact and the observer made zero save calls. The two material parts matched their active configuration, sole solid, volume and centre. Both body getter channels returned null in each case. Both document channels returned nine values and matched the classic RGB and transparency. In D01 its RGB differs from the stored model and physically based values. In D02 those three stored RGB values coincide.

Each selected-state renderer result attached to the part itself and matched the classic roughness and exact filename in both sources. The archived renderer ID matched the configuration holder in both cases. The part call returned a different ID in D02. Render roughness differed from the physically based roughness in both sources. These distinctions keep material identity, legacy document display and renderer state as separate measured owners. [Native receipt](../measurements/2026/AssignedMaterialAppearanceGetterNative01.json)
