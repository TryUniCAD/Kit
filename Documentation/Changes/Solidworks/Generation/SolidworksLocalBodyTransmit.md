# SOLIDWORKS local BODY transmit serializer

The package can serialize complete, resident node graphs for the current
planar imported-body kernel profile. `EncodeLocalXmt` accepts ordered
`XmtNode` records generated from the neutral geometry and their optional
BODY attribute list. It computes the framing and first-use schema
descriptors from the package grammar. Invalid typed fields, counts,
geometry references and alternate schemas are refused.
[Serializer and reproduction procedure](../../../../re/solidworks/records/SdkLocalBodyTransmit2026.md)

Two independent offline runs emitted identical receipts. Bare and minimally
owned versions of two generated prisms matched both reference transmit and
frame bytes. The package reader preserved every typed record. Twenty-one
malformed inputs were refused. The measured format scope covers the
current single-solid plane-and-line local transmit. The integrated research
builder kept all four completed containers and their 48 streams byte identical.
[Measurements](../../../../re/solidworks/measurements/2026/SdkLocalBodyTransmit01.json)

The part archive serializer also serves parametric parts and local imported
bodies through the same configuration map. A local import registers its
generated body atom, activation mark and selected mark before serialization.
The shared path reproduced four native-accepted imported parts and six
signed box builds byte for byte, including all 120 logical streams.
Construction recorded zero runtime input reads. Public fallback qualification
remains open.
[Shared archive regression](../../../../re/solidworks/measurements/2026/SharedGeneratedPartArchive01.json)
