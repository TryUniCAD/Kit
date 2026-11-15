# Circle marker placement on the pinned 2026 image

Status: **partial — static rule recovered; no curve-family lock or generated-output acceptance**

This record describes native construction and solver-update rules. It does not
implement a writer, inspect held-out native streams, or establish that an
emitted curve opens, rebuilds or remains editable. No oracle, repository module,
local test or shared REA session was executed for this investigation.

## Binary identity and evidence method

| Image         | SHA-256                                                            | Preferred image base |
| ------------- | ------------------------------------------------------------------ | -------------------- |
| `sldmodu.dll` | `569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e` | `0x4b140000`         |
| `sldmgu.dll`  | `99b6382da64df9fd37ca04720c210eaadc6750feb8cdeae6dd1289865da56e7c` | `0x31dd0000`         |

Both licensed images remain outside the checkout. Addresses below are preferred
virtual addresses in the named image. Static evidence came from bounded
`llvm-objdump` instruction ranges, PE import/export metadata and little-endian
binary64 constants in those exact images. No vendor listing is reproduced here.
An objdump heading can name the nearest earlier export; it does not establish
the name or entry of an unexported helper.

## Native search rule

`sgArcHandle::findUniquePointOnCircle` is exported at model address
`0x4c560e50` and returns at `0x4c561047`, with a success tail at
`0x4c561048`–`0x4c561081`. Its inputs are the sketch, centre, radius, angular
step, normal and an output point. The return is an integer success value, not
a point count.

| Quantity                                   | Native value                                                            | Evidence                                                                        |
| ------------------------------------------ | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Radius admission and point-query tolerance | `1e-7`                                                                  | Constant `0x4cdd64f0`, radius comparison `0x4c560eb7`, query setup `0x4c560fc6` |
| Full-turn angle                            | `6.2831853071796`                                                       | Constant `0x4cdfec80`, division at `0x4c560eca`                                 |
| Ordinary construction/update step          | `0.29670597283903666` radians, or 17 degrees using the native full turn | Constant `0x4cf85090`; construction load `0x4c4b8080`, update load `0x4c516de9` |
| Construction-only search-failure angle     | `3.438298626428837` radians, or 197 native degrees                      | Constant `0x4cf85098`, load `0x4c4b80db`                                        |

For the positive finite ordinary step, the instruction sequence
`0x4c560ece`–`0x4c560f09` computes the integral floor of full-turn/step.
The resulting bound is 21. The loop starts at one at `0x4c560f24`, forms
`angle = index * step` at `0x4c560f74`–`0x4c560f7c`, and continues only while
the index is less than the bound at `0x4c560fe5`–`0x4c560fe7`.
Consequently the ordinary candidates are 17, 34, ..., 340 degrees, in that
order. It does not try zero or 357 degrees.

For each candidate, `getCirclePointAtAngle` at `0x4c561490` computes the
position. The search calls `sgSketch::pointExists` at `0x4c560fda` with that
position, tolerance `1e-7`, mode zero and excluded index `-1`. It accepts the
first false return, copies the candidate to the output at `0x4c561053`, and
returns one at `0x4c56107c`. Exhaustion or radius below `1e-7` returns zero;
the output is not assigned by that failure path. An unordered radius comparison
also takes that failure branch. No general invalid-step contract is claimed.

## Coordinate construction

`getCirclePointAtAngle`, `0x4c561490`–`0x4c561647`, creates the initial basis
vector `(1,0,0)` and the reference normal `(0,0,1)` at `0x4c5614dc`–
`0x4c561511`. If the requested normal is not parallel to the reference normal,
it forms reference-normal cross requested-normal and rotates the initial basis
through the oriented angle between those normals. It then rotates the resulting
basis by the candidate angle about the requested normal, multiplies by radius,
and adds the centre at `0x4c56158c`–`0x4c5615d7`.

The import bindings establish the bounded mathematical operations:

| Model import slot | Mathematical operation         | Math-module target                    |
| ----------------- | ------------------------------ | ------------------------------------- |
| `0x4cd3a978`      | Vector cross product           | `0x31f1a050`                          |
| `0x4cd3aab0`      | Parallel-vector predicate      | `0x31f1b1e0`                          |
| `0x4cd3ab98`      | Oriented angle between vectors | `0x31f1bb20`                          |
| `0x4cd3abc0`      | Rotation transform             | `0x31f24670`                          |
| `0x4cd3aaf0`      | Apply transform to vector      | `0x31f1a6f0`                          |
| `0x4cd3a5f0`      | Scalar times vector            | Imported scalar/vector multiplication |
| `0x4cd3a5b0`      | Point plus vector              | Imported point/vector addition        |

For normal exactly `(0,0,1)`, the first alignment rotation is skipped and the
local candidate expression is

`candidate(k) = centre + radius * (cos(k*step), sin(k*step), 0)`

The positive sine sign follows from the math-module rotation matrix at
`0x31e2cff4`–`0x31e2d140` and vector application at
`0x31f1a810`–`0x31f1a86f`, rather than from the function name alone.
`mg_RotateXform` calls that matrix routine at `0x31f2472d`.
Thus the ordinary isolated-circle first free marker is at 17 degrees when that
candidate has no native point match. This is a local-coordinate rule; a world
point still follows the independently established sketch-plane transform.

The mathematical expression is not a claim of binary64 identity with every
vendor math-library normalization and trigonometric operation. Near-parallel
normals, exact tolerance boundaries and arbitrary 3D normals require their own
bounded analysis and owner observations before promotion.

## Fresh construction and its distinct fallback

The existing arc-construction helper begins at model address `0x4c4b7f80`.
It first finds/inserts the centre with tolerance `1e-8` at `0x4c4b7fdd`.
The full-circle branch compares the input start and end through imported
`mgPoint_c::operator==` at `0x4c4b7fec`, derives the radius from start minus
centre at `0x4c4b8012`–`0x4c4b8025`, and invokes the search at `0x4c4b8091`.

If that search fails, this constructor computes the circle point directly at
197 degrees at `0x4c4b80db`–`0x4c4b80f0`; it does not repeat the uniqueness
query on that fallback. Either path then calls `sgSketch::addNewPoint` with
point type two at `0x4c4b812a`, and copies the returned index to both endpoint
locals at `0x4c4b812f`–`0x4c4b8131`. This corroborates the shared marker
identity rule without copying a saved coordinate. It does not prove that every
public circle-authoring route reaches this particular constructor.

## Solver replacement is conditional

The coordinate-commit helper begins at model address `0x4c5167d0` and ends at
`0x4c5172c8`. Its first point pass marks type-two points to skip ordinary solved
coordinate writes through `isUniqueCirclePoint` at `0x4c516915` and mask store
`0x4c51698a`. The later circle-specific path can still reposition such a marker.

That path excludes deleted arcs, requires its handle-admission helper
`0x4c5cec50` to return true, and applies separate solver-work gates. After
updating arc solver data, it requires a circle at `0x4c516edb`, a valid start
index, a nonnull point, and signed point use count at `+0xe8` no greater than
two (`0x4c516ef4`–`0x4c516f1e`). The aliased getter at `0x4b28e380` is exactly
a signed 32-bit load of that member; its exported unrelated owner name does not
change the point object passed here.

Let `v` be the old marker-to-centre displacement, `n` the solved circle normal,
and `r` the solved radius. The path compares `abs(r - sqrt(v dot v))` and
`abs(n dot v)` at `0x4c516f7e`–`0x4c516fc3`. Both below `1e-11` skip the
replacement entirely. The separate change counter increments only when either
quantity is greater than `1e-8` at `0x4c516fa8`–`0x4c516fb4`.
This distinguishes coordinate repair from the counted-change threshold.

When replacement proceeds, the helper first writes a provisional marker
`centre + r * anyUnitNormal(n,1)` at `0x4c51705c`. For exactly positive Z,
the math helper `0x31f1ab00` selects positive X through `0x31f1ab2b`, so the
provisional marker is `centre + (r,0,0)`. It next calls the same 17-degree
unique-point search at `0x4c5170c8`. Only a successful search causes the second
point write at `0x4c5170dc`. Search failure leaves the provisional marker;
this update path has no 197-degree fallback.

The update search radius is re-read through `sgArcHandle::getRadius` at
`0x4c51708b` after that provisional point write, and is passed in `xmm2` at
`0x4c5170c2`. It is not passed directly from the original solver-radius register.
The centre is likewise retrieved again at `0x4c5170a6`. Floating-point addition,
subtraction and the radius getter can therefore matter to exact binary64
reproduction even when their mathematical radius is unchanged.

An unchanged circle can therefore retain its current marker. A circle that
reaches the replacement path can select a different angle because another
sketch point occupies an earlier candidate. The isolated first-free result is
not an unconditional seam angle for every existing circle or every rebuild.

## Point-match scope and remaining boundaries

The used `pointExists` overload begins at `0x4c4ce590` and delegates to the
internal finder at `0x4c4dd8e0` via `0x4c4ce630`. For this call, mode zero
does not restrict matches to point type two, and exclusion `-1` excludes no
particular marker index. The finder obtains nearby point handles through
`iFindAllPointMatches` at `0x4c690860`, then rejects points with flag `+0x54`
mask `0x2` set, external entities and an explicitly excluded index
(`0x4c4dda45`–`0x4c4dda6b`). A nonnegative qualifying result makes the wrapper
return true; no result uses sentinel `-2`.

The spatial query has distinct new-sort and old-sort paths at
`0x4c690893`/`0x4c690a55`; this investigation did not close all numerical
boundary and sort-cache semantics in those paths. The 17-degree conclusion is
therefore conditioned on the first candidate having no qualifying native point
match. It must not be expanded into an unproved Euclidean-distance, box-distance
or all-point matching rule near `1e-7`.

## Exact next owner observation

The oracle owner can observe the exported search entry and leave around fresh
training-circle construction, then around an actual driving-radius edit. On
Windows x64, entry has sketch in `rcx`, centre-by-value backing pointer in `rdx`,
radius in `xmm2`, step in `xmm3`, normal backing pointer at entry `rsp+0x28`,
and output pointer at `rsp+0x30`. Record the pointed-to values before they are
destroyed and read the output only when signed `eax` is nonzero.

Record the native return from `pointExists` at `0x4c560fda` and the caller return
address to distinguish initial construction `0x4c4b8096` from solver replacement
`0x4c5170cd`. Capture the actual marker index and writes at `0x4c51705c` and
`0x4c5170dc` to separate provisional and accepted positions. This requests
measurements from the owner; this agent did not launch, attach to or automate CAD.

Any further acceptance claim still requires the family hash lock before writer
implementation and held-out generated-output measurements between healthy
controls. The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md#stopping-conditions)
state the stopping conditions as “success under every criterion on this page”
or “the end of the available context”. This static record does not satisfy
product acceptance.
