# SOLIDWORKS 2026 document mass and custom units

Task `B04-SW2026-UNITS`, PR #121. The native measurement uses SOLIDWORKS
2026 SP05.2 executable `34.5.2.0604`, SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
The two input shapes are independently authored corner and centred
rectangles with unrelated dimensions and three driving lengths. They
use native sketch and boss construction in the reserved Windows 11 VM.
The six native-authored file hashes are established before any
custom-mass writer construction.

`DocumentUnitApi.py` reads the registered version 34.0 type libraries.
`IModelDocExtension` owns the measured preference calls. The
`swUnitSystem` selector is 263 and `swUnitsMassPropMass` is 259. The
option for an ordinary document setting is 0. The installed declarations
give native API system values 5 for MMGS and 4 for custom, and API mass
values 2 for grams and 3 for kilograms. The archive uses separate values.
[SOLIDWORKS document unit API](https://help.solidworks.com/2024/english/api/swconst/DP_Units.htm)

| Archive owner | Classified rule | Measured scope |
|---|---|---|
| `moPart_c.f9b8` | User unit table. Its sixteen entries follow the actual SDK archive class order. | Both parts and all three modes |
| `moPart_c.f9c0` | Independent analysis table, omitted in these sources. | Both parts and all three modes |
| `moUnitSysUnits_c.fb0` | The serialized system selection is 4 for MMGS and 3 for custom. | Paired preference changes and native reopens |
| `moDensityUnits_c.fc4` | The serialized mass selection is 1 for grams and 2 for kilograms. | Grams and kilograms form a one-field delta within custom |
| `moDensityUnits_c.has_fb8` and `fb8` | The measured custom mode attaches an independent length-format owner. Its initialized format matches the actual primary display format with its dual child absent and its `f88` value zero. | Each complete nested graph matches in both designs |
| `moDensityUnits_c.fc0`, `fc8`, `fcc` | Volume selection reads `fc8` when `fcc` is nonzero, and otherwise `fc0`. The measured files retain volume fields 3 and mode 0 before and after both changes. | Pinned native getter and fully parsed tables |
| `moLengthUserUnits_c.f88` | The primary value changes across the native mode transition. In each design the values equal the rounded displayed height and depth. Its broader authoring rule remains unqualified. | Corner 23.82 to 6.12, centred 17.62 to 9.22 |

Hopper through the REA CLI inspected five exact addresses in the pinned
`sldmfcu.dll` SHA-256
`af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735`.
The mass getter and setter at `0x3c7da1a0` and `0x3c7dc2d0` read
and write native memory field `fc4`. The system pair at
`0x3c754580` and `0x3c755b20` binds `fb0`. The volume
getter at `0x3c918060` supplies the `fcc` branch. The PE export
addresses identify the actual owning classes even when Hopper displays
a folded alias. The isolated CLI invocations use a private target copy.

The complete `moModel_c::getDefaultDensityUnit` body in pinned
`sldmodu.dll` covers `[0x4c01f240,0x4c01f360)`. Its IAT bindings
find the model's actual user table, identify the density and length
classes and attach the primary length through
`moDensityUnits_c::setLengthUnit` if the density owner lacks a length.
The six typed archives show the independent nested representation
after native serialization.

`AuthorDocumentMassUnits.py` verifies the immutable packet, brackets
the six saves and separate reopens with pristine controls, and logs
every native session identity and preference. Each source mode preserves
the modeled dimensions, feature tree, solid count, volume, area and
centroid. All ten native processes and 292 candidate checks pass.
Both controls pass and the license process inventory stays identical.

`QualifyDocumentMassUnits.py` binds all six source hashes to the
native record and requires exact Definition, CMgr, Config-0 and
ResolvedFeatures re-emission. The first observer rejected the additional
density length owner. The second assumed the standalone fresh format.
The final observer derives the expected complete detail from the actual
primary format. All 24 stream checks and both complete paired table
comparisons pass. The [measurement receipt](../measurements/2026/DocumentMassUnitsNative01.json)
keeps all three observer identities and normalized native evidence.

This qualifies the disclosed source setting and ownership map. Generated
native verification, original-corpus admission and additional custom
units remain open.
