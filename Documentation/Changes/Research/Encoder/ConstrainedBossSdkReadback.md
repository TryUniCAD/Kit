# Read a generated constrained Boss through the independent SDK

Compare the saved P03 baseline with the exact source-free research candidate from [PR #325](https://github.com/TryUniCAD/Kit/pull/325). The candidate fails the default strict SDK read. A separate strict design-only read recovers its sketch and Boss, with a different projected relation order and without B-rep.

## Reproduce the reads

Use Python 3.14 and the pinned SOLIDWORKS reader from [PR #121](https://github.com/TryUniCAD/Kit/pull/121) at `c0a401a607759fb0c2589647c2a22af65ebb7ce1`. Record the native file SHA-256 before and after each read. Use the archived native baseline at `re/automation/PairedCaptures/P03/solidworks-db1390476325/P03-solidworks-baseline-a.SLDPRT` from capture revision `89c25945f5833ad9c3a1c6c683df510b5702dd54`. Prepare its JSON with the [P03 source intent procedure](ConstrainedBossIntent.md) and generate the candidate with the [persisted constructor request](ConstrainedBossCandidate.md). Supply an unused `.SLDPRT` output through the documented `candidate` argument. Check both file digests against the [pinned observations](../../../../re/solidworks/records/P03GeneratedSdkReadback.md) before comparing them.

Run each following call in its own fresh process with that reader's `src` first on the import path. Store the complete `CadDocument.to_json()` in a new private file on success. Keep the exception and the options if the read refuses.

| Read | Call to `convert.open_document` |
| --- | --- |
| Default | `open_document(path, source_format="solidworks.sldprt")` |
| Design-only | `open_document(path, source_format="solidworks.sldprt", include_brep=False, include_tessellation=False)` |
| B-rep without tessellation | `open_document(path, source_format="solidworks.sldprt", include_tessellation=False)` |
| Lenient | `open_document(path, source_format="solidworks.sldprt", strict=False)` |

Keep the default outcome before making any additional calls. Inspect the document's diagnostic list, retained native records and typed resolved metadata separately. The matching SDK model is required to read the persisted JSON. For the paired strict design-only documents, run `re/automation/SemanticComparison.py` with the exact two JSON digests, declared `mm` geometry units and zero tolerances. The ordinary candidate checkout refuses the newer model. Reproduce the separate comparison with `src` from the exact reader revision and the comparator directory first on the isolated process path. Import `interchange.serialization.JsonCodec` and `interchange.document.Models.DocumentModel` from that reader before running the unchanged comparator module with the same arguments. See [SDK revision mismatch when comparing reader JSON](../../../Gotchas/Research/Readers/PinnedReaderJsonSchema.md).

## Verification

The source default read returned one B-rep and three partition or delta payloads. The generated candidate failed default strict and B-rep without tessellation with `SLDPRT contains no readable Parasolid payload`. Strict design-only decoded both archives. Lenient candidate output was byte-identical to the candidate design-only document.

Both design-only documents reported one sketch, eleven relations, three parameters, one body and twenty-six timeline nodes. The body-producing features linked to their own Front-plane sketches and carried the same 10 mm positive blind depth. The four axis relations, the separate Origin reference and the four shared corners matched by role. The individual 20 mm height and 40 mm width operands and their owners agreed. The source projected height before width and the candidate projected width before height, though both native distance blocks recorded width before height. The keyword index determines the projected order. The existing source replay witness refused the candidate's projected order. Both decoded Boss operations were Join. The prepared target's first-body Create remains separate from that observed reader result.

The unmodified graph comparison, loaded with the exact reader's model, reported `different`. It matched 57 nodes and recorded 188 unresolved entries per side, including 25 native-only definitions and 25 retained native records per side. Four reference differences concern the unresolved `N_Axis` selection on the renumbered native identity of the rectangle sketch. Both typed resolved reports retained an unsupported `moSimpleSurfIdRep_c` schema 1 class. This read-only comparison leaves whole-source preservation, native edit and save/reopen, independent held-out qualification and public admission open. No CAD application or model calls ran.

[Recorded archive, document and comparison digests](../../../../re/solidworks/records/P03GeneratedSdkReadback.md) · [Projected dimension order gotcha](../../../Gotchas/Research/Readers/ConstrainedBossProjectedOrder.md) · [Analytic body scope gotcha](../../../Gotchas/Research/Readers/ConstrainedBossAnalyticBodyScope.md)
