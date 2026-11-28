# Automatic native reader verification

The developer CLI now requests native API verification after pinned SOLIDWORKS and Fusion decoding.
`kit run` submits mapped scopes sequentially and verifies completed rescan inputs in application batches.
The controller retains dependencies between scopes, including across pause and resume.
Independent rescans inside one scope can still use multiple offline workers.

## Use

Run the existing `kit research --root CHECKOUT solidworks ...` or `fusion ...` command.
Kit detects the local API before starting an application.
No remote worker configuration is required.

Use `kit research --root CHECKOUT api status solidworks` to inspect SOLIDWORKS availability.
SOLIDWORKS verification requires Windows, the registered licensed COM server, and `pywin32` in Kit's Python environment.
Close existing SOLIDWORKS sessions before verification.
The verifier uses a new session and the existing exclusive oracle mutex.

For Fusion, run `kit research --root CHECKOUT api enable fusion`.
This installs the KitVerify add-in and records hashes for the selected checkout's verifier sources.
In Fusion, run KitVerify once and select **Run on Startup** under **Scripts and Add-Ins**.
Close Fusion before you repeat the decoding command.
Kit then launches a fresh local process for each measurement.
Ordinary Fusion startup returns before loading the research checkout or starting a verification event or polling thread.
Manual initialization records API readiness without starting the worker.
Only a process launched by the verifier receives the session nonce needed to load and serve its matching request.
An existing application session remains open and blocks verification.
Enable the add-in again after changing verifier sources.

`KIT_NATIVE_API_DIRECTORY` selects an absolute private Fusion verification directory instead of `~/.kit/verification/fusion`.
Use a separate directory for an isolated research host or compatibility run.
When using this option, start Fusion with the same environment setting.
Compatibility tests select an unused directory and cannot attach to a configured user add-in.

## Results

The readers retain their existing `document.json`, `receipt.json`, and Fusion `summary.json` artifacts.
The additional `NativeVerification.json` records the measured input hashes, source revision, application build, controls, cases, and edits.
Reader comparisons reconstruct the exact published `document.json` and verify its receipt hash again immediately before comparison.
They also require the SDK source inventory to match the publication receipt.
The report's neutral hash therefore identifies the artifact the user received.
Catalogue runs retain separate `NativeVerification-solidworks.json` and `NativeVerification-fusion.json` reports.
Live report schema `2` keeps a compact case index.
Measurements, comparisons, saved-edit readbacks, and detailed case results are separate bounded JSON artifacts in the adjacent private `*.Evidence-*` directory.
Every artifact reference records its relative path and SHA-256 digest.
Completed cases are reduced to their summaries in memory, so a large batch does not retain or repeatedly serialize every native snapshot.
The batch index is written at initialization and finalization.
Per-case artifacts provide durable progress without rewriting all earlier summaries at each checkpoint.

The native batch performs these operations:

1. Rebuild and measure the pinned healthy control.
2. Open each candidate in a fresh application process.
3. Rebuild and measure bodies, volume, centers, exact planar boundaries, feature definitions, parameters, and sketch constraints.
4. Compare those observations with the current decoder output.
5. Change each supported independent driving parameter separately.
6. Rebuild, measure, save, and restore the original parameter.
7. Reopen each saved edit in a fresh process and decode that saved file again.
8. Rebuild and measure the final healthy control.

Failed controls invalidate the whole batch.
Changed source code, reused processes, and changed application builds also invalidate acceptance evidence.
Missing decoded measurements cannot pass comparison.
An unavailable API returns setup instructions and leaves verification incomplete.

The SOLIDWORKS collector distinguishes methods from values returned by dynamic
dispatch. See the [verification dispatch correction](../Workers/SolidWorks/Verification/SolidWorksVerificationDispatch.md).

| Reader exit status | Meaning                                                  |
| ------------------ | -------------------------------------------------------- |
| `0`                | Decoding and requested native reader verification passed |
| `1`                | Input, decoding, or dispatch failed                      |
| `3`                | A Fusion batch contains rejected inputs or reader errors |
| `4`                | The native API needs installation or enablement          |
| `5`                | Native verification failed or its batch was invalid      |

Direct research scripts retain offline decoding unless passed `--native-verify`.
The launcher inspects the selected reader's declared parser options before forwarding that option.
This bounded source inspection does not spawn a capability process or depend on terminal encoding.
It recognizes literal `add_argument` declarations in the entry script.
Dynamic or imported declarations conservatively select the explicitly unverified compatibility path.
Older checkouts still decode their pinned inputs.
They return status `4` after successful decoding and explicitly report that verification was not performed.
Their existing artifacts and Fusion partial-result status remain intact.
The installed developer CLI supplies that option automatically.
Production conversion does not import or invoke these research oracles.

## Scope and limitations

The report identifies its scope as `native_source_reader_verification`.
It compares decoded source documents with their own application observations.
It does not qualify a new writer or a cross-format conversion.
Existing research receipts and conversion markers remain unqualified.
`portable_complete` and `conversion_qualified` remain false.

Current API collectors handle part documents with one to sixteen independent dimensional parameters.
Assembly occurrences and unsupported parameter types fail explicitly.
Comparison covers feature order and suppression, parameter values and ownership, expression dependencies, sketch frames and supports, exact sketch entities, and constraint operands and dimensional bindings.
One-sided solid extrusions compare their profile, operation, depth or through-all termination, direction, taper, start offset, and owned parameter bindings.
Planar single-body results compare vertices, straight edges, face planes, and each face's boundary loops in addition to topology counts and measured mass properties.
The decoder's planar boundary representation supplies its centroid independently of the native measurement.
Known metadata folders do not enter the operational feature graph.
Unknown authored features, unresolved references, constructed planes, multiple configurations, nonplanar boundaries, ambiguous profiles, and other unsupported definitions produce explicit field names in `semantic_gaps`.
The live index links to each case's detailed gap list rather than duplicating it in the batch summary.
Absent decoded centers or other required values also prevent a passing case.
Unordered geometric inventories use spatial buckets and structural categories before applying the unchanged numeric tolerances.
Each item allows at most 256 candidate comparisons; more ambiguous geometry fails explicitly instead of causing an unbounded search.
Sketch entities and boundary vertices and edges must also have unique geometric identities within their owner.
Duplicate coincident entities leave reference binding unverified even when both inventories have matching counts and values.
Face-attached sketches remain unverified until the exact support face identity is compared; a producer name and frame alone do not establish that identity.

`full_semantics_verified` is computed from the case and saved-edit comparisons.
Every required observation must exist and match for it to become true.
A live batch additionally requires healthy controls, fresh owned processes, an unchanged application build, and unchanged verifier and decoder sources.
Only then does `live_batch_verified` become true and the overall status become `passed`.
Successful native measurements with incomplete semantic comparisons remain `unverified` and return status `5`.
These fields describe the selected source-reader verification scope; they do not establish writer or cross-format qualification.

To inspect a saved observation without starting an application, run:

```sh
kit research --root CHECKOUT api compare fusion --document document.json --measurement Observed.json --output Compared.json
```

Use `solidworks` for a SOLIDWORKS observation.
The command reads bounded serialized inputs and uses the same semantic comparator and assessment as the live batch.
It returns `0` for a complete comparison and `5` for missing or differing observations.
Its scope is always `offline_measurement_comparison`; `native_acceptance` and `live_batch_verified` always remain false.
An authored fixture or saved report cannot qualify a live native batch through this command.

Fusion needs its owner-enabled startup add-in to load in the newly launched process.
The protocol requires its PID to match the directly launched process.
A launcher that redirects to another process cannot qualify a case.
Timeouts leave native sessions available for owner recovery instead of closing unrelated documents.

## Verification evidence

Source inspection covered controller dependencies, CLI forwarding, API detection, batch invalidation, and artifact publication.
CLI compatibility coverage now checks missing-API reports and nonzero verification outcomes at the installed process boundary.
The Windows compatibility job also selects the encoding and legacy-checkout process cases explicitly.
The legacy fixture checks out only SDK and automation paths, avoiding unrelated historical CAD trees.
It explicitly populates the initially empty sparse index before launching the historical reader.
Its historical lazy fetch uses the public repository and does not require persisted checkout credentials.
Catalogue process coverage inspects the persisted predecessor dependencies and native availability report.
Serialized CLI coverage decodes the pinned P03 Fusion control and compares it with an independently authored observation fixture.
It checks a complete comparison and rejects missing semantics, unsupported fields, wrong feature directions, wrong parameter bindings, wrong constraint operands, wrong topology counts, and wrong face planes.
It also checks reordered observations and a coordinate perturbation across a spatial bucket boundary within the numeric tolerance.
The P03 fixture has one boundary loop per face; the reorder case covers edge order within those loops and does not establish inner-loop reorder acceptance.
An additional serialized CLI case duplicates point geometry in both the decoded document and observation inventory and requires an unverified result.
The fixture is explicitly offline evidence and cannot establish licensed API acceptance.
No local tests or licensed application acceptance were executed during implementation.
Remote CI and live licensed SOLIDWORKS and Fusion measurements remain required.

The [queue repair entry](NativeVerificationQueueRepairs.md) records the numeric topology comparison correction, consistent Windows metadata snapshots, and catalogue finalization integration.
