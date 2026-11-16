# Saved circle reader inputs

`re/tooling/sw2026/PrepareSavedCircles.py` prepares the six vendor-saved derivatives from the two generated circle boss measurements. These inputs support remote archive/semantic comparison after native edits and saving. They add no generated writer outputs or held-out cases, and native acceptance does not transfer to privacy-modified fixtures.

The preparer binds the exact native receipt hash, original job hash, six saved-file hashes, source executable identity and neutral requests. Expected center, radius, radial mode and depth come from each neutral request and explicit edit factors. It rejects incomplete native phases, different membership/builds, changed sources and existing output directories.

```sh
uv run --no-sync --python 3.11 python re/tooling/sw2026/PrepareSavedCircles.py \
  /private/NativeCircleBossRun /path/to/CircleBossInspection01.json \
  /private/InspectionJob.json /private/NewSavedCircleCorpus \
  --expected-receipt-sha256 RECEIPT_SHA256 --redact-name PRIVATE_ACCOUNT_NAME
```

Like the existing discovery preparer, this is actual research data preparation through a bounded real container-module loader. It executes no archive schemas, round trips, conversion or tests. It preserves native streams and performs only supported, equal-width framed metadata redactions, recording each changed span by context and hash. Unknown private contexts fail before writing. The prepared containers are not reparsed locally. Metadata and preview privacy review is bounded and does not prove exhaustive privacy coverage.

Outputs include six `.SLDPRT` reader inputs, `Manifest.json`, `PrivacyLedger.json`, `SourceEvidence.json` and extracted `PreviewPNG` files when present. Keep originals outside the checkout. Review extracted images before publishing prepared fixtures. Runtime writers must never load any of these saved files or metadata ledgers. Remote CI must independently parse the complete archives, require proven schemas, compare emitted bytes and check decoded semantics against neutral targets.

Verification at introduction: source inspection and AST review only. The first actual preparation stopped before destination creation on a private framed CString in `Contents/CMgr`. The discovery corpus helper's original stream allowlist excluded that stream. The helper now accepts an explicit additional metadata-stream argument, empty by default; only this saved-copy preparer opts into CMgr framed-string redaction. This fixture transformation does not identify the private string's exact native field or transfer original native acceptance. The [saved-metadata gotcha](../../../Gotchas/Conversion/Solidworks/Model/VendorSavesCanAddPrivateConfigurationStrings.md) records that boundary. Preparation and remote reader results remain pending. The [circle boss ledger](../../../../re/solidworks/records/CircleExtrusionSynthesis2026.md) retains the separate native measurement and unresolved boundaries.
