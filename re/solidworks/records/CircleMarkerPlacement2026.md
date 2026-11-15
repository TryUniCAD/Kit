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
and arbitrary 3D normals require their own bounded analysis and owner
observations before promotion. The finite collision endpoint rules are
established separately below; their runtime corroboration remains pending.

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

## Collision rule: ordinary finite local sketch points

Confidence: **confirmed static**, bounded to finite coordinates and coherent
native point indexes. Runtime corroboration is not yet present. This section
supersedes the earlier unknown coordinate-boundary classification.

The used `pointExists` overload begins at `0x4c4ce590` and delegates to the
internal finder at `0x4c4dd8e0` via `0x4c4ce630`. That finder explicitly passes
eligibility flag one to `iFindAllPointMatches` at `0x4c4dd9e3`–`0x4c4dd9fb`.
Consequently mode zero is not permission to collide with every native point
type. The fixed eligibility predicate is applied before the mode-specific tests.

### Point eligibility and owning coordinate frame

| Runtime member                  | Meaning in this predicate                                                 | Evidence                                              |
| ------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------- |
| Sketch `+0x08`                  | Pointer to its point-array object                                         | Getter `0x4b285140`                                   |
| Point-array object `+0x08`      | Contiguous point data; point stride `0x158`                               | Array-index calculation `0x4c692eb5`–`0x4c692ec5`     |
| Point `+0xc8`, `+0xd0`, `+0xd8` | Stored binary64 X, Y, Z                                                   | XY loads `0x4c692ed3/0x4c692edd`, Z load `0x4c4ddac7` |
| Point `+0x18`                   | Owning sketch pointer, required nonnull                                   | `0x4c490e58`–`0x4c490e65`                             |
| Point `+0x48`                   | External-reference pointer                                                | `0x4c3e2031`–`0x4c3e204c`                             |
| Point `+0x54`                   | Low-word flags: masks `0x1`, `0x2`, `0x4` participate below               | `0x4b340f10`, `0x4c4dda45`, `0x4c3e1cef`              |
| Point `+0xb0`                   | Signed 32-bit nonzero alternative to flag mask `0x4` for referenceability | `0x4c3e1ce0`–`0x4c3e1cf9`                             |
| Point `+0xe4`                   | Signed 32-bit native point type                                           | `0x4c490e5c`                                          |
| Owning sketch `+0x450`          | Nonzero admits type ten as an additional special case                     | `0x4c490e67`–`0x4c490e75`                             |

Virtual slot `+0x138` in the point vtable installed at `0x4c49099f` targets
`0x4b340f10`, which returns true exactly when flag mask `0x1` is clear.
Both query engines require that result. Both also invoke `0x4c490e40`, the
point-referenceability predicate, because the eligibility argument is one.
It requires:

1. Flag mask `0x1` clear.
2. Point `+0xb0` nonzero or flag mask `0x4` set.
3. A nonnull owning sketch.
4. Type in `{0,1,3,4,9,11,12,14,17}`, or type ten with owner `+0x450` nonzero.

The normal type set is the bit test against native mask `0x25a1b` at
`0x4c490e80`–`0x4c490e8d`. Type two is absent. Existing full-circle marker
points therefore do not obstruct a candidate. Ordinary type-zero circle
centres and line endpoints can obstruct it. Type-one origin points count only
if they are actually in this sketch's point collection; no global model-origin
query is present.

The internal finder then rejects flag mask `0x2`, external points and the
excluded index at `0x4c4dda45`–`0x4c4dda6b`. With the caller's argument one,
the external predicate at `0x4c3e2020` returns true exactly when `+0x48` is
nonnull for these surviving points; its drawing-detachment exception is only
reachable for argument zero. Excluded index `-1` excludes no valid point index.
Mode zero skips both the exact-type filter and the mode-one additional
filter. Creation-ID preference chooses which qualifying index is returned;
it cannot change the existence Boolean because every surviving nonnegative
index also updates the fallback index at `0x4c4ddb58`–`0x4c4ddb5f`.

The XY comparison reads the point payload directly, and the candidate is
passed unchanged from `getCirclePointAtAngle`. No model-to-world, view or
screen transform appears in this comparison. For an ordinary local 2D sketch,
both inputs are in that sketch's local frame. World-plane placement does not
rotate or scale the collision tolerance. Z is ignored when `is3D` is false.
For local 3D points, the final filter is `abs(candidate.z - point.z) <= tolerance`
at `0x4c4dda8c`–`0x4c4ddad6`; old-sort query paths also perform the same Z test
at `0x4c691bb1`–`0x4c691bf3` and `0x4c691f61`–`0x4c691fa3`.
The exported `is3D` getter at `0x4c4bd140` reads cached sketch `+0x568`; value
`-1` delegates to owner profile `+0x368`, virtual `+0x1a0`. Handle-level
transformed/block points are outside this ordinary local-point scope.

### Exact XY endpoint conditions

Let `q` be a candidate, `p` an eligible point, and `t=1e-7`. Each native bound
is computed as an individual binary64 subtraction or addition. Comparisons
must use those rounded bounds; substituting a Euclidean distance or even
`abs(p-q) <= t` can change a boundary decision.

| Native point-index engine | X condition, with the identical condition on Y | Evidence                                                                                                                               |
| ------------------------- | ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| New coordinate trees      | `fl(q.x-t) <= p.x < fl(q.x+t)`                 | Both tree searches use lower-bound comparisons at `0x4c693f10` and `0x4c693f30`; iteration excludes the upper iterator at `0x4c69406f` |
| Legacy sorted arrays      | `fl(q.x-t) <= p.x <= fl(q.x+t)`                | Lower-bound comparison at `0x4c692ee5`; upper-bound comparison at `0x4c69323b` advances past equality                                  |

The new engine's `0x4c693cf0` invokes its coordinate-range helper twice, with
axis zero at `0x4c693d51` and axis one at `0x4c693da4`, then intersects the
two index sets at `0x4c693dee`. The old engine likewise intersects X and Y
matches at `0x4c691b34` and `0x4c691ee4`, rather than evaluating radial
distance. Its two old array pairs are processed separately and their results
are combined. Both admit a corner point with X and Y each near the permitted
tolerance even when its Euclidean distance exceeds `t`.

This is an actual endpoint difference between native engines, not a spelling
difference for a shared symmetric predicate. Lower endpoints are inclusive
in both. Upper X/Y endpoints are exclusive only in the new engine. When no
qualifying point lies on an upper X/Y boundary, the two finite local predicates
agree. The Z comparison, when enabled, retains the inclusive absolute-difference
test described above.

### Native engine selector and implementable neutral rule

`isUsingNewSortArrays` at `0x4c6940b0` obtains `SldSession_c::Environment` through
import slot `0x4cd3c498` and calls environment virtual `+0x1b0`. It selects the
new engine only when that Boolean is true and all four old-sort counts at
sketch `+0x2a8`, `+0x2c8`, `+0x2e8`, `+0x308` are zero. It allocates the
tree holder at sketch `+0x328` if needed. Otherwise it selects the legacy
engine, converting an existing tree holder as necessary. These exact gates
are at `0x4c6940cb`–`0x4c69412c`. No current value of the external environment
Boolean was measured, and it must not become a guessed writer constant.

For a neutral ordinary local sketch with coherent native indexes, the search is
therefore implementable as an ordered candidate loop over the generated native
point graph: apply the eligibility fields above, test the engine-specific XY
box and optional Z condition, and reject a candidate if any point survives.
Earlier marker points do not enter this collision set. Centre and ordinary
endpoint coordinates come from the same neutral sketch, not a saved-file table.
For an engine-independent result, compute the result under both endpoint rules
and require that the selected angle agree. A boundary-sensitive case remains
unproven until the engine state or a canonical-input rule is established.

Index-cache construction, loaded stale indexes, nonfinite coordinates,
transformed block points and external-reference geometry are outside this
proved neutral-construction rule. No arbitrary cache value or environment
preference is supplied by this record.

### Function identity ledger

Hashes below cover raw `.text` bytes in each half-open preferred-VA range.
Non-leaf ranges come from the pinned image's PE exception-directory
`RUNTIME_FUNCTION` entries. Leaf ranges end at the decoded return and are
explicitly labelled. They are hashes of external binary evidence, not copied
vendor programs or writer data.

| Boundary                            | Range, end exclusive      | SHA-256                                                            |
| ----------------------------------- | ------------------------- | ------------------------------------------------------------------ |
| Unique circle search                | `0x4c560e50`–`0x4c561083` | `250094a7e230f70bf3fd6f2ac249b2538df6e287795fa171525b2cf8b40e6b52` |
| Used point-exists wrapper           | `0x4c4ce590`–`0x4c4ce699` | `1e10e3d395a55a69d734781a0a4212f39b4e1cdefc871c3ada04e27d2cb6d00a` |
| Internal point finder               | `0x4c4dd8e0`–`0x4c4ddc17` | `2d9d71418a2698823bb5fb8be9a42520dabe5797008b018f367cad337729c864` |
| Nearby-point dispatcher             | `0x4c690860`–`0x4c690a7c` | `602f6a72166d7a8f43ef246dff8cd9a0b0eb4f86775dd1aa6b71ee2657ec6e1d` |
| Legacy XY intersection and Z filter | `0x4c691870`–`0x4c692110` | `b53276b576c617901e6f3491394f3f07336ad70ded1fdd95ecbf1dae2c564e06` |
| Legacy coordinate bounds            | `0x4c692cc0`–`0x4c693435` | `cdb670b243425ef37e1301ba7f69694f928a01e193b2b4b499a11a20a6dab216` |
| New XY intersection                 | `0x4c693cf0`–`0x4c693eb6` | `49bfc916debf8f61ff012af45cf817a914d6a5843d96adb539202a29c1249465` |
| New coordinate bounds               | `0x4c693ec0`–`0x4c6940a2` | `bb36bda96bf8da5abed380746ac197581dc260f5a736565cd4816c6bb6871a06` |
| Index-engine selector               | `0x4c6940b0`–`0x4c69419a` | `9d5087f56340118a60c00249cf6c2d8f4d112b0cee8dae56c8eded410b124107` |
| Point referenceability              | `0x4c490e40`–`0x4c490e97` | `61e59ee97f342237a8b5c42b4f9e82e59658a743895428ecefa78b46950933c3` |
| External predicate                  | `0x4c3e2020`–`0x4c3e207e` | `9c101b202ee0b6289b88364970e566a9e995c287f89729444e5ed9e736b9df93` |
| Referenceability base, leaf         | `0x4c3e1ce0`–`0x4c3e1cfa` | `88fcb3fcb5f2bf2667857e3a05e5aa651e2c267671acddaea9ee32d6f7cf0ae6` |
| Point alive predicate, leaf         | `0x4b340f10`–`0x4b340f1a` | `32f368a3881482747c86cee468d3d86f6625e94f1973122ff7f5a93326ea57e6` |
| Point-array getter, leaf            | `0x4b285140`–`0x4b285145` | `fc46ea8acdf166d47f2230b3d3975fbd0a4a0f5c898b7c2b2ec854359cb94b85` |

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

Observe naturally occurring `isUsingNewSortArrays` calls at `0x4c6940b0` and
their signed `eax` return, together with sketch identity, the four old-sort
counts and tree-holder pointer. The getter can allocate or convert indexes, so
an observer should record actual native calls rather than invoke it to inspect
state. A boundary probe needs separate lower and upper X/Y equality cases and
a qualifying ordinary point, rather than a type-two marker that the predicate
will exclude regardless of distance. No observation may use or close the
user-owned unsaved drawing presently occupying the shared VM.

Any further acceptance claim still requires the family hash lock before writer
implementation and held-out generated-output measurements between healthy
controls. The [CAD success criteria](../../../Documentation/Reference/Operations/CadSuccessCriteria.md#stopping-conditions)
state the stopping conditions as “success under every criterion on this page”
or “the end of the available context”. This static record does not satisfy
product acceptance.
