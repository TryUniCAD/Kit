# Generate a constrained SOLIDWORKS Boss candidate from P03 evidence

Prepare one canonical request for the pinned, positive Front-plane P03 discovery baseline. This research entry point checks the exact source JSON, the logical edges, their shared point aliases, and the archived body owner before it writes the request. The original Join remains in the source evidence. The target model describes the first output body as Create. A native comparison of these operation semantics remains open.

## Prepare and replay

Run the [P03 source intent procedure](ConstrainedBossIntent.md) to create the source and logical JSON. Then use unused private paths and the Python 3.14 developer environment.

```sh
python -I -B re/automation/P03CandidateRequest.py \
  --source-json /private/p03-source.json \
  --logical-json /private/p03-logical.json \
  --output /private/p03-request.json
```

Keep the reported request SHA-256 separately. The one published request file contains the exact target document and its digest, the source and logical JSON digests, the ordered saved operands and record spans, and the body label evidence. Changing the file requires a new qualified preparation and independently retained digest.

Call `P03CandidateRequest.generate_request` from the research Python environment with the request bytes, the retained digest, and the existing explicit [`PortableBossContext`](../../../../re/solidworks/WriterResearch/VerifyFreshBoss.py). The context supplies caller-authored output identity, clocks, density, and presentation, as in the [bounded native constructor](../Writers/SolidWorks/Metadata/SolidWorksPortableBossCandidate.md). Omit `candidate` to run the existing in-memory generation and readback. Supply an unused `.SLDPRT` path to retain the research candidate. The original native archive and both original JSON files are unnecessary at generation time.

## Boundaries

The public read's `Body 1` is an unbound fallback for this archive. The saved compatibility atom has the `BlindBoss` label. The source custody records both. A separate exact archive check found the same implicit kernel label and no explicit body rename. The constructor uses the verified compatibility label in its own target view. The original documents and their native remainder stay intact.

The constructor's shared point slots represent the four inferred corner joins. The saved Origin remains a separate point and one native coincidence. The width and height retain their bottom and left anchoring roles and ordered operands. Complete source presentation, unrelated native features, and vendor-specific operation differences remain outside this research candidate.

The source-bound writer input does not establish whole-source preservation, native edit and save/reopen, a public conversion route, or independent held-out generalization. `vendor_loadable` and `application_usable` remain false until independently measured.

See [unbound body display label](../../../Gotchas/Research/Readers/ConstrainedBoss/UnboundBodyDisplayLabel.md).

## Verification

The source intent and candidate process tests passed together in 74.68 seconds on Windows Python 3.14.6. After the candidate child script was separated into setup, audit and replay stages, the candidate process test passed again in 56.60 seconds. It captured the exact source, prepared the logical input, and built request SHA-256 `d460d8352b7e34526a5e95d451d5671454d8b30d8ef96e5adf90111d67812a49`. After removal of the test-owned source and logical JSON, two fresh processes produced candidate SHA-256 `a0e524cc73b844042c7da6bf86b3a12120fb4f73aaf34de7f0d6cc481ebda15f`. The existing archive verifier checked 32 streams, the 40 × 20 × 10 mm part, a centroid of (20, 10, 5) mm and a volume of 8,000 mm³. Its generated feature and dimension identifiers were independent of the source. Wrong retained request digest and existing request destinations were refused without changing their bytes. No native application ran.

The strengthened process check passed in 63.06 seconds. Its file read audit starts before the project imports and constructor setup. The only recorded data reads were the pinned request and the packaged layout schema. A separate fresh child rejected an unexpected binary input before project imports. The request check compared all seven persisted relations with the strict source, including ordered operands, dimension ownership and native record spans. Removing the Origin relation or reversing the height operands failed that comparison. Both fresh generations retained the same candidate SHA-256.
