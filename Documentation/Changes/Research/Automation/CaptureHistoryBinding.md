# Capture history binding on an automation-only branch

The clean automation branch starts from main without inheriting the former PR's vendor-DLL commits. Copying unchanged files does not recreate their original capture introduction. `CaptureLineage.json` therefore pins original source `f5b23031c4163528a2e4f5029ab34102133b983e`, its existing source ref and the SHA-256 of the complete 130-file input roster, including tracked modes and blob IDs.

## Usage

Fetch the preserved metadata and explicitly permitted research inputs before corpus validation:

```sh
uv run --frozen python re/automation/CaptureHistory.py fetch
uv run --frozen python re/automation/Corpus.py check --manifest re/automation/Corpus.json
uv run --frozen python re/automation/PairedCaptureIntake.py --revision CURRENT_FULL_SHA --lineage-contract re/automation/CaptureLineage.json
```

Replace `CURRENT_FULL_SHA` with the exact candidate commit. Network hydration accepts only the bundled authority, verifies the existing ref and requests its exact commit with `blob:none`. It fetches missing blobs explicitly from the sealed capture roster, original authoring fixtures and original corpus manifest. Recognized native CAD controls, evidence and historical notes are research inputs; vendor software is prohibited. Extension and recorded-prefix screening supplement the sealed roster; they are not independent content validation. No old checkout, decoder execution, branch rewrite or receipt rebinding occurs.

Intake checks the current capture roster for exact identity, then evaluates introductions, ancestry and authoring provenance on the original graph. It also checks aliases across the entire current tree and retains historical quarantine and qualification blockers. Changes to input content, modes or membership fail closed. Historical corpus source revisions, measurements and frozen-rule reservations are unchanged.

Both Git subprocess paths, including streaming corpus reads, discard inherited `GIT_*` overrides, disable replacement objects, grafts, system/global configuration and lazy fetching. Shallow repositories are refused because a declared boundary can hide original parent objects. Missing objects require explicit acquisition rather than an implicit historical payload fetch.

## Evidence and limits

Metadata inspection established the 130-file contract digest `ca44feca3f2ca32cd852f32e4afde2e5a2b334a8c83a150e813d8256f6c106b6` against the preserved original tree. New process coverage exercises intact binding, changed/missing/extra inputs, mode changes, replacement refs, grafts, a bad contract, absent lineage, an external native alias, streaming blob replacement and hostile Git environment variables. These cases are authored for hosted execution; no local tests or application runs were performed. Static verification is recorded with the published candidate.

This preserves custody, not native qualification. Ten receipts and 74 paired native files still establish zero qualified pairs. The separate missing original Fusion source, licensed same-installation restart chain, supplemental admission and two-week pilot remain open. See the [step register](../../../Reference/Research/AutomationSteps.md), [clean-history gotcha](../../../Gotchas/Git/CleanHistoryNeedsOriginalLineage.md) and [Git identity gotcha](../../../Gotchas/Git/GitReplacementsCanAlterLineage.md).
