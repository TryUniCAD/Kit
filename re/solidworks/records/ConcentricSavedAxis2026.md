# Signed concentric endpoints after native save

Task `B04-SW2026-MATES-CONCENTRIC/saved-axis-read`, owner `assembly_frontier`, delivery PR #121. The reader accepts the disclosed native-saved radial pair and retains its signed selected axes, actual child face and authored aligned/free relationship. This tranche covers the ordinary solved two-occurrence reader. Dependencies are the stored orientation state, independently bound child kernel owners and the controlled native radial lifecycle. [Orientation state](ConcentricOrientationEnable2026.md) · [Kernel owners](ConcentricKernelFaceIdentity2026.md) · [Native lifecycle](ConcentricRadialAssembly2026.md)

## Field rule

The active `moCylinderRef_w` under `moMateConcentric.f410[ordinal].o` owns the selected axis sign. Its `f108` is the saved unit direction in the selected child's coordinates and `fe8` is its signed direction in assembly space. The exact-build orientation-state constructor obtains `f108` by inverse placement of the world direction. The serializer loads the vector into the private state separately from `fe8`. The actual child kernel cylinder provides the carrier line, point and radius. Its axis can use either direction along that line. [Field and constructor bindings](ConcentricSupportSnapshotConstruction2026.md)

The reader verifies unit norms for both local vectors and compares all three components of `f108` with one signed choice of the actual kernel axis. The dot product chooses the sign and the component checks establish collinearity at `rel_tol=1e-10` and `abs_tol=1e-12`. The rigid occurrence rotation transforms that signed `f108` to the stored `fe8`. The original exact point/radius checks at the declared tolerances still bind the endpoint to its owned child. Since both ends select the same child cylinder, both share the same local orientation in this profile. The signed world directions independently satisfy the actual ordered alignment code and coaxial relationship. The public `stored_axis` retains the actual `fe8`. [Endpoint frame check](../../../src/convert/adapters/solidworks/Core/TypedMates/Cylinders/CheckCylFrame.py) · [Pair check](../../../src/convert/adapters/solidworks/Core/TypedMates/Cylinders/CheckCylPair.py)

## Exact observed orientations

The linked archive supplies the active wrappers, the actual component chain and the owned cylinder face. The native author/reopen observations independently agree with the ordered occurrence IDs, corresponding faces, rigid placements, world points, signed axes and radii. All radial observations are from the already completed controlled SOLIDWORKS 2026 SP05.2 run, executable build `34.5.2.0604`.

| Native pair | Kernel axis | Both signed local wrapper axes | Ordered signed world wrapper axes | World dot | Alignment code |
| --- | --- | --- | --- | --- | --- |
| D01 source | `−Z` | `−Z` | `−Z`, `−Z` | `+1` | `1` aligned |
| D03 source | `−Z` | `−Z` | `(-0.450079, -0.069166, -0.890306)`, `(0.450079, 0.069166, 0.890306)` | `−1` | `2` anti-aligned |
| Radial native-saved pair | `−Z` | `+Z` | `+Z`, `+Z` | `+1` | `1` aligned |

Both native-saved radial ends have world direction residual zero, carrier component error `1.11e-16`, point error `6.94e-18 m`, coaxial separation zero and radius `7.19 mm`. The measured saved child selects real kernel node `27`, wire face `40` and body atom `101`. Its archive and the saved parent are held by exact SHA-256 in the receipt. The ordered endpoint records in the saved and freshly reopened native observations are equal. [Sanitized measurement](../measurements/2026/ConcentricSavedAxisRead01.json) · [Prior root audit](ConcentricParentRootAudit2026.md)

## Public process evidence

The before snapshot is `22cbb0ccc4bb6cd959bf1306bf4ddeb61712944a`. The after snapshot substitutes the four reader files by hash. The existing [public reader worker](../../tooling/sw2026/ReadConcentricPublic.py) takes JSON on stdin with the native `path`, locked `sha256` and `mode` of `default` or `metadata`. It runs as `python -I -B re/tooling/sw2026/ReadConcentricPublic.py --root SDK_ROOT --output NEW_RECEIPT`. The existing [comparison](../../tooling/sw2026/CompareConcentricRead.py) checks independent native endpoint observations and kernel IDs.

The 74 public SDK processes make 840 native comparisons in the after snapshot, 238 of them numerical. The saved radial pair changes from `unsupported` to `admitted` in both modes and contributes 120 comparisons, including 34 numeric checks. All 12 before/after complete public-document pairs for the six original/edited D01–D03 saves remain identical. The 22 pre-existing diagnostic artifacts and the frozen pre-solve radial parent keep identical complete refusal documents. They include wrong local direction, wrong world direction, wrong point, wrong radius, wrong alignment and stale or foreign owners. The source files and diagnostic artifacts were read without modification. This measurement started zero native processes, read zero held-out files and produced zero CAD files. [Sanitized measurement](../measurements/2026/ConcentricSavedAxisRead01.json)

Whole-source D01 construction still requires its root inventory and provenance, and held-out qualification remains open. [Whole-source blockers](ConcentricParentRootAudit2026.md)
