# SOLIDWORKS verification dispatch

The native reader verifier can now inspect a SOLIDWORKS part when the dynamic COM
binding returns a feature, geometry object, or scalar directly for a member with
no arguments. It calls the member only when the binding returns a method.

The verifier reads the application's sketch transform as affine data. It
requires finite values and unit scale. It also supplies a typed null component
when reading extrusion selections in a part or saving an edited part without
export data. The native base-feature flag
distinguishes a body-creating extrusion from a cut or a merge.

Use the existing [native reader verification](../../../Automation/AutomaticNativeReaderVerification.md)
command. The change does not expand the verifier's supported feature families.
The native reports retain missing semantic fields and comparison failures.

On SOLIDWORKS `34.4.1`, the original verifier failed both bracket controls with
COM `0x80020003` at `FirstFeature`. A diagnostic run of the repaired verifier
measured the same stock control with one body, 8,000 mm³ volume, center
`[20, 10, 5]` mm, six faces, twelve edges, and eight vertices. The diagnostic
identified further failures in sketch transforms and part selection before
those calls were repaired. This check does not qualify any conversion route.

See [native part selection marshaling](../../../../../Gotchas/Research/Workers/SolidWorks/PartSelectionComMarshaling.md).
