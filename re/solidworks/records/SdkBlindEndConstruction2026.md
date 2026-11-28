# SDK blind end and parameter construction

Task `B04-SW2026-CONSTRUCTION`, owner `/root/flag_ownership`, delivery PR #121.
This is a construction continuation after the frozen public-reader tranche.
It owns only new `Archive/Construction/Blind` modules and its process evidence.
No prior reader file, shared builder, archive layout or Git state is modified.

The bounded exit condition is a complete ordinary forward-blind end-spec node
and its five role-specific parameter nodes, integrated with actual native stream
serialization from independently authored neutral inputs. Full feature/model
construction, public writer registration, native acceptance and C10 remain open.

## Evidence basis and scope

The component reuses the [profile/live-dimension construction ledger](ProfileConstruction2026.md),
[model and ID construction](ModelConstruction2026.md),
[current resolved grammar](ResolvedBodyGrammar2026.md) and its concrete runtime
descriptors. All model addresses below refer to the pinned 2026 module SHA-256
`569a081928ad24afac5408cc15a1034d18e89b2c5001428a64115a3cc497067e`.
This task adds no binary analysis, vendor software, native observation or held-out
input. The existing native constructor rules supply the evidence, not saved rows.

The implementation uses only the standard library and the shared `ArchiveNode`
and `RuntimeClass` object model. It imports no reader helper, research builder,
CAD bridge, file API or native runtime. It does not register a public writer.
The existing SDK field serializers own byte encoding, counts and shared archive
maps. This component creates object fields; it does not patch or emit a recorded
field program.

The target is archive version 19000. `BlindEndInput` takes the depth in metres,
an explicit direction Boolean and version. Only the ordinary forward direction
is admitted. Depth is finite and at least `1e-14`, matching the selected shared
dimension-domain restriction. Unsupported versions, reverse direction, Boolean
depths and clamped or nonfinite lengths reject before node construction.

## Parameter construction

`MakeBlindParam` accepts an actual validated input and one role from
`1,2,3,4,19`. Native extrusion constructor `0x4bad3ab0` creates the first four
displays. From-end constructor `0x4bad3e00` creates role 19 even when type zero
omits that display from storage.

| Field or subject                                | Class                    | Rule and provenance                                                                                                                                                                                   |
| ----------------------------------------------- | ------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Runtime descriptor                              | Derived vocabulary       | Roles 1, 2 and 19 select `moLengthParameter_c`; roles 3 and 4 select `moAngleParameter_c`. Native dimension factory slot `+0x3d8` targets `0x4c8214b0` or `0x4c821470`. All concrete schemas are one. |
| `moNodeName_c.f08` and parameter `f18`          | Derived object reference | Format `D` plus the supplied role integer, retaining a new name node. Native name factory `0x4c820f20` and parameter name setter `0x4c19c9b0`.                                                        |
| Parameter `f58`                                 | Input/derived            | Roles 1 and 2 take the authored depth; roles 3, 4 and 19 take their selected zero-angle or zero-offset input. Native constructor roles and setter `0x4c19cae0`.                                       |
| `f08=-1`                                        | Constructor state        | The parameter remains unassigned on this path. The actual persistent ID is dimension `f50`, allocated by `0x4c821c40`. It is not a placeholder node ID.                                               |
| `f0c=0`                                         | Constructor state        | Parameter constructor `0x4c19baf0` calls the flag routine `0x4c03ed90` with zero after the node constructor.                                                                                          |
| `f28=0x40000000`, `f2c=0`, `f20=""`, `f48=None` | Constructor state        | The recorded native node/parameter constructors supply the mask, secondary mask, empty text and absent alias name.                                                                                    |
| `f68=0`                                         | Setter state             | `0x4c19cae0` clears the alternate-value flag. No alternate `f60` field is needed in this branch.                                                                                                      |

Each invocation creates a new parameter and name object. No field offset,
object index, saved scalar, captured string or per-file value is supplied.
The writer derives the string length and object/class tags from those nodes.

## Complete end-spec field construction

`MakeBlindEnd` constructs exactly the 35 ordinary modern fields from the
end-spec constructor `0x4bad35c0` and the caller's retained graph references.
The selected type-zero, single-end calls are recorded at `0x4bad3ce5`.
Constructor states below apply to this factory. They are not universal values
for every saved end specification.

| Fields                                                                                                                                                    | Class                      | Rule                                                                                                                                    |
| --------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `f138`, `f90`                                                                                                                                             | Constructor state          | Null direction/reference pointers in this selected branch.                                                                              |
| `f08`                                                                                                                                                     | Derived from selected mode | One for the ordinary single-end mode.                                                                                                   |
| `f0c`, `f10`                                                                                                                                              | Declared mode vocabulary   | Zero for the forward and inactive reverse blind end conditions.                                                                         |
| `f8c`                                                                                                                                                     | Input projection           | The explicit admitted direction Boolean converted to integer. Reverse input is rejected.                                                |
| `f18`, `f20`, `fc8`, `fd0`                                                                                                                                | Input object references    | Retain the supplied forward/reverse distance and draft display nodes. No scalar replaces a live dimension.                              |
| `f88`, `has_f28`, `has_f48`, `fb8`, `fbc`, `fc0`, `fc4`, `fb0`, `fb4`, `fa8`, `fac`, `fd8`, `fdc`, `f12c`, `f130`, `f148`, `f14c`, `f150`, `f154`, `f158` | Constructor state          | The native constructor explicitly clears these scalar and presence fields. They share one independently authored zero-field vocabulary. |
| `fa0`                                                                                                                                                     | Constructor state          | Zero binary64 for the inactive constructor value.                                                                                       |
| `fe0`, `f100`                                                                                                                                             | Derived collection framing | Fresh empty object-array records. Their counts come from the actual fresh row lists.                                                    |
| `f128`                                                                                                                                                    | Constructor state          | One from the documented ordinary constructor.                                                                                           |
| `f140`                                                                                                                                                    | Input object reference     | Retain the actual caller-owned `moFromEndSpec_c`, including its runtime-only role-19 graph.                                             |

Every retained display must have one actual `moFeatureDimHandle_c` and the local
`ff0` dimension, with null external/cache references `fe8/f100`.
The concrete dimension/parameter classes, role-derived names, actual values and
assigned dimension IDs must agree. The five displays, parameters and persistent
dimension IDs remain distinct. An unresolved external-class placeholder cannot
stand in for a concrete class.

The caller still owns the dimension/handle/display constructors, model styles,
profile/body-feature/history graph and header ID allocator. This component does
not invent their fields. The caller allocates actual dimension `f50` values.
The primitive checks assigned and distinct IDs; the shared scalar serializer
retains the field-width domain checks for those caller-owned values.
The parameter's `f08` remains unassigned. The from-end type must be zero and its
retained display must carry the actual zero-valued `D19` graph.
See [dimension identities](../../../Documentation/Gotchas/Conversion/Solidworks/Model/Dimensions/DimensionAndParameterIds.md)
and [omitted dimensions](../../../Documentation/Gotchas/Conversion/Solidworks/TransientDimensionsConsumeIds.md).

## Process integration and proof boundary

The focused `SdkBlindEndProcess` receives only a neutral JSON request on stdin.
It initializes the existing research model constructor and codecs before the
strict runtime-input-read guard. It constructs a fresh part, then replaces only
its five parameter owners and end-spec node with the SDK constructors.
It never reads a vendor-saved file or obtains a model value from a fixture.

The actual SDK Config/CMgr/Resolved writers serialize the resulting graph.
The header SDK codec remains the existing generated-header bridge.
The comparison covers `Config-0`, `CMgr`, `Config-0-ResolvedFeatures`, its
`ModelHeader` and `Header2`. Baseline bytes are freshly generated from that same
neutral request in memory. They are not a template, runtime dependency or saved
native input. The manager context is decoded from the process's own generated
manager stream, independently from the Config map. Resolved serialization uses
the actual Config snapshot.

The permanent process case authors four- and seven-vertex polygons with different
depths. It checks the five actual stream comparisons, full in-memory round trip,
input-dependent lengths, graph identities and nine invalid construction cases
per model. The final archive is composed from computed streams. The process
reports native/public writer qualification as false.

The initial 15-file code snapshot has SHA-256
`fdc06fe6cf119b4ba70c471ffe1075a26c4a471a748ad96201144fb943d73a3a`.
The parent independently froze 4,006 source paths, source closure SHA-256
`119bfe808438cca8fa4db67f7769f5524c1171e667e2cfd9dd251ebc9076d619`.
The complete generated process receipt has SHA-256
`83537e779abe29330f86e688461849b36a53fee76a1a038b11a6116b398c4e19`.
The permanent integration case and both separately captured process cases passed
on Python 3.13.15. Each case passed five exact stream comparisons and nine
malformed rejections, with zero runtime input-file reads.

The two resolved streams grow from 14,064 to 14,826 bytes as the topology changes
from four to seven vertices. Both use 106 resolved schemas without missing or
provisional grammar. Their maps extend the actual Config counter 82 to 198 and
204 respectively. These are observed results, not emitted bases or defaults.
Five distinct dimension IDs remain assigned, and all five parameter node IDs
remain unassigned. The actual `D19` graph is retained in both models.
The sanitized [receipt](../measurements/2026/SdkBlindEndConstruction01.json)
binds the exact source, generated artifacts and complete process report.

The SDK returns plain `ArchiveNode` objects. Older research helpers also use
`Obj` convenience accessors and subtype checks. The proof installs the SDK
owners after those builder/keyword operations, then uses the shared typed
serializers. A future direct builder delegation must adapt that caller boundary
explicitly. It must not import research `Obj` into production or weaken concrete
node validation. [Accessor boundary](../../../Documentation/Gotchas/Conversion/Solidworks/Archive/Construction/PlainArchiveNodesUseTypedFields.md)

No prior reader, native or held-out result qualifies these constructor bytes
automatically. The worker performs static checks only and has no vendor-oracle
or VM access. All fifteen executable paths remain frozen after parent execution.

The CAD stopping conditions remain:

> The first is success under every criterion on this page.
> The second is the end of the available context.

This component is an implemented construction boundary. Complete native model
synthesis and measured public writer acceptance remain work under those criteria.
