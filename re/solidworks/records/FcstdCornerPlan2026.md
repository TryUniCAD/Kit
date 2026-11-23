# Source-owned FreeCAD corner and width-depth equation

The full FreeCAD inputs still refuse SOLIDWORKS publication. Their actual sketch, Pad and equation owners now reach the shared typed part graph in a guarded research process. The generated graph exposes a concrete dormant-dimension mismatch before archive emission. [Exact evidence](../measurements/2026/FcstdCornerPlan01.json)

Task `B04-SW2026-CORPUS/CORNER-PLAN`, owner `/root/release_path`, integration `/root`, delivery PR #121. This step depends on the original-path census, the [local expression binding](FreecadLocalSketchExpr2026.md), and the shared rectangle, anchor, and [width-depth](../../../Documentation/Changes/Solidworks/Construction/SolidworksPublicWidthDepthWriter.md) construction. Full admission requires an accounted source-owner plan, exact native qualification, a lossless strict readback, and authenticated membership in the requested corpus.

## Selected source identities

The historical recursive audit counted resolved paths. The surviving per-file inventory is target-side and gives no source identity join. The probe selects only four cases from the existing [verified original-path census](PublicFcstdWriterCensus2026.md). Its candidate table SHA-256 is `d004e25a4cb37d851c8ecff0d9d4a61155953352097eaf33803a0d3e1910eb2b`. The nine closest signatures all have four sketch lines and one forward blind Pad. The three listed N10a files are release saves of one design. The other six cases contain a spreadsheet, and `C132`, `C143`, and `C058` also select a symmetric rather than a corner-anchored sketch. The closest starting point is `C130`, with the smallest property inventory and no spreadsheet, explicit App::Point, or local element-map sidecars.

| Case | FreeCAD release | Source SHA-256 | Additional Pad parameter rows | Retained payloads |
| --- | --- | --- | ---: | ---: |
| C130-P01 | 0.21.2 | `d1f9225bfdf31d9708fc8fc8f94261edc9479d01d6a09c720ae70c16a5aa2362` | 14 | 6 |
| C123-P01 | 1.0.2 | `c965847aa2a1ba6c1bacc43ae0c911db1610e57497ab5ca19fea5e6aed33ada4` | 15 | 8 |
| C017-P01 | 1.1.4 | `215d76c07e95dd13f791b404eeacd6f625a0bbefa603e3653b007a73a853184c` | 19 | 8 |
| C059-P01 | 0.21.2 | `73cd885cd4755b274fe1106db3022923352ea45a7a4d9964d48202790a47de61` | Spreadsheet contrast | |

The source authority covers the measured files only. All three original-source writes remain inadmissible. None of these four source hashes is authenticated as a member of the original 165-part/five-assembly benchmark. [Roster evidence](FcstdCorpusAvailability2026.md)

## Model graph

The proof takes the complete strict neutral FCStd read with B-rep and tessellation requested. The actual sketch owns the identity XY datum by its whole-object link, signed frame, attachment mode, and stored identity placement and offset. The typed width, height and depth values retain their source IDs and names. The raw and typed width-to-depth bindings must agree with the actual Pad expression-engine property and current width. The shared arithmetic evaluator independently validates the cached depth.

Four ordered endpoint joins become four genuinely shared native point objects. Each source relation maps to an actual native point or line owner. The four unary constraints own their respective lines. Both distance dimensions select the same source line endpoints, with width at `(0, 1)` and height at `(1, 2)`. The authored `(-1, 1)` root-point slot binds to the distinct origin handle and the actual same-part origin profile. Closed geometry and a zero coordinate alone cannot authorize the join or the anchor. Two actual native dimension references link the named `"Length@Pad" = "width@Sketch" / 2` relation. The constructor binds live parameters and the same part on both sides.

An independent analytic prism from the authored lines and depth matches the intact decoded B-rep by vertex coordinates, edge endpoints and face incidence. All three have six faces, twelve edges and eight vertices, 16,000 mm³ volume, 4,000 mm² area and centre (20, 10, 10) mm. These are host model and boundary observations.

Two fresh guarded processes per positive reproduce identical reports. Another process exercises the authentic spreadsheet-backed refusal. The positive cases each preserve a full neutral JSON round trip and the exact original archive hash. A changed external slot, a conflicting portable reference, a missing authored join at unchanged coordinates, the wrong expression operand, or a newly active draft each fails. Runtime data reads after source intake, output bytes, native launches and corpus credit all remain zero.

## Remaining owner boundary

Normal `PrepareNative` sends the intact B-rep through the imported-body planner, which rejects the retained parametric capabilities. Calling `PlanEqPart` directly rejects the extended source scope. The ordinary registry refuses the explicit native stream and preserves the caller bytes and cursor. The research graph stops before archive serialization and keeps the original document unchanged.

Every original retains an inactive 10 mm second-direction length in `Pad.Length2`. Its end condition remains absent. In the shared ordinary single-direction graph, the actual `moEndSpec_c.f20` display owns a distinct `D2` parameter, but the default constructor puts the current 20 mm primary length there. The `BossEndInput.SecondDepth` field enables two active directions and cannot supply the dormant value. A native-saved edit independently demonstrates that dormant and active values survive separately. The smallest new native contrast should bind a distinct model-owned dormant value to the one-direction owner while keeping the live direction flag, then verify the number after open, a live depth edit, save and fresh reopen. [Single-direction saved evidence](GeneratedNestedAssemblySavedState2026.md) · [Scope gotcha](../../../Documentation/Gotchas/Conversion/Freecad/Primitives/InactivePadLengthSurvivesSourceRead.md)

The measured ordinary equation reader also requires literal D1/D2 dimension labels. It needs a guarded named-parameter lane that binds the real handles before accepting the authored names. The original `Body` label, the other Pad parameters, source metadata and provenance, origin/axis objects, and retained OCCT lineage remain open. The newer releases retain element-map owners and an alternate Refine value. The 1.1.4 source adds an actual App::Point. No source readiness claim is made by making any of these fields disappear.

## Reproduction

Use a checkout with the production tree of `ffa49a63caf2b3c433c05433c7b638e5d0d4fde7` and the [probe and projection](../../tooling/sw2026/freecad_census/ProveFcstdCorner.py). Supply the existing verified inventory and a new receipt path. The originals are reopened only at their approved original paths and the receipt contains hashes and owner measurements.

```sh
python3.14 -I -B re/tooling/sw2026/freecad_census/ProveFcstdCorner.py \
  --verified-inventory /path/to/frozen/census/VerifiedInputs01.json \
  --output /tmp/FcstdCornerPlan01.json
```
