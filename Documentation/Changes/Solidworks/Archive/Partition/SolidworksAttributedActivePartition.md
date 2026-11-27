# SOLIDWORKS attributed active partition geometry

The strict SLDPRT reader can recover the boundary geometry of a bounded
current-format active part with attributed vertices. Normal decoding and
the existing fin-shadow repair keep their original precedence. The new
path requires a complete typed graph and supplies a solid only when the
saved topology and source annotations pass its checks. It refuses alternate
shell-face attachments and verifies that the face orientation agrees with
the directed fin ring on its positive-sense plane carrier.

Open the part through `convert.open_document` or `kit decode`. The
supported profile contains one closed planar solid with line edges.
Each face must have one quadrilateral loop.
The reader validates saved free trim and geometric-owner
relationships without treating the trims as direct edge geometry.
It preserves the active payload, including the attributed vertices,
and projects the supported unchanged face identifiers and annotation
orders. The model-only and raw extraction paths retain their existing
behavior.

The retained component fixture is an exact, privacy-checked active and
delta member from the previously measured 12 mm native save. It keeps
the original partition digest and excludes the private source archive.
The component test uses the installed SDK's ordinary partition transport
and active part reader. The private whole-file checks separately cover
the public SDK and CLI using the intact original source.
[Component fixture provenance](../../../../../re/solidworks/Fixtures/PartitionAttributes/Manifest.json)
· [Complete active owner research](https://github.com/TryUniCAD/Kit/pull/345)
· [Prior native measurements](https://github.com/TryUniCAD/Kit/pull/338)
· [Alternate shell attachments](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/Topology/DerivedShellsCanHideAlternateFaceAttachments.md)
· [Directed ring and face sense](../../../../Gotchas/Conversion/Solidworks/Archive/Partition/Topology/FaceSenseMustAgreeWithDirectedRing.md)

The installed SDK and CLI agreed on one closed 9,600 mm³ solid with
six faces, twelve edges, eight vertices and the measured centroid
(20, 10, 6) mm. Both supported face annotation orders and all six
unchanged face identifiers were recovered. Model-only JSON and the
three original exported geometry payloads were byte-identical to the
previous reader's results. The actual private source bytes remained
unchanged. No native session ran for this decoder verification.

Both regression modules passed through the repository's existing planner,
tracked shard and completeness report. The older module keeps its six-case
matrix. The new installed-component test covers the measured attributed
geometry and 21 refusal cases, including contradictory shell, face and plane
records.
Independent screening verified the checked-in member and both expanded
frames. The original source archive stays private.

Unsupported carrier, fin, owner and attribute relationships remain
outside this geometry profile. Whole-source conversion and writer
acceptance are separate work.
