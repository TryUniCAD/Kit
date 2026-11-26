# Measure the source-order P03 candidate in SOLIDWORKS

The source-order P03 candidate passed the measured open, rebuild, depth edit, save and fresh reopen sequence on SOLIDWORKS 2026 SP04.1 build 34.4.1.1011. The native run used candidate SHA-256 `29b581feaf693b2a5e38e2f8bac70d2f3ab2b7f3f4f56be104e64701e0c0a62a`. This is the opt-in source-order output in the [P03 replay guide](SolidworksKeywordDimensionOrder.md).

## Repeat the measurement

Prepare the exact candidate using the source-order replay. Retain the three independent, same-family native files from the original P03 capture, including the separately saved 12 mm reference. Use the private native plan and runner whose hashes appear in the evidence record. Verify the input, executable and helper hashes before use. Run each role in a fresh owned SOLIDWORKS process with an idle all-session inventory. The measured order was stock before, source, edited source reference, read-only candidate, writable candidate copy, fresh saved reopen and stock after. The edit phase used a new writable copy and saved to a new sibling path. [P03 paired measurements](../../../../re/automation/PairedCaptures/P03/solidworks-db1390476325/measurements.json)

Each native snapshot used the vendor's same-interface `IRefPlane` comparison against the Front plane, an independently fetched Front reference and a Right-plane negative control. The observer checked the driving width, height and depth, the four shared corner aliases, the separate Origin reference and the directed operands. It bound the extrusion to its actual sketch, measured its base-feature role and confirmed that its six faces belonged to the one final solid. It retained the original feature-handle identity and extrusion flag readings. [Specific plane identity](../../../Gotchas/Research/Workers/SolidWorks/FrontPlaneIdentityNeedsSpecificInterface.md) · [Native getter binding](../../../Gotchas/Research/Workers/SolidWorks/SolidWorksNativeGettersCanReturnValues.md)

Both stock controls passed. All seven owned processes exited normally, and the final all-session check found zero active SOLIDWORKS sessions. The cohort ran for 95.524 seconds. The candidate kept one solid with six faces, twelve edges and eight vertices. A single depth edit changed the measured volume from 8,000 to 9,600 mm³, the surface area from 2,800 to 3,040 mm² and the centroid from (20, 10, 5) to (20, 10, 6) mm. The dimension and the extrusion definition each returned the exact 12 mm SI operand after fresh reopen. The original source and candidate bytes, the private writable input and the saved derivative retained their recorded hashes. [Native cohort and saved-derivative receipt summary](../../../../re/solidworks/measurements/2026/P03NativeLifecycle.json)

## Read the saved derivative offline

Use the saved derivative with SHA-256 `dcea552fa4751563c124fb1dc571f3e0b36c0ce37ce39610b45f7717d8687115` and the clean SDK revision `c0a401a607759fb0c2589647c2a22af65ebb7ce1`. Run the pinned SDK in a fresh Python 3.14 process. The recorded read passed these two option sets to the public API on the same bytes:

```python
default = open_document(data, source_format="solidworks.sldprt", strict=True)
model_only = open_document(
    data,
    source_format="solidworks.sldprt",
    strict=True,
    include_brep=False,
    include_tessellation=False,
)
```

Both modes returned 26 feature rows, one sketch and one design body. They preserved seven saved sketch relations, four inferred corner joins and the 12 mm driving parameter on `BlindBoss`. The SDK projected a blind +Z `ExtrusionFeature` with operation Join. The design body names it as the final feature and has no bound native body identifier. Default strict retained three current-schema Parasolid payloads and returned `brep=None` with no diagnostics. Model-only returned no B-rep, native geometry payloads or meshes. The independent full typed graph attempt refused `moSimpleSurfIdRep_c` schema 1. The acquisition used one fresh offline process and preserved the derivative hash. [Saved partition read limit](../../../Gotchas/Research/Readers/ConstrainedBoss/SavedBossPayloadsCanLackPublicBrep.md)

## Scope

The native record covers this exact candidate, its saved derivative and matching same-family controls. The original feature-handle comparison returned 0, and the measured `IsBossFeature` and `Merge` flags returned false. Those raw results remain in the evidence. The two measured SDK operation and construction intent values remain Join and Create. Whole-source preservation, independent held-out generalization and public writer qualification remain open. The measured source and candidate differ in several raw groups, including the feature tree and presentation.
