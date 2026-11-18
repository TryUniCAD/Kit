# Default SDK recipe for an ordinary standalone SOLIDWORKS part

The ordinary writer preparation accepts a millimetre neutral document with one
closed loop of nonconstruction lines on the canonical Front Plane. The loop
drives one forward blind boss, one editable length, and one solid. The actual
neutral configuration, names, sketch endpoints and depth supply the model.
The generated container has ten streams. [Polygon construction](SdkCompletePolygonPart2026.md)

The approved target is SOLIDWORKS 2026 SP05.2, executable 34.5.2.0604, archive
version 19000, full build date code 2026306 and Parasolid behavior 370108.
The shared serializer allocates its graph, feature identities and save-state
owners. One writer clock event supplies creation, modification and save epochs.
History records Kit as the author and leaves the native-save flag clear.
[Target codes](ModelConstruction2026.md) · [History ownership](HistoryConstruction2026.md)

## Default fields

| Fields | Input or rule |
| --- | --- |
| Name, support, configuration, sketch and driving depth | The admitted neutral model supplies the names, line topology and dimension. |
| System tree and role names | The default English part initializes the ordinary folders in the qualified order, canonical planes, annotation cabinet and origin. |
| Part and analysis units | Neutral millimetres select MMGS with degree angles. The separate analysis unit table uses MKS and radians. Kit chooses four decimal places for both. |
| English style | The profile uses ISO, constructor resource labels, Century Gothic and a solid continuous line style. Empty cut-list expressions and exclusions initialize unused owners. |
| Print widths | The 2026 `utLineWidthPrintData_c` constructor at `sldmfcu.dll!0x3c84adb0` stores 0.18, 0.25, 0.35, 0.5, 0.7, 1, 1.4 and 2 mm as binary32 metres. The process computes those values from the documented metre scale and does not read the preference overlay. |
| `fa58/fa5c/fa60/fa64` | The pinned factory settings register shaded tessellation 26, wireframe tessellation 25 and optimal tessellation enabled. The angular value is four for 26 by the factory's truncated logarithmic rule. |
| `fa90` | The document stream-compression preference uses the registered factory false value. |
| `f1688` | The UI material-density preference uses the registered factory value of 1000 kg/m³. The unassigned body retains the measured effective density of 1 kg/m³. |
| `f1418` | The hatch's English constructor resource `0x3c2c` is `ANSI31 (Iron BrickStone)`. Angle, scale and flags belong to the verified hatch initializer. |
| Empty journal, display bits, user options and text | Kit sets the unused journal caption to `Journal` and emits no overrides, content or user provenance for these owners. |
| Final self identity | Windows paths use the specified absolute destination. A standalone host path has no Windows drive mapping. The writer derives the qualified neutral locator from its actual basename under `C:\KitSdkCandidates`. |

The settings proof binds six original modules, preference getters and typed
initialization payloads. The print-width proof is REA evidence
`ev_adaa2d6db07ed7d926bd2de116712d88f007c149989e31d45634a22a42f64fa0` and
the eight constructor writes beginning at `sldmfcu.dll!0x3c84adce`. The exact
binary32 words are `393cbe62, 3983126f, 39b78034, 3a03126f, 3a378034,
3a83126f, 3ab78034, 3b03126f`. All eight match conversion from the decimal
millimetre values above. [Factory settings receipt](../measurements/2026/SdkPartPreferenceDefaults01.json) ·
[Style vocabulary](StyleConstruction2026.md)

## Controlled verification

Two fresh neutral shapes use only the default recipe. The guarded builds each
repeat in a fresh process, round-trip all ten streams and have distinct file
lengths. The first controlled native trial completes the lifecycle for each
shape and fails its assumption that UI preference density drives the
unassigned mass calculation.

The repeat keeps both generated files unchanged. The observer reads the
document preference and effective body density separately. Six fresh
SOLIDWORKS processes pass between independent controls. Both parts retain
their 25 ordered native rows, editable depth and measured solid through a
driving edit and a fresh reopen. The archived native locator stays absent.
All 240 numeric checks pass. [Native evidence](../measurements/2026/SdkDefaultPartNative01.json) ·
[Density ownership](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Parts/DefaultPartDensityHasTwoOwners.md)

The recipe covers ordinary neutral parts with no authored material or
presentation overrides. The factory values cannot substitute for authored
document preferences or assigned materials. The three original polygon
held-outs qualify the polygon construction separately. The new default
recipe trial adds no held-out source or FCStd corpus conversions.
[Original polygon evidence](../measurements/2026/SdkOriginalPolygonNative01.json)
