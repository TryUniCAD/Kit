# Probe the baked FreeCAD label on a generated SOLIDWORKS body

The probe checks how a disclosed standalone FreeCAD `Part::Feature` label reaches a freshly generated SOLIDWORKS BaseBody and its named local storage group. It uses the previously checked native owner chain and the SDK at `42878d802e4d53ba1dd92528a67fa8122880cff0`. The supervisor verifies the disclosed lock and the underlying three FCStd files. It requires a single baked Shape owner for each standalone example and rejects the actual live `Part::Box` control. [Input owner audit](../../../Freecad/FreeCadBakedSourceOwnerAudit.md) · [Probe](../../../../../re/tooling/sw2026/imported_body_source/BuildBakedLabelPair.py) · [Exact receipt](../../../../../re/solidworks/measurements/2026/DisclosedBakedLabelPair01.json)

```sh
python3.14 -B re/tooling/sw2026/imported_body_source/BuildBakedLabelPair.py \
  /absolute/path/to/DisclosedSources01 /unused/external/DisclosedLabelPair01
```

Both arms use the `Baked01` document UUID `7490b28c-63bc-4aee-8a15-b20536063fab`, object `4041` and `Specimen.Shape.brp` SHA-256 `a592c24920093bc8bcdd580212620368f30a0bcd0d3908f3d1be5c1a413e9256`. The worker receives explicit box stations, configuration, labels and three ordinary document text fields. It creates a fresh box from the signed stations and calls the shared bare-import constructor. `SourceLabel` uses the authored `Disclosed Baked A`. `LabelOnly` uses the alternate `Disclosed Baked B` text from the separately verified second source. The second arm uses the first source's geometry and identity. The workers repeat model construction and obtain identical results with file access and child processes blocked during generation. The generated parts remain in the external directory. [Bare import constructor](../../../../../src/convert/adapters/solidworks/Archive/Construction/Part/Imports/MakeBareImport.py)

| Owner | Verified in the pair |
| --- | --- |
| Native self file and active configuration | Both headers resolve `C:\KitBakedLabelOnly01\Candidate\Baked01.SLDPRT` at fixed author epoch `1795300000`. Both arms keep `Default` active. |
| Feature and storage group | Strict read binds one unsuppressed imported feature, BaseBody ID `18`, to the actual LocalBodies group key. The group key and both exposed feature and body labels follow the arm's input label. |
| Managed body | The typed feature and configuration maps select atom `101` at actual local mark `3`. The raw kernel is the same 3,759 bytes in both arms. The strict B-rep binds to `sldprt:body:1`, with six faces, twelve edges and eight corners. |
| Source identity text | `FreeCAD Source UUID`, `FreeCAD Object ID` and `FreeCAD Shape SHA-256` are ordinary document custom properties. The separate `docProps/custom.xml` and its typed property readback are identical. |
| Visibility and presentation | Source `Visibility=True`, target feature unsuppressed, and ordinary single-body atom fields remain fixed. Native enumeration returns the same one visible solid in both arms. The probe uses the previously modeled ordinary ambient input. |

The label changes LocalBodies, Config-0-ModelHeader, ResolvedFeatures, Header2 and KeyWords. Each arm re-emits six actual typed archive streams byte-for-byte, including the regenerated LocalBodies envelope and the unchanged Config-0 and CMgr. Strict readback checks exact wire-unit corner coordinates, edge incidence, volume and centre against the computed source box. [Local owner reader](../../../../../src/convert/adapters/solidworks/Core/TypedResolved/BodyNames/Local/ReadLocalOwner.py) · [Document text input](../../../../../src/convert/adapters/solidworks/Archive/Construction/Metadata/Properties/PartTextInput.py) · [Visible-body enumeration](../../../../../re/solidworks/records/AtomManagerBodyEnumeration2026.md) · [Body label sequencing](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodies/LocalNameReadPrecedesMetadataBinding.md) · [Wire-unit station comparison](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/LocalBodies/LocalBoxStationsUseWireUnitRoundTrip.md)

The native contrast staged each verified output at the same embedded
task-owned locator. Two fresh SOLIDWORKS 2026 SP05.2 controls bracketed
both open, rebuild, save and fresh reopen lifecycles. All four candidate
processes reported zero open warnings, open errors and rebuild diagnostics.
Both arms retained the distinct BaseBody and body caption, one visible
solid and the same three document custom text values. All 232 geometry
checks passed. The measured volume is 2,761.41796875 mm³, area is
1,445.28125 mm², and centre is `(3.8125, 20.125, 7.8125)` mm.
[Native observer](../../../../../re/tooling/sw2026/imported_body_source/ObserveBakedLabelContrast.py) ·
[Native receipt](../../../../../re/solidworks/measurements/2026/DisclosedBakedLabelNative01.json)

This diagnostic preserves the disclosed label in the target behavior.
The complete FCStd carrier and its provenance, element-map metadata,
local tolerances, assigned material and presentation remain open.
[CAD success criteria](../../../../Reference/Operations/CadSuccessCriteria.md)
