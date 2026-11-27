# Signed offset starts on unequal two-sided extrusions

This is source-native research evidence. Complete portable decoding, reconstruction and conversion acceptance remain unfinished.

Task `A08h-FusionOffsetStart20261127` is owned by Codex on `feat/fusion-offset-start-20261127`.
Fresh base and frozen reader checkout: `91a73de348894a5791a51b977cd6fe0fe677a617`.
Committed native inputs: `1647204042fca11349eb62a4e495387204648c8b`.
The [automation register](../../../Documentation/Reference/Research/AutomationSteps.md#a08h-fusionoffsetstart20261127) owns status and exit conditions.

## Selected contrast

Existing `Notes/Extrude.md` explains the independent distance and offset operands, and the existing extent corpus has signed one-sided offsets.
The earlier A08i offset-plane builder and the ProfilePlane draft campaign in PR #394 do not supply this combined three-driver lifecycle evidence.
This campaign measures unequal, untapered, two-sided NewBody circular extrusions with an explicit OffsetStart definition.
The baseline uses first/second distances 17/29 mm, offset +7 mm, radius 13 mm and center `(7,-11)` mm on XY.
One-factor contrasts change each distance, offset sign/zero, radius, profile placement or XY/XZ frame.
Swapping the side distances preserves volume while reflecting the axial centroid about the offset plane.
Two sealed parameter holdouts combine unseen distances, offsets, radius, placement and frame.
They share the generator lineage and do not qualify independent lineage or the programme's reserved P05.

`Capture.py` fixed this roster and analytical prediction before dispatch.
Its pre-dispatch SHA-256 is `05d677a4971d4050c976ac3d959abdc32be2da7058755bf3ead007ad2fb0b18e`.
Every captured geometry and parameter comparison passes: 79 API observations and 57 archives.
The cylinder stations are `offset-second` and `offset+first`, in internal centimeters.
Volume depends on the summed side distances; centroid also distinguishes their roles and the signed start placement.
Changing offset alone translates the body without changing its volume.
No new wire grammar is inferred from this geometric agreement.

## Expanded contrasts

The user then requested a larger scope while decoding continued in the background.
`ExtendedCapture.py` freezes sixteen additional cases before dispatch, with SHA-256 `df560d27acc45a6aa3e812cfb4b4e70bbe4a251ddeb380e409c9ddfe91c49356`.
The extension adds first distances 0.125, 25.4 and 97.5 mm; second distances 0.375, 31.75 and 83.25 mm; signed offsets -101, -1, 12.7 and 107 mm; a 0.9 mm radius and YZ placement.
Four additional holdouts combine independent fractional distances, signed offsets, radii, centers and frames.
The -1 mm offset edit crosses to +2 mm; the extreme offsets place both cylinder ends on one side of the sketch.
The initial 57-file source commit and original receipts remain unchanged.
Expanded native sources, captures, manifests and receipts live under `Expansion/`, with separate runtime jobs and source revision.
The two groups contain 27 modelling cases and 139 saved archives, including four native controls.
All 405 fresh-process lifecycle, control and process comparisons pass across 27 distinct process IDs.
The [combined summary](Evidence/CampaignSummary.json) binds both groups, 193 source observations, 2,780 native comparisons and 278 BRep initial tables.
The two reader archives retain 282 JSON artifacts: 139 partial documents, 139 receipts and four batch summaries.
The oracle was released idle without a recovery marker; controller outcomes retain both prefix refusals and all completed jobs.

## Native process and edit evidence

Fusion `2706.1.17` authored the samples through the private serialized CAD API in an empty owned session.
Both zero-offset controls use the same explicit OffsetStart type as the candidates.
Each case saves its baseline, independent +3 mm edits of first distance, second distance and signed offset, then restoration.
The signed offset edit changes the signed value directly, including a zero-to-positive control; extent magnitudes preserve their existing side signs.
`Capture.json` retains requested specifications, actual expressions, model parameter roles, body count, volume, area, centroid, bounds, frame and feature health.

`Verify.py` opens each baseline in a different fresh owned process.
It measures initial open and rebuild, independently edits/restores all three drivers, exports/reopens each edited save, and saves/reopens restoration.
One unchanged known zero-offset control is rebuilt and measured before and after each process.
Source/control hashes, process IDs, executable hashes, exports, errors and empty document inventories stay in the report.
`Evidence/Summary.json` and `Evidence/NativeVerification.json` record actual completed counts and pass/fail dispositions.
Radius and profile placement vary during authoring but remain outside independent driving-dimension lifecycle checks.
No unrelated application session is attached to, stopped or recovered.

## Deterministic reading

A separate trusted research checkout remains detached at the fresh base above, with a task-only Python 3.14 CLI installation.
The existing A03 controller and configured supervisor run offline batches concurrently with the single serialized Fusion resource.
`Worker.py` implements the existing `InferenceSession` result contract and private native script transport; it changes no shared workers.
Its private `Paths.json` selects absolute `root`, `cli`, `client`, `capture` and `verify` paths. The private client owns its credential file.
Models remain off.

Replay committed files with the frozen checkout and unused output directory:

```sh
kit research --offline --root /absolute/trusted/reader-checkout fusion \
  --manifest /absolute/campaign/Evidence/Corpus.json \
  --asset re/Fusion/OffsetStart20261127/Native/baseline.f3d \
  --output /absolute/unused/output
```

Repeat `--asset` for all 57 paths. Add `--allow-partial` only for explicit fallback.
Strict reading rejects all 57 with `Unsupported native Fusion DcExtrudeFeature.profileLocaltionType`.
Explicit partial replay retains all 57 documents and receipts, with zero reader errors.
The native inspector independently matches 1,140 fields and bindings: distance/taper operands, signed offset, ProfileOffset role, start/extent/operation, circle placement and profile/component ownership.
The existing production width-aware reader parses all 114 BRep initial tables.
Complete source-to-BODY reconstruction remains separate: the research ASM8-only helper does not qualify the ASM4 identity route.
These are known admission and helper limits, not evidence that offset-start wire grammar is unknown.
The public policy remains unchanged. See the [zero-offset type gotcha](../../../Documentation/Gotchas/Research/Campaigns/ZeroOffsetRetainsStartDefinition.md).

`CompareNative.py ROOT CAMPAIGN OUTPUT` reuses existing inspectors and checks hashes before comparisons.
`Package.py RUNTIME CAMPAIGN` verifies each group’s lifecycle measurements and packages documents, receipts and summaries.
After both groups complete, `Seal.py RUNTIME CAMPAIGN` validates aggregate counts, controller outcomes, oracle release and background worker overlap before sealing all files.
The JSON-only reader archive retains every published strict/partial outcome. Exit 3 is incomplete decoding.
Neither partial decoding nor native source acceptance establishes editable target conversion.

## Preserved failures and gaps

The first two offline attempts rejected a campaign-authored manifest with a 14-byte prefix instead of the existing verifier's required 16 bytes.
No input bytes changed. Corrected controller jobs use a new identity and output directory, while `CorpusInitial.json`, failed receipts and logs remain retained.
The native resource initially stayed queued until explicitly marked available in the controller; no session or lease was stolen.
The existing rendered-script size guard and single losslessly compressed control avoid the prior campaign's oversized transport requests.
Raw requests, controller ledger, detailed native decodes and fresh exported copies remain in `/private/tmp/KitOffsetStart20261127`.
Published failure summaries remove private home paths and bind original receipt hashes.

Remaining work includes complete portable source admission, ASM4 body identity/reconstruction, independent sketch-driver lifecycle, broader operations/taper combinations, independent generator lineages and donor-free editable target acceptance.
`Evidence/Unresolved.json` retains these boundaries; no shared decoder or production support change is included.
Planning remains separately owned on unmerged PR #392, so this established register claim awaits stable linking there.
