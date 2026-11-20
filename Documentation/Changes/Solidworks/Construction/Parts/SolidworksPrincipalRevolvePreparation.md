# Principal-plane revolve preparation

The internal ordinary boss revolve constructor reads the selected
support frame from the neutral model. It supports origin-centred
canonical Front, Top and Right planes. The sketch contour and
construction line retain their sketch-local coordinates. The axis
wrapper derives its model-space start, direction and span from that
line and frame. The effective axis of the neutral angular operation
determines the sweep direction.

The linked archive keeps the actual profile, plane, selection and
driving angle owners in the shared model. Use the internal
`PrepareRevolve` operation with an explicit final part path and
writing event. Its current scope is one rectangular boss, a selected
construction line, a single positive angle and the three canonical
frames.

Four authored documents generated path and named-stream outputs
with identical bytes and zero guarded external accesses. All 40
measured streams re-emitted exactly. Strict readback recovered the
closed solids, actual sketch support and live angle. Four unsupported
support and axis variants refused before output.
[Preparation receipt](../../../../../re/solidworks/measurements/2026/SdkPrincipalRevolvePreparation01.json) · [Disclosed controls and sealed inputs](../../../../../re/solidworks/records/PrincipalRevolveSources2026.md)
