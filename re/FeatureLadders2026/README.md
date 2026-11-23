# Native feature ladders, 2026-11-22

This is discovery evidence, not conversion acceptance or a qualified codec change.
The source SDK revision is `c8d85d713dc357770115329e9f1bcb027dbfca4f`.
Task `A08h-Ladders2026` records this scoped follow-up to merged PRs #158 and #207.
Codex owns packaging and investigation; no claim is made on their broader programme.

## Scope and outcomes

The campaign planned 96 native batches and 288 files, with capacity one per application.
Each batch creates a rectangular sketch and blind extrusion, with controls before and after the variation.
Independent variations change width, height or depth across front, top and right planes and both extrusion directions.
The complete native batch duration was 25.09 minutes. Offline inspection finished afterward.

- Fusion completed all 48 batches and returned 144 files. Twenty-four strictly projected to neutral documents.
- SOLIDWORKS completed 11 batches and returned 33 files. All 33 strictly projected to neutral documents.
- One SOLIDWORKS batch failed after recovery, and 36 further batches were blocked before dispatch.
- All 120 Fusion neutral refusals retained their strict diagnostics. Typed native-state inspection parsed all 120.
- Native requested-volume comparisons passed for all 177 returned files. Twenty-four Fusion neutral volume comparisons passed.
- SOLIDWORKS neutral volume and surface-area comparisons remain unavailable. A decoded body is not numerical geometry acceptance.

These are not 177 independent feature families. Repeated controls are intentional.
The independent shape family is the ordinary rectangle boss; plane, direction and scalar values vary.
No sketches with independently measured driving constraints, complex histories, assemblies or drawings were qualified here.
No target conversion, independent edit/reopen acceptance, held-out semantic qualification or production decoder change is established.
All new files are discovery material. They cannot be relabelled as held-out evidence for a rule trained on this campaign.

## Published data

`Manifest.json` lists the source identity, all 96 cases, every native outcome, and every published artifact hash.
`Cases/` retains original API-saved CAD files and native ground truth.
`Reports/` retains gzip-compressed neutral or typed-native JSON, with zero gzip timestamps.
`Programs/` retains the exact submitted owner-authored Python recipes. They require the application's `app` and private `work` objects.
These scripts are research generators, not SDK runtime code. Their controlled native templates are never production writer donors.
`Attempts.json` keeps sanitized attempt identities, controller fingerprints, retries and outcomes.
`ControllerStatus.json` is the final read-only controller snapshot. Parked old attempts remain visible after successful recovery retries.
Aggregate the manifest by logical case, not by counting all attempt states.
`Comparisons.json` and `Summary.json` state the measured scope and unresolved semantics.
`EarlierCorpusOutcomes.json.gz` retains all 778 pinned-input strict outcomes and completed partial-fallback summaries.
Those source files were already committed. Earlier expanded derived documents remain in the private run and can be replayed.
Partial fallback was stopped by the user; its documents never count as strict successes.

Published reports replace local paths and host names. The manifest retains original and published report hashes.
Original private logs, controller SQLite state, job tokens, process identities and personal CAD transport configuration remain outside this package.
No vendor executable, template, library, interop assembly or SDK is included.

## Inspect and verify

Use Python 3.14 for Fusion ZIP Zstandard inputs.
From the repository root, choose an unused report path:

```sh
python3 re/FeatureLadders2026/Verify.py --output /tmp/FeatureLaddersVerification.json
```

The verifier checks every published artifact hash, strict/partial classification, control boundaries and recorded native volume.
It checks evidence consistency. It does not open CAD applications or qualify conversion.
Read a compressed report with `gzip -dc PATH.json.gz`.
Re-run a native file through the public reader with a new output path:

```sh
kit decode re/FeatureLadders2026/Cases/fusion-000/variation.f3d -o /tmp/FusionLadderReplay.json
kit decode re/FeatureLadders2026/Cases/fusion-008/variation.f3d --layer native -o /tmp/FusionLadderNative.json
```

Neutral failures must retain their strict refusal. A typed-native report does not replace a successful neutral projection.
Use the manifest source revision for exact baseline replay. Later decoder changes require their own revision-bound evidence.

## Blockers and follow-up

SOLIDWORKS lost its COM RPC connection. Supported recovery allowed three further batches before the fault recurred.
The failed session's cleanup also reported the unavailable RPC server. This does not identify a format defect or prove a safe host restart.
Investigate the native service/process evidence before further native recovery. Successful cases must not be resubmitted.

Fusion refuses 72 reverse prisms without the supported constrained-rectangle proof, 24 non-identity placements and 24 unconstrained YZ prisms.
The strict gates protect currently proven semantics. Do not delete them to obtain green results.
Use the measured files and typed graph records to establish a general rule, then verify it on separately authored held-out controls.
The broader native-worker integration, constraint recovery and bidirectional editable conversion remain open.
