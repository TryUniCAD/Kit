# SOLIDWORKS drawing property sections

The research drawing constructor now writes the native property-section and name-dictionary framing for its six neutral sheet-index values. It computes the typed text records, IDs and dictionary entries from the neutral mapping. The same helper accepts other ordered text mappings. [Research constructor](../../../../../re/tooling/sw2026/builders/PropertySections.py)

The previous generated XML placed its values inside a second `Properties` element. The native reader selects `propertySection` and separately loads name-dictionary records. The corrected format uses the source-proven user-defined section GUID, ordinary text type and fresh-ID allocation rule. [Source evidence](../../../../../re/solidworks/records/DrawingPropertySections2026.md)

Two guarded generator processes produced identical complete drawings with zero runtime input-file access attempts. Only the property XML changed among seven logical streams. Structural inspection and the public drawing reader retained the expected sheet and scale.

The native trial used nine distinct processes with healthy pristine, repacked and reduced-native save/reopen controls. The corrected generated drawing opened with zero errors and warnings and accepted the scale edit, but SaveAs returned `[false, 1, 0]`. The trial was interpretable and exited 3. This grammar correction is insufficient to repair native saving; the generated drawing has no passing fresh-reopen evidence. [Native result](../../../../../re/solidworks/measurements/2026/DrawingBlankPropertySectionsNative01.json)

`InspectBlankDrawingPropertySections.py` verifies the frozen neutral request, construction receipt, stream comparison, observer hash and input packet before the native trial. Pass `--packet-sha256` and `--runner-sha256`. Its `--verify-only` mode checks custody on the host. Native exit 0 requires the generated drawing to pass the controlled scale edit, SaveAs and fresh reopen. [Observer](../../../../../re/tooling/sw2026/InspectBlankDrawingPropertySections.py)

This change covers research construction of ordinary text properties. Additional property types, equation states and production writer admission remain unqualified. The existing blank-drawing oracle packet measures the edit, save and reopen boundary. [Related gotcha](../../../../Gotchas/Conversion/Solidworks/Archive/Drawings/DrawingPropertiesNeedNameDictionaries.md)
