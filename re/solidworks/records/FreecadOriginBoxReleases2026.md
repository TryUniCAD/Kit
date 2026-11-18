# FreeCAD origin box release schemas and native construction

Task `B04-SW2026-FCSTD-BOX`, PR #121. The strict FreeCAD adapter reads
the twelve disclosed CAD Fixture Recipes v1.23 cases named F14a through
F14d under FreeCAD 0.21.2, 1.0.2 and 1.1.4. Each input is independently
authenticated before neutral decoding. All twelve identify archive
version 1 and schema 4. The actual property owners differ by release.
Membership in the historical 165-file roster remains unverified.

| Source profile | Authored intent and stored owners | Shared output |
|---|---|---|
| 0.21.2 F14a | One independent AdditiveBox, empty `Support`, implicit schema units, body and three real positive millimetre lengths | Origin-anchored native profile, blind boss, three editable drivers and 13 text properties in MMGS |
| 1.0.2 F14a | Vanilla 3D attach engine, empty `AttachmentSupport`, unsuppressed box, explicit standard mm/kg/s/degree unit choice, default material identifiers and a compound flag | Same independently built geometry. Native millimetre/kilogram custom units and 19 properties |
| 1.1.4 F14a | Same semantic shape plus an owned origin point, neutral fuzzy tolerance, the preview extension and additional element-map metadata | Native origin aliases and literal source identity, custom mm/kg units and 22 properties |

`FreecadBoxRelease.py` reads the actual named enum choice and checks
the empty support, suppression and string-map states. The 1.1 origin
point must have the standard role, the actual origin group link,
identity placement and no expressions. The feature and body retain
their separate material identifiers as text. The stored UUID resolves
to the FreeCAD Default library material with density `1 kg/m³` in
both releases. The actual native effective unassigned body density
has the same value in the [measured custom-unit parts](DocumentMassUnits2026.md#generated-native-verification).
Native assigned material and appearance parity remain open.
[FreeCAD 1.0.2 default material](https://raw.githubusercontent.com/FreeCAD/FreeCAD/1.0.2/src/Mod/Material/Resources/Materials/Standard/Default.FCMat)
· [FreeCAD 1.1.4 default material](https://raw.githubusercontent.com/FreeCAD/FreeCAD/1.1.4/src/Mod/Material/Resources/Materials/Standard/Default.FCMat)

The shown `Refine` and fuzzy tolerance values remain literal
source properties. Both upstream primitive implementations return
the ordinary solid before their Boolean/refinement branches when the
base shape is absent. The admitted feature explicitly proves an empty
base and no active attachment. It derives all vertices and length
drivers from the authored lengths. [FreeCAD 1.0.2 primitive implementation](https://github.com/FreeCAD/FreeCAD/blob/1.0.2/src/Mod/PartDesign/App/FeaturePrimitive.cpp#L67)
· [FreeCAD 1.1.4 primitive implementation](https://github.com/FreeCAD/FreeCAD/blob/1.1.4/src/Mod/PartDesign/App/FeaturePrimitive.cpp#L66)

The source guard retains all three supported profile fields and
the existing default construction for legacy callers. Both newer
recipes pass their explicit mm/kg choice to the shared typed unit
writer. Six guarded builds reproduce the three layouts with and
without the source B-rep and payloads. All generated files have zero
runtime input reads. The normal SDK read recovers one complete box,
the three dimensions, the actual Body name and every expected text
property. Both Config and ResolvedFeatures re-emit exactly per file.

The nine genuine attached or multi-feature cases and four deliberate
scope mutations refuse generation. The additional mutations cover
a foreign unit mode, material identifier, active origin displacement
and populated string map. The nine earlier FreeCAD box guards still
reproduce both original native-tested files byte for byte.
See the [guarded release measurement](../measurements/2026/SdkFreecadBoxReleaseConstruction01.json).

The exact newer-release native packet is frozen at SHA-256
`bfad084b837281083c6550f20a2fc8c2139bef428c79c59aa7b8082a4a1c94ca`.
`InspectFreecadBoxReleasesNative.py` binds its two generated files
to the complete guarded build record. The two independent fresh
lifecycles measure Length, Width and Height editing, native kilogram
preferences, actual origin ownership, named body, mass and text
properties through controls, rebuild, save and reopen.

## Native persistence

Both controls and all four candidate processes pass on SOLIDWORKS
2026 SP05.2. Each of the six driving edits rebuilds the same native
parametric owners. Length and Width are restored before the final
Height edit and save. The fresh native reopens recover heights
`15.87 mm` and `16.19 mm`. All eighteen candidate observations retain
the one-solid topology, the named Body, origin constraints, expected
geometry, text and the custom millimetre/kilogram setting. Observed
mass divided by volume is `1 kg/m³` in all eighteen states. The
license processes remain unchanged across the batch.

The host verifier reads both fresh files and both edited derivatives
through the normal strict reader. All four retain the actual named
drivers and source properties. Forty stream comparisons include
Definition, CMgr, CMgrHdr2, both headers, Config-0, ResolvedFeatures,
KeyWords, Biography and History. The initial observer used the native
compact KeyWords spelling for all four. The fresh constructor uses
spaced empty elements, and the native save uses compact empty
elements. Selecting the corresponding documented frame reproduces
all four KeyWords streams exactly.
[Native measurement](../measurements/2026/SdkFreecadBoxReleaseNative01.json)
[KeyWords spelling](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Revolve/KeywordEmptyElementSpelling.md)

Native assigned material, appearance and full original-corpus
qualification remain open.
