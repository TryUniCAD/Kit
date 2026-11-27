# November 25 capture failures: committed-record audit

Investigation of the 12 capture failures that the SOLIDWORKS reader/writer plan attributes
to a November 25 retry run. `re/automation/CompareDecoded.py` was not modified.

## Summary

**No committed per-failure record of the plan's November 25 retry run exists.** The figures
("50 unresolved decodes", "12 capture failures", "7 body-measurement", "5 sketch-region") appear
only in the plan paragraph on PR #296; no committed run, receipt, manifest or artifact set carries
that breakdown, so the 12 failures cannot be reproduced, compared or clustered. The committed
capture-failure records that do exist are clustered with their real counts below; they are a
different, smaller set and are not presented as the plan's 12.

## Question

The plan on PR #296 (`Documentation/Maintenance/SolidworksReaderWriterPlan.md`, commit
`d9ab9e067`, present only on that branch and not on `main`) states:

> The November 25 retry run recorded 50 cases with unresolved decoding and 12 capture failures.
> Seven failures concerned body measurements. Five concerned sketch profile regions or areas.

The task was to find the committed per-case records behind those 12 failures, run
`re/automation/CompareDecoded.py` on the committed artifacts, and group the 12 by root cause,
saying for each group whether it is decoder-side or needs a SOLIDWORKS re-capture.

## Finding

No committed record of that November 25 retry run exists in the repository. The only committed
occurrence of the phrase is the plan paragraph on PR #296 itself. No committed SOLIDWORKS run
records 12 capture failures, and no committed run records a 7 body-measurement / 5 sketch-region
split. There are therefore no per-case artifacts to decode, no decoded-JSON pair for
`CompareDecoded.py` to compare, and no honest basis for a decoder-side versus re-capture
classification of those specific 12 failures.

This is a negative result, not a substitute cluster analysis. The committed runs that are nearest
in time and topic are listed below with the failures they actually record, so a later reader can
see what does exist and can supply the missing run directory.

## Exact commands run

All commands were run from the checkout root. `main` is at `1619f00bf`.

```sh
# Locate the plan document and its only mention of the run
git fetch origin pull/296/head:pr296
git show pr296:Documentation/Maintenance/SolidworksReaderWriterPlan.md
git log --all --oneline -S"capture failure"
git log --all --oneline -S"November 25"
git log --all --oneline -S"unresolved decoding"

# Search the worktree and full history for the failure categories and counts
grep -rIl -e "November 25" -e "Nov 25" -e "Nov25" -e "2025-11-25" .
git grep -il -e "november 25" -e "nov 25" pr296 -- re Documentation
git log --all --oneline -S"body_measurement"
git log --all --oneline -S"sketch_region"
git log --all --oneline -S"capture_failure"
git log --all --oneline -S"12 capture"
grep -rIlnE -e 'body[_ -]?measure' -e 'sketch[_ -]?region' -e 'capture[_ -]?fail' \
  --include=*.json --include=*.md --include=*.csv re Documentation
grep -rInE '"unresolved[A-Za-z_]*"[[:space:]]*:[[:space:]]*[0-9]+' re Documentation
grep -rInE '"(failed|capture_failures|failures)["]?[^:]*:[[:space:]]*12' re Documentation

# Inspect every committed directory that records run failures or retries
find re -type d \( -iname '*failur*' -o -iname '*retry*' -o -iname '*cycle*' \) -print
git log --all --since=2026-11-24 --until=2026-11-28 --name-only --pretty=format: | sort -u

# Confirm the comparison tool's inputs (it was not edited)
python3 re/automation/CompareDecoded.py --help
```

## Committed run records near November 25

The following committed records are the only run evidence found in that window. None is the
November 25 retry run described by the plan, and none contains 12 capture failures.

### SOLIDWORKS feature ladder recovery (`re/solidworks/FeatureLadderRecovery`)

A genuine SOLIDWORKS retry/recovery run, committed by `16809c2ce` (2026-11-24) for PR #270.
It re-captures 37 previously missing batches (`solidworks-059`..`solidworks-095`, 111 native
files) and retains exactly two failed attempts: one COM failure (`com_error: (-2147023170, ...)`
in `OriginalFailedAttempts.json`, case `solidworks-068-restart`) and one local supervisor
settlement failure. `Manifest.json` records all 111 files as `strict_decoded` and all 37 cases as
`complete_controlled_batch`. Its recorded problems are neutral placement and the absence of
explicit neutral volume and surface-area properties, not 12 capture failures.

### Fusion rim-fillet pack (`re/Fusion/RimFilletPack`)

The only committed run with exactly 12 cases and a 7/5 outcome split. Its process timestamps are
2026-11-25T22:35Z-23:28Z and it was committed by `7dd610f03` (2026-11-26) for PR #301.
`README.md` records "Five native-saved sources reconstructed. Seven retained the explicit
four-byte snapshot-header refusal." That is 7 + 5 = 12, but the categories are a snapshot-header
refusal versus a successful reconstruction on **Fusion** inputs, not the SOLIDWORKS
body-measurement / sketch-region categories in the plan. `Failures/` holds six decode artifacts
that all reduce to "Native Fusion projection requires a sketch followed by one extrusion" or
"Unsupported native Fusion feature class".

### Earlier feature ladder campaign (`re/FeatureLadders2026`)

Committed 2026-11-22 by `7a0a987ec`. `Summary.json` records 96 batches, 177 returned files,
57 `strict_decoded` and 120 `strict_rejected`; one SOLIDWORKS batch failed after recovery and 36
were blocked before dispatch. The 120 rejections are unresolved decoding, not capture failures,
and the count is not 50.

### Cut and revolution campaign (`re/CutsRevolutions2026`)

Committed 2026-11-23 by `2b7497e9e`. `Summary.json` records 30 planned batches, 51
`strict_rejected_or_failed`, and native receipts of 20 completed / 1 blocked / 2 failed. Its
`README.md` states that raw commands, logs and receipts remain outside the checkout at
`/tmp/KitFeatureCampaign-20261123b`.

### Encoder round-trip (`re/solidworks/measurements/2026/EncoderRoundTrip`, `re/Fusion/EncoderRoundTrip`)

The Fusion native measurements are dated November 25 (`re/Fusion/EncoderRoundTrip/NativeEvidence.md`).
The run covers four SOLIDWORKS roles and two Fusion roles. It records the strict SDK reader
refusing the four vendor-saved variants, not 12 capture failures.

## Committed capture-failure records that do exist, clustered by root cause

These are the capture- or process-level failures actually recorded in committed artifacts near
November 2026, grouped by root cause with their real counts. None is the plan's 12. "Decoder-side"
means fixable offline from the committed bytes; "re-capture" means a fresh licensed native run is
required.

| cluster | root cause | committed count and evidence | side |
| --- | --- | --- | --- |
| SOLIDWORKS native COM/RPC loss | The COM RPC connection drops mid-run and the host service needs investigation | 37 cases (36 batches blocked before dispatch plus 1 failed) in `re/FeatureLadders2026/Summary.json`; 1 retained COM failure in `re/solidworks/FeatureLadderRecovery/OriginalFailedAttempts.json` | Re-capture / host repair. Not decoder-side. |
| SOLIDWORKS capture shutdown timeout | The owned SOLIDWORKS process does not exit normally after `QuitDoc`/`ExitApp`, so cleanup is forced | 21 failed P04 attempts, six cases exhausting their retries, in `Documentation/Changes/Research/Supervisor/Catalogue/SolidWorksCaptureShutdown.md` | Re-capture / worker repair. Not decoder-side. |
| SOLIDWORKS thin-wall side | The one-sided wall is captured on the wrong local side of the sketch frame | 1 written-recipe batch withheld, three recipes, in `Documentation/Changes/Research/Supervisor/Catalogue/SolidWorksThinWallSide.md` | Capture/authoring-side; the corrected recipe needs a fresh capture to verify. |
| Fusion malformed snapshot header | A four-byte snapshot-header field is malformed and complete archive emission is refused | 6 cases in `re/Fusion/RimFilletPack` (`Qualification/HeaderGuards.json`, `README.md`) | Decoder-side guard; no re-capture. |
| Fusion decode/projection refusal on a captured file | The strict reader refuses a captured file's feature or projection | 6 decode artifacts in `re/Fusion/RimFilletPack/Failures/`; 120 `strict_rejected` in `re/FeatureLadders2026/Summary.json`; 4 vendor-saved variants in `re/Fusion/EncoderRoundTrip/NativeEvidence.md` | Decoder-side, but this is unresolved decoding rather than a capture failure and is tracked by the unresolved-decode audit. |

## Why CompareDecoded.py could not be applied

`CompareDecoded.py` compares two directories of decoded `CadDocument` JSON, or an explicit
version-1 pair manifest:

```sh
python3 re/automation/CompareDecoded.py --left LEFT --right RIGHT --unit mm -o OUTPUT
python3 re/automation/CompareDecoded.py --manifest MANIFEST --unit mm -o OUTPUT
```

No committed decoded-JSON pair is associated with the 12 failures. The run the plan cites has no
committed per-case decode outputs; the campaign READMEs that do exist state that raw outputs,
controller state and logs remain outside the checkout (for example `/tmp/KitFeatureCampaign-20261123b`
and `.rescratch`). With no left/right inputs there is nothing for the tool to compare, so no
command against the 12 failures is reported here. The tool itself is unchanged.

## Nearest committed evidence for the two stated categories

These are the closest committed observations to the plan's "body measurement" and "sketch region
or area" wording. Each is a single small run, not the November 25 run, and neither establishes a
7/5 split.

- Body measurement: `re/automation/BatchEvidence/ContinuousSessionObservation.json` retains one
  failed probe, recipe `extrude-thin`, result `written_recipe_body_measurements_differ`, with
  as-built and reopened volumes both 560 mm3.
- Sketch region/area: `Documentation/Changes/Research/Supervisor/Catalogue/SolidWorksBatchRejectionIsolation.md`
  records three thin-wall measurement failures that withheld nine cases across three batches in
  an earlier 62-case catalogue run.

## What would unblock this task

Supply the November 25 retry run directory or its state store (the plan's own paragraph does not
record one). With the per-case native files and their decoded JSON, `CompareDecoded.py` can be run
as specified and the 12 failures can be grouped by root cause and classified decoder-side versus
re-capture.
