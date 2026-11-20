# Observed stock part lighting in SOLIDWORKS 2026 SP05.2

Task `B04-SW2026-IMPORTED-BODY`, PR #121. The evidence supports
construction from explicit scene semantics. A universal vendor default
remains unqualified because the native loader consumes an actual session
environment vector. This matters for neutral import parts with no authored
presentation. All four measured empty-environment files open with warning
32. At the same logical destinations, their authored-ambient counterparts
open, rebuild, save and reopen cleanly with the same kernel and rollback
bytes.
[Same-locator native lighting comparison](../measurements/2026/GeneratedLocalImportLightingContrast01.json)

## Disclosed source census

Two fresh host processes repeated the same typed scene observations on
three unrelated part families. Every source matches an existing native
receipt for `sldworks.exe` **34.5.2.0604**, SHA-256
`3f6844591c7456a476bdc141817a21c3c10f770e12347a698eef5ea8ad60d1fe`.
The program reads the actual Config-0 manager selection, verifies the
environment folder's identity in the resolved root list, and follows the
four distinct registered members of its actual list.

| Native source | Governing feature | Source SHA-256 |
| --- | --- | --- |
| Imported solid | `moBaseBody_c` | `13f1ef12ab727323a826ead989087079f44e9b24a4326aa9b65be61c9d81f325` |
| Circular blind boss | `moExtrusion_c` | `1c1bc718661b88a119bc3ac041f97d56cf5b4a06e290e1ac1afc79d423e42d23` |
| Full revolve | `moRevolution_c` | `28e1f9cd045a7a264b2bdf8658ae593744d65ca708def4a48199ec357f063ab0` |

Each part supplies 269 named typed field slots across the environment
folder and its ambient and three directional members. Comparison replaces
verified member references with their ordered roles and excludes only the
top-level persistent identity `f08` and creation FILETIME words `f2a0`
and `f2a4`. It preserves those values separately and regenerates both
FILETIME words from the decoded instants. File and map positions are
recorded as diagnostic data. The comparison retains nested fields,
including actual name-holder text and visualization records.

Of 254 retained slots, 252 agree. The only differences are environment
folder `f29c` and `f301`. Both the semantic reader and the complete
retained light records agree across all three parts. Import and revolve
share all four stored creation instants. The circle has later instants,
with distinct ambient and directional fractional ticks. The observation
therefore compares independent geometry with inherited or recreated
lighting under a shared observed profile. It has no independently varied
session preference or language input.
[Complete field census](../measurements/2026/StockPartLighting01.json)

## Field authority

| Field or group | Classification |
| --- | --- |
| `f08`, `f2a0`, `f2a4` | Persistent allocation and explicit creation chronology. These are separate model domains and all actual values remain in the receipt. |
| Environment `f29c` | Retained update stamp. Imported, circular and revolve values are 113, 139 and 115. The fresh-light constructor's seed 101 cannot supply the saved folder state. |
| Environment `f301` | Retained subservice-pack field. The saved values are 0, 2 and 0 in the same order. The shared fresh feature constructor assigns this field from its target. The application that saved a file does not determine the value of each previously created owner. |
| Light `f29c`, `f0c`, `state`, `f35c`, `f36c`, `f428`, `f478`, `f488`, `f490`, `f500` | Stable observed state also backed by the existing exact-build type-one constructor evidence in its supported lane. These are constructor rules or initialized state under their documented conditions. |
| Light `f388` | Every observed saved member sets KeepInScene false. The exact unmodified type-one constructor seeds 1 in this position. The saved scene has effective state beyond bare constructor defaults. |
| Light `f390`, `f398`, `f3a0`, `f3a8`, `f3b0`, `f498` | Actual coefficients, colour, direction and shadow softness. Stable for the corresponding roles on these files. The native creation route sources the effective attributes from the session vector. The sample supplies no portable rule for choosing those inputs. |
| Light `f18.f08` and `f4f8` | Actual display label and separate external identifier. The files share Ambient and Directional1 through Directional3 despite different part and configuration titles. All three directional members share the external string `Directional-1`. No alternate language or session-name source was measured. |
| Remaining stable fields | The census preserves each observed value and its owner. Stability across these files leaves fields without independent constructor provenance as observations. |

The exact native `moModel::createDefaultLights` function
`[0x4c019c60,0x4c01a036)` in the pinned `sldmodu.dll` obtains the current
session environment named `Default`, creates the specified kinds, copies
the effective attributes, and inserts the members under the actual folder.
The separate `hasLights` function accepts any actual member that passes
its light predicate. A clean open with one authored ambient therefore
establishes light admission in the measured setup. Matching the native
preset requires the independent preference and localized-name owners that
populate the session environment.
[Exact native producer](PartEnvironmentDirtyPropagation2026.md)
[Type-one constructor](AuthoredAmbientConstruction2026.md)

## Reproduction

```sh
PYTHONPATH=src:. python3.14 -B \
  re/tooling/sw2026/downstream/lighting/AuditStockPartLights.py "$DISCLOSED_ROOT"
```

The observer opens the three exact disclosed paths and verifies their
hashes again after reading. It produces a numeric field receipt and
opens zero native applications or held-out payloads. Writer admission
and default selection stay outside this checkpoint.
