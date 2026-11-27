# Admit the SOLIDWORKS 2026 captured controls

The [control admission record](../../../re/solidworks/v2026/ControlAdmission.md) records, for
the committed SOLIDWORKS 2026 research inputs, whether each pinned file exists with the
recorded SHA-256 and whether the values recorded for it match what the repository's own
pinning and campaign verifiers report. It covers baseline items 1 and 5 of the
[SOLIDWORKS reader and writer delivery plan](../../Maintenance/SolidworksReaderWriterPlan.md).

## Behavior

The record has two parts. First, the [build manifest](../../../re/solidworks/v2026/Manifest2026.json)
pins SOLIDWORKS 2026 SP05.2 build `34.5.2.0604` and 14 licensed modules by length and SHA-256;
the modules set `tracked_in_git: false`, so they are pinned but not hash-checked in a checkout.
Second, the seven committed captured controls under `re/solidworks/v2026/corpus/` are admitted
with their length, SHA-256, Git blob at the corpus pin revision `f643a3dd`, introducing
revision, primary expected-value record and pass/fail result.

## Usage

Read the record before treating any of those seven parts as a control. Re-run the listed
commands to reproduce it:

```sh
sha256sum re/solidworks/v2026/corpus/*/*.SLDPRT
python3 re/automation/Corpus.py snapshot --revision f643a3dd01555bc18cc49aa973cf3f7d3ff21ad2 --manifest /tmp/verify/canonical_f643a3dd.json
python3 re/NativePlacement2026/Verify.py --output /tmp/verify/np.json
python3 re/FeatureLadders2026/Verify.py --output /tmp/verify/fl.json
```

## Limits

All seven controls exist and their working-tree SHA-256 equals both the blob at the corpus pin
and the value recorded in `CanonicalCorpus.json` and in each control's primary measurement
record. A fresh `Corpus.py` snapshot at `f643a3dd` differs from the committed
`CanonicalCorpus.json` only in 33 normalized evidence entries, with zero differing assets.

The record also documents gaps: `Corpus.py check` cannot run on
`re/automation/Corpus.json` because its pinned revision `74a0bc35` is absent from the
repository; `Corpus.py check` fails on the published `CanonicalCorpus.json` because of that
documented path normalization; and neither campaign verifier references these seven controls,
so their passing status is not admission evidence for them. No numeric tolerance is recorded
for the controls. The record is research evidence and does not qualify native writing or
conversion acceptance.

## Verification

`git` 2.43.0 and Python 3.12.3 at `main` `1619f00b`. The record's commands were run and their
observed output is quoted in the record: `Corpus.py snapshot` at `f643a3dd` exits 0 with
`{"native_by_format": {"f3d": 2040, "f3z": 2, "sldasm": 6, "sldprt": 248}, "evidence_files": 299, "qualified_pairs": 0, "native_acceptance": "not_established"}`;
`re/NativePlacement2026/Verify.py` reports `passed`; `re/FeatureLadders2026/Verify.py` reports
`passed`.
