# Native circle mode and parameter-name bindings for primitive preparation

Task `B04-SW2026-FREECAD-CYLINDER` belongs to `/root/assembly_occurrence`. Root owns integration and native tests in PR #121. This is a bounded exact-build static follow-up to the [complete source admission](FreecadCylinderAdmission2026.md). It adds no primitive writer, custom-name lifecycle qualification or native acceptance. All original native and sealed controls remain untouched.

This tranche exits with reproducible native bindings and concrete SDK ownership gates. Product completion retains the full source-qualification exit condition in the source admission record.

The actionable result is that `D1` is the first automatically generated parameter name, rather than a mandatory wire constant. The current circle preparation guard requires that spelling. The common native parameter setter and name-object serializer do not. The existing SDK already has an authored-name argument on the shared length-parameter constructor, and its ordinary prism end input already carries a primary depth name. Circle composition does not forward those names throughout its graph and keywords.

## Target and method

The pinned SOLIDWORKS 2026 SP05.2 `sldmodu.dll` is 46,536,280 bytes, preferred base `0x4b140000`, SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`. Target-free REA resource inspection binds that identity as `ev_7fc3ecfa02cbbd7d6067ca5c370b778582e5ddc85ae1940285a50b90bfc6ceec`. The instruction checks use stateless Apple LLVM 21.0.0 on that original PE. No analysis database, Hopper document, CAD process or VM was opened.

[`PinCircleNativeBindings.py`](../../tooling/sw2026/freecad_cylinder/PinCircleNativeBindings.py) independently regenerates seventeen method-range hashes, the actual circle virtual targets, both numeric conversion factors, naming-prefix/format vocabulary, the concrete node-name serializer and its archive imports. It outputs numeric bindings and hashes, with no vendor listing or payload. [Machine-readable knowledge](FreecadCylinderNativeParameter2026.json) binds its source, exact output, private instruction receipt hashes and twelve SDK dependency hashes at `47dd6ab67598eb7cdafe8b6595ba19ba2f7da355`.

## Radius and diameter are explicit representation choices

The previously derived [circle construction](CurvedSketchConstruction2026.md) and [parameter lifecycle](RadialParameterLifecycle2026.md) rules are independently rechecked here. Their existing disclosed native evidence is recorded separately in [SDK circle construction](SdkCircleBoss2026.md). This pass adds no new oracle observations.

| Input branch                   | Native decision                           | Value-dimension type | Owned length |
| ------------------------------ | ----------------------------------------- | -------------------- | ------------ |
| Explicit `DirDistOption=9`     | Radius selector is nonzero                | `sgDim.f80=3`        | `r` metres   |
| Explicit `DirDistOption=8`     | Radius selector is zero                   | `sgDim.f80=15`       | `2r` metres  |
| Ordinary automatic full circle | Equal start/end geometry selects diameter | `15`                 | `2r` metres  |

`sgSketch::makeRadDim`, `0x4c4cb670–0x4c4cb882`, computes the actual centre-to-marker distance. Branches at `0x4c4cb723–0x4c4cb75e` select or double that length. The concrete constructor at `0x4c40fec0–0x4c40ff03` chooses type `3` for a nonzero radius selector and type `15` otherwise. Map a source `Radius` to the explicit radius selector independently of the circle geometry.

The conversion bodies at `0x4c42f850` and `0x4c431170` respectively change type `3→15` and `15→3`, multiplying the existing length by `2` or `0.5`. The constants are read from `0x4cd9e318` and `0x4cd9a3c0`. The actual `sgCircleDim` table at `0x4cf79588` binds value getter slot `+0x88` to `0x4c81fc50` and setter slot `+0x1b8` to `0x4c81fe00`. The ordinary double-parameter path retains `Dimension_c.f28`. At `0x4c81ffef` it calls the existing parameter setter `0x4c19cae0`, which writes its scalar `f58` and clears alternate-value state. No parameter name is replaced or allocated in the direct conversion bodies.

This is not a whole-program guarantee for callbacks, equations or shared parameters. It also does not make a display-only toggle sufficient: the existing radial display, subtype and text-kind rules must remain consistent with the value-dimension type and length. The shared radial builders already take one explicit `IsDiameter` choice for those owners.

## Automatic `D1` and stored names have different owners

| Operation                 | Exact native owner                                                                             | Consequence                                                                                         |
| ------------------------- | ---------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| Generate candidate        | `moModelFeature_c::nameParameter`, `0x4bea1400` with the first candidate at `0x4bea144b`       | First ordinary empty-profile candidate is `D1`                                                      |
| Format candidate          | `Dimension_c::genParamName`, `0x4c820f20` with prefix pointer `0x4db03700`, format at `0x4cdf9d88` | The format is `%s%d` with prefix `D`                               |
| Set parameter label       | `Dimension_c::setParameterName`, `0x4c821c40`, calls `moParameter_c::setName` at `0x4c821c67`  | Caller text reaches the existing parameter                                                          |
| Store name                | `moParameter_c::setName`, `0x4c19c9b0`, calls `0x4b555250`                                     | Create a `moNodeName_c` when parameter `+0x18` is null, or update the existing text              |
| Serialize name            | Concrete vtable `0x4cd8ce98`, vendor slot five, target `0x4c179ca0`                            | The name object's string at runtime `+0x08` goes through the imported Unicode CString writer/reader |
| Assign dimension identity | Naming calls the header allocator at `0x4c821d0b` only when dimension `+0x50==-1`              | The ID allocator retains any existing `f50` independently of the generated name     |

The node-name serializer dispatches to the imported `swccu.dll` Unicode CString operators at IAT `0x4cd3da28/0x4cd3da30`. It does not enforce a `D1` token or regenerate a name from the dimension ID. The active grammar's owners are parameter `moNode_c.f18` and text `moNodeName_c.f08`. Parameter `f48` is a separate optional name object with alias semantics still open.

`moParameter_c::setName` also compares the resulting name with resource token `0x2e56`. An equality calls `moNode_c::setFlagOn2` at `0x4c19ca00` with mask `0x1`. Its target `0x4c03ed70–0x4c03ed7e` reads and updates runtime `+0x2c`, the separate node mask `f2c`. Thus a general rename is not justified by replacing the name text alone. The resource's resolved text, localization and special-name role remain open in this source trace. Arbitrary name syntax, collisions, expression lookup, higher-level rename validation and save/reopen behavior are also not closed by the storage body. In particular, this trace does not qualify a FreeCAD full parameter name containing spaces or punctuation as a native editable name. A future source bridge must explicitly bind the original source ID and full name to the chosen native leaf and actual owner, then measure that choice.

## Exact SDK reuse and gaps

| SDK path                                | Current behavior                                                       | Source-preserving continuation                                                                     |
| --------------------------------------- | ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `Dimensions.MakeLengthParam`            | Already accepts `NameValue`, validated as one leaf by `ReadDriverName` | Reuse the same parameter and name-object constructor                                               |
| `Circles.MakeRadialVal`                 | Calls that constructor without the name argument                       | Forward the admitted radial name through the existing defaultable argument                      |
| `Circles.AddCircDimMut`                 | Publishes the same parameter, value dimension, handle and display      | Forward intent through the shared graph rather than constructing another parameter                 |
| `Part.Neutral.ReadCircParams`           | Requires two/three unextended native-style drivers named `D1`/`D2`     | A complete primitive bridge needs the actual source IDs and names |
| `SketchDimensions.MakeSketchKeys`       | Reads the generated parameter's actual name                            | Reusable without a renamed keyword surrogate                                                       |
| `Blind.BlindEndInput` / `SelectEndName` | Existing prism route carries `DepthName` for primary ordinal one       | Reuse this ownership pattern                                                                       |
| `Blind.BossEndInput`                    | Circle end input has no primary-name member                            | A future coherent extension must bind the actual primary depth name, preserving defaults           |
| `Part.MakePartKeys`                     | Uses `DepthName` for `BlindPlan` and `D1` for circle depth  | Derive keywords from the same admitted name as the real parameter                                  |

These are proposed later hooks, not implemented changes. A name-only patch would leave the thirteen-parameter source contract, metadata, placement, material reference and explicitly absent source sketch/support unresolved. The primitive writer gate remains closed until independently authored native sources are locked and the complete mapping is qualified.

Confidence: the representation choice, automatic first-name rule and stored-name ownership are **confirmed** within their stated static and previously measured disclosed bounds. Custom-name lifecycle, conversion callback and general equations remain open. The hypothesis that the file grammar itself requires `D1` is **refuted** for the inspected name-object path.

The English resource and the exact case-insensitive comparison are bound separately. [Resource owner and ARM64X view](FreecadCylinderNameResource2026.md)

See the [specific naming gotcha](../../../Documentation/Gotchas/Conversion/Solidworks/Profile/Dimensions/AutomaticCircleNamesAreNotWireConstants.md), [source envelope](FreecadCylinderAdmission2026.md) and [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
