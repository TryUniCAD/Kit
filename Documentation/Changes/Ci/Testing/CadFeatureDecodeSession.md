# Inspect actual native CAD feature decodes

Manual source audits accept `feature_session=true` to run the existing native readers on all 714 pinned Fusion files and 58 SOLIDWORKS parts.
The source revision is immutable and separate from the reporting harness revision.

```sh
gh workflow run MergeQueue.yml --ref WORKFLOW_BRANCH -f audit_sha=FULL_SOURCE_SHA -f feature_session=true
```

The `CadFeatureSession` artifact preserves decoded `document.json` files, their source-bound receipts, and `FeatureInventory.json`.
The inventory lists each recovered feature step, its definition type and interpretation status, and per-file sketch, parameter, body, and unresolved counts.
Native-only definitions and missing definitions remain explicit; they are not equivalent to interpreted parametric features.
Rejected inputs remain listed, and unexpected reader errors fail the session.

This is a research observation, not lossless conversion or vendor acceptance.
The session cannot establish missing source semantics or independently qualify a recovered feature.
Existing acceptance, security, PR, and native queue gates remain enabled.
The optional session is skipped on PR and merge-group events.

Local verification is limited to formatting, whitespace, and repository policy.
Actual feature decoding runs remotely; its source SHA, run URL, and measured outcomes are recorded in the PR after execution.
