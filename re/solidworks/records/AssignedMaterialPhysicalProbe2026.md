# Generated physical material owner probe

Task `B04-SW2026-NAMED-MATERIAL`, PR #121. The bounded experiment constructs dimensioned ISO rectangular bosses with an independently authored neutral material. The material identity supplies an explicit catalog key and material record reference. This experiment requests the two-token native identity and supplies no allocation rule for a numeric catalog ID. Its output tests physical property ownership with the ordinary fresh rendering defaults. Populated material appearances, custom material catalogs, body assignments, overrides, and the XML material tree are outside this experiment. [Physical owners and installed build](AssignedMaterialOwners2026.md) · [Material tree correlation](AssignedMaterialTreeCorrelation2026.md)

## Constructor evidence

The exact `sldmodu.dll` image in the licensed SOLIDWORKS 2026 SP05.2 build has SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Its PE runtime-class descriptor `0x4daefbd0` names `moDensityParameter_c` and selects factory `0x4c176540`. The factory calls constructor `0x4c19bac0`, which calls the scalar parameter constructor at `0x4c19baf0` and installs the already identified vtable `0x4d124660`. The scalar constructor calls the ordinary node constructor at `0x4c03c250`; it sets the null auxiliary pointer, applies the initial clear-state operation and stores the provided density scalar. It also initializes the alternate value and flag to zero. The ordinary node constructor establishes the unset id, null name, empty text, primary flags and secondary zero. Independent ordinary current-body evidence and the SP05.2 density operation corroborate that wire shape. [Density terminal and store rules](AssignedMaterialOwners2026.md) · [Disclosed typed owner walks](AssignedMaterialArchiveOwners2026.md)

## Contrast and scope

The [guarded builder](../../tooling/sw2026/materials/BuildAssignedMaterialProbe.py) validates one material, projects the geometry separately and builds the existing dimensioned part graph. It uses the typed material for the explicit experiment assignments before the shared archive emits. It constructs the part-density subtree, active configuration density, and active visual identity independently. The three selected owners have five contrast modes, including the unassigned generated control and the all-owners case. A second geometry and catalog exercise the all-owners case independently. The research process checks deterministic generation, exact typed re-emission of the three linked streams, allocated map continuity and zero access to external files or processes in generation. It never reads saved material property records.

The [packet preparer](../../tooling/sw2026/materials/FreezeAssignedMaterialProbe.py) uses neutral geometry for the measurement predictions and pins generated candidates, the already qualified separate vendor control, and every exact helper. The [native observer](../../tooling/sw2026/materials/RunAssignedMaterialProbe.py) uses one process per case to measure actual editable driving values, feature tree, active material identity, physical selected-body density, mass and geometry at the exact path, both cold and after rebuild. The probe establishes an observable contrast; native edit, save and fresh reopen are required in later qualification. Only the disclosed cohort is used. The earlier salted commitment for independent originals stays closed during discovery. [Private prewriter custody receipt](../measurements/2026/AssignedMaterialPrivateSourceLock01.json)

## Native measurements

Six computed files opened and rebuilt without diagnostic warnings or errors in six distinct SOLIDWORKS processes. The two surrounding controls also passed in fresh processes. The candidates passed 120 numeric checks for native driving lengths, analytic volume, area, centroid and selected-body density consistency. The disk hashes of the generated inputs remained unchanged. [Generated custody receipt](../measurements/2026/AssignedMaterialPhysicalProbeBuild01.json) · [Native measurement receipt](../measurements/2026/AssignedMaterialPhysicalProbeNative01.json)

| Generated contrast | Named assignment observed | Selected-body density in kg/m³ |
| --- | --- | ---: |
| No added owner | Blank | 1000 |
| Part density | Blank | 2700 |
| Active configuration density | Blank | 1000 |
| Active visual identity | Requested aluminium | 1000 |
| All three owners, aluminium | Requested aluminium | 2700 |
| All three owners, steel | Requested steel | 7858.000032 |

Both all-owner cases preserve the same identity, density, and expected mass before and after a rebuild. In this ordinary single-configuration shape, the part density subtree supplies the observed density and the active visual IdName supplies the identity. The configuration scalar alone leaves the selected-body density unchanged. The comparison establishes cold and rebuilt physical behavior in the pinned build with ten ordinary generated streams. Native persistence, any catalog payload or authored appearance, and held-out qualification remain open. [Independent identity and density](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Parts/MaterialIdentityAndDensityHaveSeparateOwners.md)
