# SOLIDWORKS bare local prism topology

`MakeLocalPrism` generates ordered typed Parasolid nodes from a
neutral millimetre B-rep for the existing `EncodeLocalXmt` serializer.
The profile admits a single untransformed, outward closed solid with
two parallel XY section levels, one outer loop per face, one line per
edge, and one plane per face. Translated and concave sections are
admitted. The compiler refuses native provenance, entity attributes,
unsupported placements, local tolerances, orphaned topology and
inconsistent analytic trims.
[Compiler](../../../../src/convert/adapters/solidworks/Archive/Partition/LocalPrism/MakeLocalPrism.py)

The compiler uses the shared B-rep validator, topology ownership checks,
and prism geometry. Its BODY, solid and void regions and shells own the
generated boundary cells. Fins follow the actual loop, paired edge use
and incident vertex rotation. The compiler allocates resident indices
in the transmission order and computes persistent entity identifiers
in their separate domain. Positions are converted to metres, while
directions, topology links and wire fields retain the current
terminal-schema rules.
[Kernel format and encoder](../../../../re/solidworks/records/SdkLocalBodyTransmit2026.md)

Two independent guarded host runs reproduced all ordered nodes,
transmits and compression frames of the preceding compiler for a
translated rectangle, a concave prism, a skew triangle and a translated
pentagon. The four complete generated parts matched byte for byte with
all 48 logical streams. The existing rectangle and concave part hashes
also match their earlier receipt. Decoded boundary measurements agreed
with analytic area, volume and centroid, ten inadmissible inputs were
refused, and construction recorded zero runtime input reads.
The part comparison uses the research builder from
`82e0674c85562a1258fa4346ab4b5e8dbe7a0398` with the compiler and probe
in this change.
[Probe and exact digests](../../../../re/solidworks/measurements/2026/LocalPrismTopology01.json)

The checkpoint provides a compiler for the bare local transmit profile.
The existing part builder call site, owned-body attributes, native
verification and public conversion admission remain separate.
