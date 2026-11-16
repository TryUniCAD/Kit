# Circle adjacency registration, SOLIDWORKS 2026

Status: **confirmed bounded static rule; fresh generated-circle acceptance pending**

Two endpoint-use events do not require two retained adjacency handles. The native
registrar tests for an equivalent handle before allocating another clone. For an
otherwise unused ordinary circle, the start and end refer to the same point.
The first endpoint registration supplies one `h1`; its opposite-point lookup and
the later endpoint role find that existing handle. `h2` remains null while the
point's segment-use count still increases twice.

This corrects the earlier two-clone inference in
[CurvedSketchConstruction2026.md](CurvedSketchConstruction2026.md#common-fields-and-point-roles).
The source corpus's 24 full circles all have the predicted single `h1` and null
`h2`. That agreement corroborates the rule but does not observe its execution or
establish generated held-out acceptance. Native point-store cleanup is real,
but it is not needed to explain this particular source observation.

## Identity and evidence

The [companion record](CircleAdjacencyRegistration2026.json) binds every function,
full body extent, digest and selected vtable slot. The target is SOLIDWORKS 2026
SP05.2, build `34.5.2.0604`, AMD64 `sldmodu.dll`, preferred base `0x4b140000`,
SHA-256 `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.

The independent inspection used the original PE section mappings, exception
directory and chained unwind ownership, then native disassembly. Eleven
functions have complete exception-directory/chained extents. Two getters are
decoded leaves through their final return. No vendor listing or binary bytes are
included. REA's native provider remains unavailable in the current session.
No CAD process, VM call, codec, schema or local test executed for this finding.

| Native operation | Address | Bounded evidence |
| --- | --- | --- |
| Arc permanence | `0x4c5635e0` | Roles zero, one and two pass the same segment handle in start/end/centre order |
| Point use | `0x4c602c10` | Increments the point-use counter before endpoint adjacency registration; role two increments centre use |
| Endpoint registrar | `0x4c5f8460` | Tests current and opposite endpoint adjacency before inserting clones |
| Existing-equivalent check | `0x4c5f8060` | Checks both nonnull point slots through handle value equality |
| Handle equality | `0x4c5bce10` | Compares index, sketch and block identity, then runtime class in the concrete arc branch |
| Opposite endpoint | `0x4c5c7020` | Returns the opposite endpoint handle; equal circle endpoints retain the same point identity |
| Concrete arc clone | `0x4c55eb40` | Preserves target index, owner, block and concrete arc class |
| First empty slot | `0x4c5f7e40` | Allocates one clone into `h1` when empty, otherwise `h2` when empty |

The arc-handle vtable at `0x4d1c5ae8` binds clone slot `+0x128` and opposite-end
slot `+0x200` to those exact implementations. Its class getter returns runtime
class `0x4dafb0e8`. Equality in this concrete branch does not use object pointer
identity. Independent clones of the same arc can compare equal without becoming
the same allocated archive object.

## Bounded construction derivation

The stated branch requires an ordinary local 2D circle, a valid admitted arc
handle, nonzero sketch current-state field `+0x128`, initially empty marker
adjacency, and successful allocation. External, construction, replacement and
general branching cases remain outside this derivation.

1. Arc permanence registers its start point with role zero. Point use increments
   `fe8` before calling the endpoint registrar.
2. The current point has no equivalent adjacency. Its empty-slot branch creates
   one concrete arc-handle clone in `h1`.
3. The registrar checks the opposite endpoint. For this circle it resolves the
   very same point, whose new `h1` now compares equal. No second clone is needed.
4. Arc permanence registers role one. The same point's `fe8` increments again.
   Both endpoint adjacency checks already find the retained handle.
5. Centre role two increments centre `fe8` and `fec` without endpoint adjacency
   insertion. For an otherwise unused centre both slots stay null.

The resulting marker has `fe8=2`, `fec=0`, one owned `h1` and null `h2`. The
centre has `fe8=fec=1` and null adjacency. Counts, object allocations and repeated
semantic references are separate quantities. The radial value dimension owns a
different geometry handle even when it targets the same arc.

The native registrar also has admission, construction, capacity, replacement
and contour-state branches. This finding does not generalize the simple circle
sequence to arbitrary insertion, deletion or shared endpoint histories. It
does not infer that an unclassified field is a safe zero or optional cache.

## Refuted inference and remaining acceptance

The previous inference treated two endpoint role calls as two unconditional
adjacency insertions. It missed the existing-equivalent checks at
`0x4c5f84d3` and `0x4c5f8556`. That inference is refuted for the bounded branch.
The corrected rule derives one retained handle from actual native control flow,
not from fitting the source corpus's null `h2`.

`sgPoint::Serialize` can clear a pointer when its actual validity virtual returns
false. It remains a separate lifecycle rule and a useful tracing boundary.
No cleanup event or callback neutrality is claimed from static inspection.

The six held-out native payloads remain unread. No curve writer or generated
output is introduced by this record. A fresh builder still needs all field
rules and native rebuild, geometry, edit, save and reopen measurements between
healthy controls under the [CAD criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md).
