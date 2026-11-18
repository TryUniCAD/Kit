# Generated SOLIDWORKS 2026 part from a FreeCAD origin box

Task `B04-SW2026-FCSTD-BOX` in PR #121. The disclosed source is
`recipe-0.21.2-F14a.FCStd` from CAD Fixture Recipes v1.23. Its strict neutral
read contains one `PartDesign::AdditiveBox`, three principal planes, one
active configuration and a single ordinary Body. The archive SHA-256 is
`2f0e5e20da3e8f6d2073a7c8dd654b0c5035ed142c2e0392a14de832cd82eb5d`.

`ProjectFreecadBox.py` checks the actual three source dimension owners,
unattached identity placement, empty expressions and material state, the
source object inventory, origin frames and the admitted source metadata
properties. It computes an origin-coincident four-edge profile and one
editable blind boss from the three positive lengths. The stored FreeCAD
analytic cache corroborates the eight expected corner points and topology.
All candidate geometry comes from the authored dimensions.

The target uses one active configuration, two independently driving sketch
lengths, one driving boss depth, a real origin relation and the original
feature label. The source property identities map to their generated native
driver owners. Source document title and comments become Summary fields.
The source license, UUID, dates, model identifiers and Body label become
literal file properties. Native display names for the three drivers and
direct body naming remain part of the open semantic comparison.

`SdkFreecadBoxProcess.py` accepts the actual neutral document and an explicit
native target path through stdin. Two fresh builds from the same strict
source and two builds from a separate frozen 5,105-file SDK closure emit the
same 12 streams and the same 9,971-byte file with zero runtime input reads.
The public SDK history read preserves 19 ordered model rows, all three
drivers and the 13 literal file properties. The default strict Parasolid
request reports a missing readable payload on the freshly generated file.
The history check explicitly disables B-rep and tessellation requests.

Eleven additional F14 inputs reject outside the scoped projection due to
active attachment, other authored entities or a different schema version.
The build verifies one disclosed source.
`InspectFreecadBoxNative.py` is prepared to measure the exact generated file,
the native body and metadata, independent length edits, a clean save and
fresh reopen between separate healthy controls. The
[build-only receipt](../measurements/2026/SdkFreecadOriginBoxBuild01.json)
binds the frozen candidate and measurement packet. Native acceptance,
original benchmark membership and the full public route remain open.
