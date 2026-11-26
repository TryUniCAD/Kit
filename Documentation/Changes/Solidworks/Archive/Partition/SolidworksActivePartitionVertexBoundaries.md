# SOLIDWORKS active partition vertex boundaries

The SDK can recover B-rep geometry for a current SOLIDWORKS 2026 active
partition when the byte scanner mistakes data inside a fin for a vertex.
The strict SLDPRT reader uses the recovery automatically if the existing
geometry decoder returns no model. Passing `include_brep=False` continues
to read document data without requesting geometry.

For recovery, the SDK validates the complete `SCH_3701250_37102_13006`
typed graph. It uses typed record boundaries to recover the full vertex table
and verifies the vertex-to-point links in both directions. The original
vertex tolerance must agree with the typed value. Each replaced scanner
entry must start within a real fin that names the same vertex. The SDK
verifies the other topology boundaries used by the geometry builder and
binds straight edges and planar faces to their typed carriers. A different
schema, unsupported carrier or hierarchy, ambiguous ownership, or failed
geometry validation keeps the existing result. Terminal fin orientation
continues to govern the resulting model.

The disclosed generated five-line prism previously returned a body record
without B-rep geometry. The strict public read now yields one closed solid
with seven faces, 15 edges and 10 vertices, and signed volume
12,343.0395 mm³. Its generated four-line control and the independently
authored P03 control retain their existing B-rep geometry and positive
winding. This reader change establishes device-free geometry recovery within
the stated scope. Native opening, parametric editing and lossless file
conversion require separate evidence.

A fresh prior-versus-updated comparison exercised six immutable inputs in
strict default, B-rep only and model-only modes. The five-line part changed
only when B-rep was requested. The other five inputs had identical canonical
documents in all modes, including the older schema and terminal fin
orientation controls. The ordered raw partition and delta payload hashes
and body counts were unchanged in all 18 comparisons. A separate generated
vertex probe preserved a finite tolerance of 0.00001 mm and refused invalid
values before geometry recovery. Wrong-owner line and plane controls also refused recovery.

The maintained integration case passed in 12.39 seconds through the
repository's planner, tracked shard and merged report. It checks public payload
extraction, older and unsupported profiles, malformed active framing, and
wrong-owner line and plane records. [Integration case](../../../../../tests/Convert/Solidworks/Partition/CurrentVertexTests.py)

A six-edge part authored and sealed before implementation independently
reproduced the missing vertex point failure. The frozen reader recovered a
closed solid with eight faces, 18 edges and 12 vertices. All eight rings
had outward orientation. Signed volume was 12,145.0224609375 mm³,
matching the independent calculation. The original source, raw partition
and delta payloads, and model-only projection stayed unchanged.
[Held-out method](../../../../../re/solidworks/records/SolidworksCurrentFinOrientation2026.md#held-out-active-partition)

A separate native-saved P03 control still returned no B-rep. The prior
geometry path reported a missing vertex use. The new fallback stopped at
unmapped typed record kind 133 before it could replace a vertex table.
Both public projections matched the pinned reader byte for byte.
[Native P03 lifecycle](https://github.com/TryUniCAD/Kit/pull/338)

[Record-boundary diagnosis](https://github.com/TryUniCAD/Kit/pull/334)
· [Terminal fin orientation](../../../../../re/solidworks/records/SolidworksCurrentFinOrientation2026.md)
