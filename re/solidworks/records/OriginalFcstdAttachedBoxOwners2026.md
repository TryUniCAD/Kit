# Original FreeCAD attached box owners

Task `B04-SW2026-FCSTD-BOX`, owned by PR #121 takeover. This proof starts
with the intact disclosed FreeCAD 0.21.2 F14c archive. It binds the model,
each stored shape and the exact shared builder output to the same
source. Public transfer policy and historical benchmark membership
remain open. [Measured receipt](../measurements/2026/OriginalFcstdAttachedBoxOwners01.json)

## Source and target identity

The default strict SDK read takes the original path from CADMPEG
`de2726870ff728352163f601ab4e60bbd54fbade`. The source SHA-256 is
`25c836424406343439bd3fa9acd82f8e6dbabdae689fe2a799099bf73805aafb`.
The proof joins all nine typed source objects and ordered dependencies
to their numeric declarations in `Document.xml`. Body's Tip and Group
own the actual AdditiveBox. The live Support selects the whole XZ datum.
The source origin group owns three planes and three axes. The XML shape
properties select the three distinct ZIP members below.

| Source owner | Member | Stored frame |
| --- | --- | --- |
| `Body.Shape` | `PartShape.brp` | Model |
| `AdditiveBox.AddSubShape` | `PartShape1.brp` | Feature-local |
| `AdditiveBox.Shape` | `PartShape2.brp` | Model |

The local shape is a positive 20 × 30 × 10 mm box. Its source placement
quaternion gives the matching signed model frame and bounds
`(0, -10, 0)` to `(20, 0, 30)` mm. The incidence check independently labels
the eight geometric corners and validates line carriers, the twelve edge
endpoint pairs, six planar closed outer rings, 24 coedges and each
edge's two face uses. It binds the whole closed shell to its solid
region. The three stored shapes, the selected FreeCAD design body and
the default strict SOLIDWORKS read all have the same normalized
incidence. Coordinate comparisons use a declared `1e-10 mm` tolerance.

The generated graph binds the source datum frames to the target
principal planes, with Top Plane feature 15 supporting the actual
profile 18. The external corner relation selects the actual model
origin 17. Length and Width reference sketch endpoint pairs `(0, 1)` and
`(0, 3)` through live dimensions 19 and 20. Height uses dimension 22
through the primary end of reversed blind boss 21. The public parameter
provenances agree with the three actual typed native parameter spans.
The generated body name and sole solid bind to body atom 101 and the
same boss. The reader retains 19 ordered feature rows, two summary
fields and 15 literal file properties.

## Exact replay and limits

Two fresh guarded builds use `ReadBoxSource` and `MakeOriginBox` with the
actual source creation epoch and previously measured logical target
path. They reproduce the full 10,189-byte output
`398a092e45c9662f82881f8254a5728a8b6f7330b80e9f78c874de9e18d2f754` and
all 12 logical streams. Two fresh guarded strict reads independently
recover the anonymous boundary incidence, named Body, volume of
6,000 mm³ and area of 2,200 mm². Those measures and the derived centre
agree with the prior native reopen of the exact same file. That native
packet also measured the three independent driver edits at 27, 36.9 and
15 mm. [Native lifecycle](../measurements/2026/AttachedTopBoxGeneratedNative01.json)

All four workers record zero data-file reads after intake and
initialization. Two equal-incidence shape caches remain distinct
source owners. Substitution of the feature-result bytes into the
body-cache slot refuses, as does omission of a shape owner or addition
of another authored domain. A source B-rep with unchanged vertex
coordinates and counts but a corrupted edge passes the older
corner/count corroboration and fails the stronger incidence check.

Inferred path, explicit path and explicit stream writes of the intact
source refuse before staging and publish zero bytes. The complete
FreeCAD archive payload and SHA binding, FreeCAD record provenance and
round-trip metadata remain unrepresented transfer categories. The
numeric FreeCAD object identities and independent origin axis objects
are source inventory evidence. Target body and contour identities
belong to the generated SOLIDWORKS graph. This exact release has
ordinary B-rep members with no element-map sidecars. Later releases
require separate evidence for their additional source owners. The proof
adds zero native observations and zero original benchmark credits.

Run the [guarded proof](../../tooling/sw2026/attached_top_box_source/VerifyOriginalFcstdAttachedBox.py)
with the unchanged FCStd path and an unused report path.

```sh
python3.14 -I -B re/tooling/sw2026/attached_top_box_source/VerifyOriginalFcstdAttachedBox.py \
  /path/to/recipe-0.21.2-F14c.FCStd /tmp/NewF14cOwners.json
```

The proof result contains hashes and analytic observations. The source
owner inventory and incidence checks accept independent expected input
identities through their worker request for a later locked comparison.
