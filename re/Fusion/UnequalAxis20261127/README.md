# Unequal two-sided revolutions about explicit construction axes

Research source evidence only. Complete reconstruction and conversion acceptance remain unestablished.

Task: `A08h-FusionUnequalAxis20261127`, owned by Codex on `feat/fusion-unequal-revolve-20261127`.
Fresh base: `331ef8ce95f7e46814c5086110be9a23478ca8a8`.
Native-input commit: `233985bac73d454f6df22e44dd3cad06bb92f7da`.
The [automation register](../../../Documentation/Reference/Research/AutomationSteps.md#a08h-fusionunequalaxis20261127) owns status.
The [change entry](../../../Documentation/Changes/Research/Campaigns/FusionUnequalConstructionAxisRevolutions.md) describes publication limits.

## Selection and freeze

Existing `Notes/Revolve.md`, `Study/revolve-mode-decoding.json` and `Study/revolve-axis-decoding.json` cover unequal angles and explicit custom axes separately.
This campaign combines them with independent changes to both angles, axis origin/direction and radial/axial profile offsets.
The rectangle remains 0.7 cm radially wide and 1.9 cm axially long. Operation stays solid NewBody, with projection disabled.
The baseline uses angles 61/23 degrees, axis origin `(1.1,-0.7,0)` cm, direction `+Y`, radial offset 0.8 cm and axial offset 0.6 cm.
Discovery changes only one of those factors per case; swapping angles and reversing the axis provide counterexamples to magnitude-only or fixed-direction interpretations.
The two `holdout_*` cases combine unseen angle pairs, translated oblique axes and profile offsets.
They are campaign-specific parameter holdouts, not the reserved programme P05 assets.

`Capture.py` fixed the analytical interval `[-second,first]`, centroid formula, case roster and holdout labels before native dispatch.
Its pre-dispatch SHA-256 was `33007f4c0806180c364d1d4ac43d47a874cc8eccc0fb49ffaf3600f27f4b1934`.
No reader rule was fitted or changed after observing these files.
The separate SDK/research checkout stayed detached at the frozen base above.
GitHub initially refused publication because the task commits used a private email.
Only those unpublished task-owned commits were recreated with the verified public noreply identity and identical trees.
`Evidence/PublicationCommitMap.json` preserves the old/new identities. The original objects and reader runs remain retained privately.
Strict and partial decoding were repeated against the publishable source commit, preserving exact blob hashes and new revision-bound receipts.
Holdout observations were measured alongside discovery, but their bytes did not contribute to a new decoder rule; none is proposed.

## Native evidence

`Capture.json` retains actual API observations and requested inputs for eleven cases and two controls.
All 57 creation, independent first/second-angle edit and restoration observations match volume and centroid predictions within `1e-7` cm³/cm.
Each angle edit adds seven degrees while holding the other fixed.
The capture saved baseline, both edited states and restored state per case, plus two controls: 46 original native files in `Native/`.
These are oracle-authored research sources, never writer templates or package data.

The existing private API serializes Fusion requests and starts only its owned fresh session.
No other session was attached to, terminated or recovered.
Capture job: `ce9d27182f07b063c541f3d0847fce89`; native build `2706.1.17`, owned PID `31104`.
`Evidence/NativeVerification.json` retains subsequent independent-process opening, rebuild, both angle edits, restoration, export and reopen observations.
It includes controls before and after each case, native process IDs and an executable SHA-256.
`Evidence/Summary.json` records the actual counts and dispositions; source acceptance does not qualify target conversion.
Axis and profile offsets are varied at authoring time. Independently driven axis/profile dimension edits remain outside the measured lifecycle.

## Deterministic execution

The existing P05 catalogue builder exposes one angle and cannot express these two angles and an explicit axis.
Campaign-local `Capture.py` therefore reuses the established TwoPoints/line-profile/two-sided native API sequence through the existing private script worker.
The shared builders, native workers and decoders remain unchanged.
The saved planner catalogue confirms the two-side method and axis input declaration; declarations alone do not qualify execution.

The CLI was installed with Python 3.14 into an isolated temporary tool directory using `uv tool install --python 3.14`.
`Worker.py` uses the existing `InferenceSession`, controller, supervisor and private native transport.
Its private `Paths.json` selects `root`, `cli`, `client`, `capture` and `verify` absolute paths; no credential belongs in this package.
The `client` directory is explicitly bound because supervised workers receive a private home directory.
Two offline batches and serial native jobs use the existing pools and an exclusive campaign resource.
Every native job has one attempt. Retained failed preparations get distinct follow-up job IDs, never an invisible replay.

The native asset manifest pins committed blobs from the input commit; offline SDK sources remain pinned to the fresh base.
`Evidence/Corpus.json` permits this reader command from a trusted research checkout with those Git objects:

```sh
kit research --offline --root /absolute/trusted/research-checkout fusion \
  --manifest /absolute/campaign/Evidence/Corpus.json \
  --asset re/Fusion/UnequalAxis20261127/Native/baseline.f3d \
  --output /absolute/unused/output
```

Add `--allow-partial` only to retain the strict rejection followed by explicit partial fallback.
The full run selects all 46 `--asset` paths.
Strict replay rejects all 46; partial replay preserves 46 unqualified documents and their individual receipts.
`Evidence/ReaderArtifacts.tar.gz` retains both summaries and the partial documents/receipts.
Exit 3 remains a published refusal, not completed decoding or conversion.

`CompareNative.py ROOT CAMPAIGN OUTPUT` independently runs the existing native helper on each hash-checked original file.
Its final 552 comparisons include angle roles, operation, solid/projection flags, selected-axis geometry/ownership, component ownership, explicit support qualification and profile placement.
544 match; eight support qualifications refuse. `Evidence/NativeComparison.json` preserves each field and diagnostic.
`InspectFraming.py ROOT CAMPAIGN OUTPUT` records actual BRep framing and the point-provider prefix observations.
`Package.py RUNTIME CAMPAIGN` rechecks fresh-process observations against the original readings and builds the evidence package.
`Manifest.json` seals the published files.

## Remaining evidence and failures

All 92 native BRep members have `ASM BinaryFile4` framing; the existing production initial-table parser reads all 92.
The separate `Study/asm_records.py` helper expects `ASM BinaryFile8`, so source-to-stored-body association and full reconstruction remain refused there.
A successful initial table parse is not complete geometry reconstruction.
The [existing width gotcha](../../../Documentation/Gotchas/Conversion/Fusion/History/FusionAsmIntegerWidth.md) applies to current saves too; this is not an unsupported-grammar claim.

Eight files from `second` and `swapped` retain `Unsupported construction-mode point provider`.
Observed 178-byte providers retain method 10 and the owning-axis trailer, but some bytes in the first 23 are nonzero.
The same axis inputs also produce accepted prefixes in other documents; no causal angle relationship or byte meaning is established.
Keep the guard until independent evidence proves a rule. See the [prefix gotcha](../../../Documentation/Gotchas/Research/Campaigns/FusionPointProviderPrefixRefusal.md).
No shared decoder repair is included.

`Evidence/FailedAttempts.json` records the initial missing manifest `prefix_hex`, supervised private-home transport failures and invocation refusals.
Original logs, controller state, detailed native decode documents, requests and receipts remain in `/private/tmp/KitUnequalAxis20261127`.
Published derived summaries scrub private home paths; original receipt digests remain recorded.
No models, proprietary binaries, vendor listings, production donor data or conversion runtime dependency were added.

General profiles, Boolean operations, other occurrence frames, support-provider prefix semantics, full ASM reconstruction, axis/profile driving edits and editable target conversion remain open.
Planning was absent from the task's fetched main; the existing child claim is retained for later linkage after that register has a stable delivery.
