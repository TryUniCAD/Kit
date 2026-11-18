# Native circle boss end conditions and readback

The internal circle boss constructor now accepts canonical Front, Right and
Top supports. Its live end specification retains reversed blind depth,
mid-plane total depth or two independently driving blind lengths. Each
case uses the same actual part, sketch and feature owners and the same
archive serializers.

The public reader recovers the actual end condition, orientation and active
dimension owners from the linked 2026 archive. A direct typed circle
projection recovers the analytic shape, radial driver and fixed centre
when the older marker-based path lacks their bindings. Use
`open_document(..., include_brep=False, include_tessellation=False)` to
inspect the editable features and parameters.

Four disclosed generated parts pass 40 complete stream comparisons.
The earlier two Front Plane candidates retain their exact file hashes.
Fourteen fresh SOLIDWORKS 2026 SP05.2 processes pass 530 numeric checks
through radial and depth edits, saves and fresh reopens. Twelve additional
public SDK read processes verify the four generated parts and their first-save
and edited derivatives. All 24 Config and Resolved streams re-emit exactly.

The [field and acceptance record](../../../../re/solidworks/records/SdkCircleEndConditions2026.md)
and [measurement receipt](../../../../re/solidworks/measurements/2026/SdkCircleEndConditions01.json)
bind the generated files, native controls and reader results. Held-out
qualification and the public circle write route remain open.
