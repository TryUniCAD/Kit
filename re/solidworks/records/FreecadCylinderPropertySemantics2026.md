# FreeCAD 1.1.4 cylinder property semantics

Native primitive conversion remains unfinished. This tranche classifies the complete disclosed source envelope; it produces zero target files, starts zero CAD processes and reads zero held-out inputs. It does not establish SOLIDWORKS lowering or native acceptance.

Task `B04-SW2026-FREECAD-CYLINDER`, owner `/root/assembly_occurrence`, delivery PR #121. Root owns integration and the oracle. Dependencies are the [source admission](FreecadCylinderAdmission2026.md), [native companion receipt](../measurements/2026/FreecadCylinderNativeSources01.json) and exact public FreeCAD revision `4fd3bf320d9566a27e60069fc8387448aaa3a094`. The exit condition remains a native editable lowering that preserves the complete admitted source and passes independently locked vendor checks.

## Source authority and reproducibility

The [source deck](../measurements/2026/FreecadCylinderSourceDeck01.json) records FreeCAD `1.1.4`, build `20260928`, at that exact revision. The [machine-readable record](FreecadCylinderPropertySemantics2026.json) pins thirteen public source files by Git blob SHA-1, SHA-256, byte length and URL. Public source copies remain outside the checkout; no vendor listings are added here.

The [auditor](../../tooling/sw2026/freecad_cylinder/AuditCylinderSemantics.py) verifies those files and correlates both declared strict neutral envelopes. It verifies all three copies of the actual native object, every scalar parameter's ID, owner, name, order, value, unit and property tree, and all six nonscalar property owners. The [receipt](../measurements/2026/FreecadCylinderPropertySemantics01.json) binds the exact repeated audit. These are source-pin and ownership checks, not target-writer qualification.

## Thirteen scalar owners, five geometric inputs

The existing decoder labels all thirteen scalar projections `driving`. Retain that recorded role and the original property tree; it is not a semantic assertion that each scalar drives cylinder geometry. The source's `Prop_Output` and `Status.Output` flags suppress recompute touch. They do not mean that a value was computed or can be dropped. Hidden status describes the editor rather than persistence. None of these thirteen owners is established as a volatile cache or disposable format constant; the derived Shape lies outside that scalar list.

| Property           | Source semantics                                             | Required preservation                                                                 |
| ------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------- |
| `Radius`           | Authored geometric length, mm                                | Actual source ID/name, radius meaning and editable native parameter                   |
| `Height`           | Authored geometric length, mm; Z displacement                | Actual source ID/name; distinguish vertical height from oblique vector length         |
| `Angle`            | Authored sector sweep, degrees                               | A live sweep owner, including the transition between full and partial sectors         |
| `FirstAngle`       | Authored prism direction angle, degrees                      | X displacement dependency on the actual `Height` owner                                |
| `SecondAngle`      | Authored prism direction angle, degrees                      | Y displacement dependency on the actual `Height` owner                                |
| `AttacherEngine`   | Authored object-level attachment selector                    | Selected label and ordered enum vocabulary, consistent with the class identifier      |
| `AttacherType`     | Hidden/read-only engine mirror, also used on restore         | Persisted class identity and engine consistency; it is not a free geometric dimension |
| `MapMode`          | Authored attachment selector                                 | Actual stable enum ordinal and support relationship                                   |
| `MapPathParameter` | Authored path-parameter input, dormant when unmapped         | Original scalar and applicability, independently of cylinder dimensions               |
| `MapReversed`      | Authored attachment orientation input, dormant when unmapped | Actual axis reversal semantics, separately from extrusion direction                   |
| `Label`            | User-authored identity metadata with output status           | Internal object name and user feature caption remain distinct                         |
| `Label2`           | User-authored description, hidden/output                     | Preserve explicit presence and text, including an empty value                         |
| `Visibility`       | Object presentation state, synchronized with GUI show/hide   | Preserve display state without suppressing the feature or deleting its solid          |

The current strict documents have one active configuration and no overrides. These are object-level properties, not evidence for thirteen configuration overrides or a FreeCAD configuration scheme.

## The two prism angles are geometric drivers

[`Cylinder::execute`](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/PrimitiveFeature.cpp#L483-L536) constructs the requested circular/sector bottom face and passes it to the shared prism extension. [`PrismExtension`](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/PrismExtension.cpp#L37-L85) marks either angle change for execution and constructs the displacement

`d = (H tan(rad(a)), H tan(rad(b)), H)`

where `H = Height`, `a = FirstAngle` and `b = SecondAngle`. This is exact source logic. The property constraints declare each prism angle in `[-89.99999, 89.99999]` degrees. The sweep property declares `[0, 360]` degrees, and execution separately rejects `Radius`, `Height` or `Angle` below the linked OCCT `Precision::Confusion()` threshold. This record does not infer additional setter enforcement or substitute an unpinned numeric OCCT tolerance.

A nonzero prism angle translates the original base face obliquely. In general it does not produce a rigidly rotated right circular cylinder. The displacement length is `H sqrt(1 + tan(rad(a))² + tan(rad(b))²)`, so an along-vector native extrusion length cannot simply reuse `Height`. An equivalent directional extrusion must retain the original base plane and derive both its direction and length from these live inputs. A partial `Angle` also changes the profile boundary; a closed-circle sketch alone does not preserve it.

For a full circular base, the mathematical extrusion has local volume `πr²H` and centre `d/2`; world placement applies afterward. These are analytic consequences of the source construction. Nonzero-angle execution, partial-sector geometry, associated surface areas and native target edits are **partial** evidence here: neither disclosed case exercises those branches. The present ordinary cases have sweep `360`, both prism angles `0`, and identity placement. Their right-cylinder geometry remains bound to the earlier fifty native companion comparisons.

The two zeros and full sweep are observed inputs, not newly discovered wire constants. Storing them as uninterpreted extra text does not prove an editable native equivalent. The two-length surrogate remains insufficient evidence for full primitive preservation.

## Attachment state has a lifecycle

[`AttachExtension`](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/AttachExtension.cpp#L94-L175) introduces the engine, support, mode, reversal, path value and offset. Its [position update](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/AttachExtension.cpp#L338-L392) returns before resetting or changing `Placement` when the mode is deactivated. The actual persistent enum [starts with deactivated at ordinal zero](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/Attacher.h#L52-L75). This explains the measured unattached member without treating the other fields as constants or caches.

The engine enum chooses one of the declared 3D, plane, line or point engines. Changing it synchronizes `AttacherType`; changing the class field reconstructs an actual `AttachEngine` subtype. [Restore](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/AttachExtension.cpp#L710-L734) consumes persisted type state, repairs the enum from it and updates attachment placement. The mirrored field therefore cannot be discarded as a transient calculation.

For the applicable common placement path, [`MapReversed` reverses both Z and X axes](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/Attacher.cpp#L420-L423). It is not negative cylinder height. For an applicable single-curve attachment, [the path input interpolates the underlying parameter domain](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/Attacher.cpp#L1697-L1742), `u = u_first + p(u_last - u_first)`. It is not generally a physical arc-length fraction. No universal clamp is established by this path. These active attachment branches remain **partial**, with no new active-support corpus or target attachment claim.

`AttachmentSupport` and `AttachmentOffset` must remain in the same dependency envelope. The former is an actual document/subelement link; the latter is a local placement combined by the attachment engine. Unattached `Placement` is the authored object transform. Active mapping can update it, and the [part feature synchronizes it with Shape](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Mod/Part/App/PartFeature.cpp#L1520-L1555). The current scope admits only the independently checked empty support, identity offset and identity placement. Active modes or nontrivial transforms need their own native dependency proof.

## Labels and visibility are not geometry dimensions

The [document-object constructor](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/App/DocumentObject.cpp#L65-L81) explicitly gives `Label` output behavior and `Label2` hidden/output behavior. The [change handler](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/App/DocumentObject.cpp#L889-L942) updates label identity separately and excludes output properties from geometry touch.

The default application `Visibility` is output/hidden/no-modify. The [GUI owner](https://github.com/FreeCAD/FreeCAD/blob/4fd3bf320d9566a27e60069fc8387448aaa3a094/src/Gui/ViewProviderDocumentObject.cpp#L180-L218) calls show/hide and synchronizes the application property. This is presentation state; it does not establish a suppression relationship or removal of the underlying Shape. The property statuses can be changed by users, so the exact source property tree remains authoritative for admission.

## Executable boundary and remaining work

The audit preserves all nineteen native properties, all thirteen parameter owners, both source naming origins, the owned B-rep, source payload identities, empty expression engine, configuration and metadata hashes. `Shape` is derived from the primitive inputs and placement; it is retained for independent source validation and never copied to output. The actual `ShapeMaterial` is `Materials::PropertyMaterial` with a UUID. Its unresolved semantic mapping is separate from the scalar classification; an empty portable material list does not prove unassigned material.

The next construction method must name the native owner for each of the five geometric inputs, define the primitive-to-sketch/history expansion, preserve labels, visibility and inactive attachment state through qualified target owners, and refuse active or otherwise unrepresented semantics. The existing [radius/name bindings](FreecadCylinderNativeParameter2026.md) and [name-resource rule](FreecadCylinderNameResource2026.md) are reusable source knowledge, not a primitive conversion verdict. No authored datum or sketch may be falsely attributed to the FreeCAD source.

New independent source cases should separate sweep, each prism angle, placement, visibility, description and attachment changes before those members are admitted. Preserve the full source in every comparison. This tranche adds no primitive held-out source lock, native writer, lossless verdict or production coverage. See the [change entry](../../../Documentation/Changes/Solidworks/Inspection/Freecad/SolidworksFreecadCylinderPropertySemantics.md) and [specific scalar-role gotcha](../../../Documentation/Gotchas/Conversion/Freecad/Primitives/CylinderScalarRolesDoNotIdentifyGeometryDrivers.md).
