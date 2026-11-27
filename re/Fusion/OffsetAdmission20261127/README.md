# SDK and CLI qualification for signed two-sided offset starts

Task `A05c-FusionOffsetReader20261127` promotes a bounded source-reader subset from campaign PR #395.
It does not qualify writing or editable cross-format conversion.
The task branch starts at freshly fetched main `91a73de348894a5791a51b977cd6fe0fe677a617`.
The first implementation is `23be702fd32d3092d98974c725bcc9d3b95fe0ee`; the final binding decomposition is `7ce58d3962f89c5c184e1fd993126e4927f9d73d`.

## Evidence and field rule

Native source groups are `1647204042fca11349eb62a4e495387204648c8b` and `c3a229ecfb1195447b9a532cc66dc975f77418b6` from [PR #395](https://github.com/TryUniCAD/Kit/pull/395).
That campaign measured 193 capture observations and 405 lifecycle/control/process comparisons across 27 fresh processes on Fusion `2706.1.17`.
Its source files, reports, holds and ownership remain separate.
This package copies seventeen digest-checked offset campaign controls and their relevant API observations, plus one tapered refusal control from PR #394 at `c2f00415b3f48dea33b349dcc43048509db3568d`.
Manifest.json records each control's source revision, including explicit source paths for the three refusal controls.
These are test inputs under `re/`, never production package data or writer templates.

The existing typed `DcExtrudeFeature.profileLocaltionType` code 1 identifies an explicit OffsetStart, including zero.
Its `profileOffset` reference identifies a `DcDoubleParameter`, which reciprocally binds a `Parameter` named `ProfileOffset` in native internal centimeters and display units `mm`.
The feature ownership, parent feature, numeric copies, role identity and allocator ID must all agree.
The neutral parameter converts centimeters to millimeters and remains a separate `DistanceExtrude.StartOffsetId`.
No offsets, captured values, file IDs or sample tables enter production code.
This is a typed-field admission extension using existing format knowledge, not a newly inferred wire grammar.

Only one unconstrained full circle on identity XY, NewBody operation, untapered unequal two-sided distance extents and qualified typed journal/snapshot history are admitted.
All existing current-body identity joins, complete topology/carrier checks, native labels, mass properties, materials and scene checks remain mandatory.
The resulting document is inspection-only, with `fusion.read_only` preserved.
The research CLI adds its separate unqualified marker; no marker is removed to force conversion.

## Deterministic execution

`Replay.py ROOT RUN SESSION` uses the existing InferenceSession protocol and configured A03 supervisor to invoke the pinned research CLI in fresh processes.
Models and native CAD calls are absent.
The first sandboxed launch was fenced before worker release because process identity was unavailable; its supervisor log and controller outcomes remain retained.
The same owned offline workers then ran with the required process inspection capability, using new job identities.
The private runtime is `/private/tmp/KitOffsetAdmission20261127`.
Its separate trusted research checkouts pin the implementation and reader baseline; they do not mutate the SDK under measurement.

The first replay strictly read 109 XY files, rejected the same 30 XZ/YZ files, and recorded no reader errors.
`Qualify.py RUN CAMPAIGN SOURCE_RUNTIME` verifies every scope decision, owned parameter role, actual native volume, area, bounds and document/receipt binding.
The first result has 1,447 passing comparisons.
The initial report incorrectly expected only one metadata marker; the correction explicitly requires both unchanged markers and retains that failed attempt.
`Evidence/Readers.tar.gz` contains only JSON documents, receipts and summaries.
All source and implementation revisions remain in those receipts.

Final replay repeats both strict and explicit fallback modes at the binding-decomposition revision.
A separate matched 16-file pre-existing circular-span corpus compares public decoded bytes against the fresh-main baseline.
The final replay again records 109 strict reads, 30 placement refusals and 1,447 passing comparisons at `7ce58d3962f89c5c184e1fd993126e4927f9d73d`.
All sixteen prior controls have identical outcome and neutral-document hashes against baseline `91a73de348894a5791a51b977cd6fe0fe677a617`, recorded in `Evidence/Compatibility.json`.
The reader archive retains the preliminary and final replay documents and receipts, plus both prior-corpus runs.

## SDK and CLI regression boundary

The shared suite opens fifteen real native baseline/edit/holdout controls through the public SDK and CLI.
It checks distinct first/second/offset/taper roles, all five owned parameters, evaluated stations, complete body geometry, JSON restoration and the read-only marker.
Three additional native controls retain XZ/YZ/taper refusals.
Encoded corruption cases change references, owners, reciprocal links, IDs, units, values, start kinds, taper, labels or snapshot carriers before actual public archive reads.
Writer and CLI conversion guards must refuse without modifying destination bytes.
These are archive, SDK and executable integration checks in the existing queue suite; no unit tests or separate workflow are added.

No new native capture was needed for the reader promotion; the source campaign's leased API evidence is reused.
Portable source fidelity outside this bounded family, independently driven sketch dimensions, broad frame support and target application acceptance remain unfinished.

## Integration fixture repairs

The first local integration run at production head `792fdecaa` passed 49 of 52 cases.
Its retained JUnit report records three fixture assumptions: CLI conversion refuses at qualification before the writer, entity emission itself refuses infinity, and offset caps need not coincide with the sketch sheet.
The repaired cases use the actual qualification message, a unique finite sentinel replaced in one validated bulk stream, and a reciprocal label move without coincident-station selection.
Independent read-only production and provenance audits found no production defect; the latter identified the refusal-control provenance correction above.
