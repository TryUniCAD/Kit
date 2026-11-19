# Assigned-material owner research for SOLIDWORKS 2026

PR #121 task `B04-SW2026-NAMED-MATERIAL` adds an exact-build research map for ordinary explicitly assigned part materials and a proposed source-authoring protocol. It adds no public reader or writer capability.

The [owner record](../../../../re/solidworks/records/AssignedMaterialOwners2026.md) and [machine ledger](../../../../re/solidworks/records/AssignedMaterialOwners2026.json) distinguish the UI density preference, physical density parameter, configuration density copy, database/material IdName and actual atom material association. The current SDK already models several individual fields, but that does not establish complete assignment or generative defaults.

The independently authored [module inspector](../../../../re/tooling/sw2026/materials/InspectMaterialOwners.py) verifies five exact original DLL hashes and emits numeric field/range/literal evidence without a vendor listing. Run it against the external pinned licensed installation copy, using a new output path:

```sh
python -I -B re/tooling/sw2026/materials/InspectMaterialOwners.py --bin /external/pinned-2026/bin --output /unused/MaterialPins.json
```

The model-free oracle capture verified three installed catalogs, the schema file identity and the required registered API members. It opened zero documents and confirmed graceful exit with FlexNet unchanged. To replay, stage the capture and the verified `OracleIdentity.py` as siblings in the immutable oracle packet. The sampled catalog density values need mass and volume calibration before they qualify as physical material inputs. [Capture tool](../../../../re/tooling/sw2026/materials/CaptureMaterialCatalog.py) [Installed metadata receipt](../../../../re/solidworks/measurements/2026/AssignedMaterialCatalogMetadata01.json)

The host-only [source-plan preparer](../../../../re/tooling/sw2026/materials/PrepareMaterialSourceRecipe.py) consumes explicit read-only installed-database/API metadata and computes independent geometry, masses and response ratios. It opens no CAD file and emits no CAD bytes. The [source protocol](../../../../re/solidworks/v2026/AssignedMaterialSourceRecipe01.json) still requires that metadata, root-owned source locks, a frozen native observer and the controlled native run. Its two disclosed designs cannot receive held-out credit.

Verification covers exact static extraction, host process smoke and installed catalog metadata. Native material assignment and generated material-bearing files remain open. The earlier custom-unit result preserved effective density at 1 kg/m³ throughout the unit-formatting changes. [Custom-unit lifecycle](../../../../re/solidworks/measurements/2026/SdkCustomMassUnitsNative01.json) [Density owner gotcha](../../../Gotchas/Conversion/Solidworks/Materials/MaterialAssignmentHasSeparateIdentityAndDensity.md)

Unresolved owners include fresh populated appearance/material state, material identifiers, atom/configuration precedence, the material XML streams and native assignment/save/reopen behavior. No saved field rows, material database rows, templates or donor payloads become writer inputs or defaults.
