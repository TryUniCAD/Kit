# Partial Top and Right boss revolves

The normal SOLIDWORKS part writer accepts a single ordinary
rectangular boss revolve on the canonical Top or Right plane.
The neutral part supplies the closed contour, four sketch
relations, the selected construction line, and one positive
partial-turn D1 with its signed sweep direction. Call
`write_document` with destination format `solidworks.sldprt`
and a named part path, or supply the final part path when
writing to a binary stream.

The registration uses the shared generative part preparation.
Full turns, other support frames, extra features, and
unrepresented source owners fail closed.
[Independent native preparation evidence](../../../../../re/solidworks/measurements/2026/SdkPrincipalRevolveHeldoutNative01.json)
