# Named planar child renderer composition

Workstream `B04-SW2026-MATES-PLANAR/source-root-projection`, owner `assembly_frontier`, delivery PR #121. The initial comparison base is `aa76928bfd03d3bcff777f27cbf91237caa13c92`. The scoped case is a dimensioned rectangular child with a stock untextured colour resource on its live model and current configuration, a separate detached self holder and an all-visible parent. [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md) · [Writer model](../../Playbook/WriterModel.md) · [Parent compound ownership](SdkPlanarVisualComposition2026.md) · [Revision-bound guarded evidence](../measurements/2026/SdkPlanarRendererComposition01.json)

| Owner | Input or generation rule | Scope check |
| --- | --- | --- |
| `moVisualProperties_c` | Main and hidden-line RGB, legacy material string and specular scalar | Complete live and detached objects verified independently, with matching semantic payload and separate ownership |
| `RealViewMaterial_c` | Ordinary stock `graphics\materials\color.p2m`, named classic optical scalars and enumerated flags | Explicit absolute Windows data directory for live owners, derived `<SystemTexture>` alias for detached holder |
| DSPBR `f88` | Independent RGBs, metallic, roughness, specular, sheen roughness, refraction, attenuation, thin-film and bools | Opaque `2025x/basic`, no textures, validated constructor fields, float32 conversion and Fresnel rule |
| Definition `f1110` | Part appearance starting ID plus two ordered authored events, with empty typed list | Holder first, live second, next cursor third. Root and config share the live numeric ID with distinct object graphs |
| Definition `f1150` | Explicit empty BOM owner presence | Retains measured wrapper and manager within the composed part Definition |
| Physical root `f1420` and config `fc50` | Constructor null root material and configuration sentinel `-1` | Legacy appearance name is its own semantic owner. Explicit physical materials require separate evidence |

The exact installed `34.5.2.0604` module observations bind `sldmfcu.dll` SHA-256 `af2148c7f429e017e75de45b27acf4105b80457fa510dffaa25db88c387a9735` and `sldmodu.dll` SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Native RealView and DSPBR constructors begin at virtual addresses `0x3c896080` and `0x3c772330`. The basic-file load and converter paths bind RGB channel expansion and float32 normal-incidence reflectance `(IOR−1)²/(IOR+1)²`, with rounding at each native intermediate. The DSPBR roughness and legacy roughness are different fields with independent named inputs. The RGB tuple and attenuation remain explicitly represented even where all three disclosed values equal the installed asset defaults. Shader inputs yield the material bytes directly from values and checked constructor rules. Neither the application asset nor a native source is a writer input file. [Read and author bridge](../../tooling/sw2026/planar_registry/PlanarRendererInput.py) · [Shared rendering code](../../../src/convert/adapters/solidworks/Archive/Construction/Part/Displays/Rendering)

| Child | Source holder, live, next ID | Fresh holder, live, next ID | Source and generated VisualStates bytes, terminal map |
| --- | --- | --- | --- |
| A20 | `3, 9, 10` | `10, 11, 12` | `1789, 26` |
| A21 | `3, 10, 11` | `11, 12, 13` | `1789, 26` |

The source bridge accepts the installed resource alias only when all three sources of appearance agree with the independent constructor outside the scoped inputs. Both generated parents match their prior bytes. The changed child streams are CMgr, Config-0, Definition and VisualStates. The guarded workers use `FinishBlindMut`, `MakePlanarGroup` and the actual `EmitAsmStreams` boundary. The unrelated appearance changes the colours and optics, uses an IOR of 3 with resulting reflectance 0.25 and allocates through the high ID word. The selected archive owns no opaque bytes or provisional schema. Crossed cursors, aliased shaders, other resources and shader profiles, invalid paths and wrapped allocation refuse.

Two strict source processes, 12 isolated generation processes, seven isolated writer refusals and eight source owner mutations pass. The guard reports zero writer runtime input reads. Both prior constructor-only controls reproduce byte for byte. The prior native registry control proves the root default density parameter can be created on save while the configuration remains unassigned. The rich renderer lifecycle has zero native runs and no new held-out credit at this revision. Actual source root and datum creation chronology, alternate shader/texture or assigned material models, and public whole-source admission remain outside the slice. The strict ordinary Definition reader and public assembly root admission retain their explicit refusals. [Density regeneration gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Oracle/Parts/NativeSaveCanPublishUnassignedDensity.md)

```sh
PLANAR_RENDER_PROOF="$(mktemp -d)/Receipt.json"
python3.14 -I -B re/tooling/sw2026/planar_registry/ProvePlanarRenderer.py \
  --disclosed /absolute/path/to/Oracle121Takeover --output "$PLANAR_RENDER_PROOF"
```

The retained receipt SHA-256 is `b86210a7e84994637e0a32fdb32e6b33b8f38c3e08a1c10eeed97e285ca0b754`. The runtime uses the measured independent data alias as neutral metadata. Saved inputs stay in their original custody. Only the sanitized receipt enters the repository.
