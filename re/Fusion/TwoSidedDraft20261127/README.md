# Independent two-sided circular extrusion drafts

This is bounded native-source decoding evidence. Complete reconstruction and conversion acceptance remain unestablished.

Task: `A08h-FusionTwoSidedDraft20261127`, owned by Codex on `feat/fusion-two-sided-draft-20261127`.
Fresh base and frozen SDK/research root: `18b41b98c96fd123a11d1ae0d1cda29b9d9746ed`.
Native-input commit: `c2f00415b3f48dea33b349dcc43048509db3568d`.
The [automation register](../../../Documentation/Reference/Research/AutomationSteps.md#a08h-fusiontwosideddraft20261127) owns status and exit conditions.
The [change entry](../../../Documentation/Changes/Research/Campaigns/FusionIndependentTwoSidedDrafts.md) records the publication boundary.
PR #393 remains a separate unequal-axis revolution campaign and is not included in this branch.

## Why this scope

The prior Extrude study qualifies positive one-sided ProfilePlane draft and untapered two-sided circular controls.
Its `Notes/Extrude.md` explicitly leaves other taper/start/sign combinations open.
This campaign combines unequal positive Distance extents with independently signed taper angles on both sides.
No matching claim was found in the refreshed open deliveries and programme comments before capture.
The P03 catalogue builder lacks separate two-side distance/draft inputs, so a campaign-local script uses the existing native script worker.
Shared catalogue builders, native workers and decoders remain unchanged.

The baseline uses radius 13 mm, first/second distances 17/29 mm, drafts +7/−4 degrees and circle center `(7,−11)` mm on XY.
Discovery independently changes each distance, each draft, radius, placement and sketch frame (XY/XZ).
A swapped-side case exchanges both distance/draft pairs: equal volume with a different axial centroid distinguishes side ownership.
Two `holdout_*` cases combine unseen distances, signed drafts, radii, placement and frame.
These are same-generator parameter holdouts, not the programme's reserved P05 assets or independent generator lineages.

`Capture.py` fixed the roster, holdout labels and independent frustum integration before dispatch.
Its pre-dispatch SHA-256 is `ead13b48de99ef988d22b1ad1381322edc106c7bb28c562b1f75cb1b79f326eb`.
No decoder rule was fitted or changed after observing these files.
Positive draft expands away from the sketch on its own extent side; negative draft contracts it.
For each side, the analytical prediction integrates `radius(s) = r + s*tan(angle)` over its positive travel distance.
The opposing side contributes a negative axial moment. Sketch-to-model transformation places the resulting centroid in the component frame.
This is measured source geometry evidence, not a new wire-grammar or portable-writer qualification.

## Native source and lifecycle

Capture job `e16431a380834e1d09eff75f50a47c43` ran on Fusion `2706.1.17`, owned PID `21956`.
`Capture.json` retains exact requested values, actual distance/draft model parameters and expressions, circle/frame data, body measurements and feature health.
All 101 baseline, four independent feature-driver edits and restorations match volume, surface area and centroid predictions.
Each distance edit adds 3 mm; each draft edit adds 2 degrees. All other driving values stay fixed.

Eleven cases each save a baseline, four edited states and one restored state, plus two untapered controls: 68 original archives in `Native/`.
Their hashes bind the committed-input manifest. Native controls remain research sources, never writer templates or production package data.
`Verify.py` reopens each original baseline in a distinct owned fresh process and measures it before recompute, then after rebuild.
It independently edits all four drivers, rebuilds, exports, restores and reopens the saved edits, then saves and reopens restoration.
An unchanged known control is opened, rebuilt and measured before and after every case.
The verification report binds that control's original SHA-256, the source SHA-256, process ID and executable hash.
Actual completed counts and numerical dispositions are recorded in `Evidence/Summary.json` and `Evidence/NativeVerification.json`.
Independently driven sketch radius and placement dimensions remain outside this lifecycle scope.

The private service owns and serializes Fusion requests. No pre-existing native session was attached to, stopped or recovered.
The controller uses one native resource and one Fusion worker; independent offline batches can run alongside it.
Models are disabled. Native source measurements do not establish editable target conversion.

## Deterministic decoding

The CLI was installed with Python 3.14 into task-only temporary tool directories.
The separate research checkout remains detached at the fresh base above.
The existing controller/supervisor, `InferenceSession` protocol and private native transport execute the jobs.
`Worker.py` needs a private `Paths.json` selecting absolute `root`, `cli`, `client`, `capture` and `verify` paths.
No credential belongs in that file or this package; the selected private client directory owns its existing credential file.
The worker explicitly binds the client's configuration base because supervised workers have a private home directory.

Use `Evidence/Corpus.json` with a trusted checkout that contains the committed native-input Git objects:

```sh
kit research --offline --root /absolute/trusted/research-checkout fusion \
  --manifest /absolute/campaign/Evidence/Corpus.json \
  --asset re/Fusion/TwoSidedDraft20261127/Native/baseline.f3d \
  --output /absolute/unused/output
```

Select all 68 asset paths for the complete batch. Add `--allow-partial` only for explicit fallback after strict refusal.
Strict replay accepts the two untapered controls and rejects 66 drafted states.
Explicit partial replay retains all 68 documents/receipts: two strict and 66 partial outcomes.
The refusal reasons include `Unsupported native second side distance or taper` and the independent non-identity-placement guard.
The former is an explicit zero-second-taper admission rule in `src/convert/adapters/Fusion/Native/Parameters/ReadParameters.py`; the latter is in `Native/Graph/GraphValues.py`.
Existing native angle fields are already decoded. These public guards remain unchanged, and their refusals are not evidence of unknown wire grammar.
The JSON-only `Evidence/ReaderArtifacts.tar.gz` retains both summaries and all published documents/receipts.
Exit 3 remains an explicit incomplete batch, not complete semantic decoding.

`CompareNative.py ROOT CAMPAIGN OUTPUT` independently runs the existing native helper on each hash-checked original file.
All 1,224 comparisons match: both distance and signed draft values, their four role bindings, side/condition/start/operation settings, circle radius/placement and explicit owners.
All 136 BRep initial tables parse with the existing production width-aware reader.
The separate research ASM8-only helper refuses unique same-asset BODY association on these ASM4 saves; complete reconstruction remains unqualified.
A successful initial table parse does not qualify the solved geometry or lifecycle identity graph.
`Evidence/NativeComparison.json` retains successful fields and reconstruction refusals without substituting ordinal BODY candidates.
`Package.py RUNTIME CAMPAIGN` rechecks retained lifecycle observations and builds the evidence files and their `Manifest.json` seals.

## Refusals and remaining work

The first eleven verification preparations were refused before native submission because two embedded controls exceeded the existing 256 KiB script limit.
Those original failures remain terminal and retained in `Evidence/FailedAttempts.json`.
Revised queued template generations carry one intact, losslessly compressed known control measured both before and after.
The worker checks fully rendered UTF-8 size before submission. No API limit was raised and no unknown native request was blindly retried.
See the [transport-size gotcha](../../../Documentation/Gotchas/Research/Workers/Verification/PersonalApiScriptSizeControl.md).

Original requests, failed preparations, controller ledger, detailed native decode documents and fresh exported verification archives remain in `/private/tmp/KitTwoSidedDraft20261127`.
Published failure summaries scrub private home paths and preserve original receipt hashes.
The package's unresolved register retains complete source-to-BODY reconstruction, portable two-sided taper admission, independent sketch-driver edits and target conversion as unfinished.
No proprietary binaries, vendor listings, model execution, production donor data or CAD runtime dependency were added.
Planning is a separate unmerged delivery on PR #392; this task retains its established register claim for later stable scope linkage.
