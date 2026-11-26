# Saved SOLIDWORKS active owner graph

The saved 12 mm P03 derivative has SHA-256
`dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115`.
Its current active payload has SHA-256
`af3dd2ac0b09608ef1d48207b0cce8d0a395fdc4adabd97a53522e12c4c9cf56`.
The development reader was the installed SDK from
[PR #340](https://github.com/TryUniCAD/Kit/pull/340), source tree
`3739be2f567a3285dd3dc725be9d0d07865a7b18`. The previous
[trim investigation](SavedTrimmedCarrierBoundary.md) stopped at kind 141.
[Retained native evidence](https://github.com/TryUniCAD/Kit/pull/338)

## Wire and owner evidence

The exact kernel used by the prior trim study declares kind 141 as
`GEOMETRIC_OWNER`. Its base and current layouts contain four scalar
references in order: `owner:p1003`, `next:p141`, `previous:p141`,
`shared_geometry:p1003`. The class uses the unchanged first-use marker
`ff`. The exact kernel's pointer gate accepts type 141 for `p141`.
Its class flag table admits the witnessed kind 30 and 133 targets for
`p1003`. This study does not qualify every kind that meets that abstract
predicate. [Layout](../measurements/2026/ActiveOwner/LoaderDescriptor.json)
· [Pointer predicate](../measurements/2026/ActiveOwner/LoaderPointers.json)

Only the two independently traced layouts are added to the research
walker's local dispatch. The existing typed cursor reads the other
records. The walk reaches the exact terminator with 189 records and one
live world. Every declared pointer resolves. An independent check
verified all 411 nonnull concrete pointer classes and reached every
record from the world. The walk never skips unknown records.

Kind 141 record 116 at body bytes `[3692, 3705)` links trim 46 and line
118. Record 123 links trim 6 and line 50. Both owner records have
singleton list links. Every line points to the same owner that names it.
The trims belong to the body's free curve list. No edge or fin
references either trim directly. Edges 110 and 84 use the respective
line bases. The typed trim intervals evaluate to those edge endpoints in
the recorded positive sense. Keep the free trims and owner links in the
source evidence when projecting boundary geometry.

## Why the general scanner misses vertices

All eight vertex records have reciprocal points. Three vertices,
indexes 68, 72 and 77, carry recorded attribute rows 75, 74 and 76.
Those rows bind back to their vertices and share the definition
`VERTEX_AUTOMATION_2_2001`. Their type-order chain is 75, 76, 74.
The other five vertices have a null first attribute reference.

The general reader's first-reference check rejects the three genuine
records with nonnull references. Its one-based missing attributes are
69, 73 and 78. The offline check reproduces the rejection on the saved
bytes and leaves the attributes intact. The existing fin-shadow repair
requires equal vertex rosters and addresses a different cause.
[Vertex verification](../measurements/2026/ActiveOwner/VertexAttributes.json)

The eight finite `next_at_vx` lists and the corresponding surface rotations
are separate. Each list has a null terminator and covers the same three
owner fins as its surface rotation. The pocket-specific comparison
refuses on this part: their orders differ at five vertices. The measured
boundary does not require changing either saved ordering.

## Geometry result and scope

The independent native comparison matches all 12 edge endpoint pairs,
24 directed fin uses, six outward face rings and eight physical vertices.
The separate 12 mm vendor control has the same 12 unordered endpoint
pairs. The existing typed table and model builders produce one
closed solid with signed volume 9,600 mm³, area 3,040 mm² and centroid
(20, 10, 6) mm. This lower-level projection checks the boundary
geometry. It does not attach source face annotations or change the
public reader. [Bound result](../measurements/2026/ActiveOwner/Boundary.json)

## Reproduce the offline checks

Set `$source` to the exact published-study derivative retained with its
native receipt. Use the existing [trim descriptor](../measurements/2026/TrimmedCarrier/LoaderDescriptor.json)
and this record's [owner descriptor](../measurements/2026/ActiveOwner/LoaderDescriptor.json).
Select an absent output directory and set `$walk` and `$vertexReport` to
the result and a new output file inside it.

```powershell
python -I -B re/solidworks/ActiveOwner/WalkKnownLayouts.py --trim-authority $trimAuthority --owner-authority $ownerAuthority --source $source --output $output
python -I -B re/solidworks/ActiveOwner/CheckVertexAttributes.py --source $source --walk $walk --output $vertexReport
python -I -B re/solidworks/ActiveOwner/CheckLowerTypedGeometry.py --walk $walk --native-record $nativeReceipt --output $geometryReport
```

The working full traces, independent comparison methods and licensed
kernel analysis remain in their private evidence folders. The repository
retains compact technical observations and reproducing methods. Every
verification in this tranche was offline. The public reader, production
SDK and writer were unchanged.
