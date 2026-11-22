# Design-only cylinder reads use the summary name

A generated attached circular boss can have a complete implicit
kernel name while its design-only read still displays the existing
summary name. The two disclosed writer candidates return
`RoundBoss` and `CurveBoss` in strict full reads, with implicit
kernel ownership bound to the actual output atom. Design-only
reads return `Body 1` and `Solid Bodies` for those same bytes.
Both modes retain the actual boss creator and both D1 drivers.

Use the full strict geometry read to verify the native body name
for these profiles. The design-only name reports available summary
state. [Disclosed comparison](../../../../../../../re/solidworks/records/SdkConcentricChildModel2026.md)
