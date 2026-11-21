# Inspect actual native CAD feature decodes

Manual source audits accept `feature_session=true` to run the existing native readers on all 714 pinned Fusion files and 58 SOLIDWORKS parts.
The source revision is immutable and separate from the reporting harness revision.
The job hydrates the sealed corpus history before reading the manifest's pinned native blobs.

```sh
gh workflow run MergeQueue.yml --ref WORKFLOW_BRANCH -f audit_sha=FULL_SOURCE_SHA -f feature_session=true
```

The `CadFeatureSession` artifact preserves decoded `document.json` files, their source-bound receipts, and `FeatureInventory.json`.
The inventory lists each recovered feature step, its definition type and recorded step status, and per-file sketch, parameter, body, and unresolved counts.
Native-only definitions and missing definitions remain explicit; they are not equivalent to interpreted parametric features.
In particular, a typed feature-step container does not qualify a nested `NativeFeatureDefinition`.
Rejected inputs remain listed, and unexpected reader errors fail the session.

This is a research observation, not lossless conversion or vendor acceptance.
The session cannot establish missing source semantics or independently qualify a recovered feature.
Existing acceptance, security, PR, and native queue gates remain enabled.
The optional session is skipped on PR and merge-group events.

Local verification is limited to formatting, whitespace, and repository policy.
Actual feature decoding runs remotely; its source SHA, run URL, and measured outcomes are recorded in the PR after execution.
The initial remote invocation stopped before decoding because the source checkout lacked the sealed manifest revision; adding the existing `CaptureHistory.py fetch` boundary repairs that setup requirement.

## Measured feature session

The [feature session](https://github.com/TryUniCAD/Kit/actions/runs/44912719271/job/136871743821) passed on source `72207ec5684d89bf98023427ce4f49eac3a5d122`, using reporting harness `a3843631111b306da76356aa017324f614219525`.
The [preserved artifact](https://github.com/TryUniCAD/Kit/actions/runs/44912719271/artifacts/14710418434) contains actual neutral documents, receipts, and `FeatureInventory.json`.
The session read 772 pinned inputs and produced 755 decoded documents; 17 Fusion inputs were explicitly rejected.

| Format            | Inputs | Strict reader | Partial reader | Rejected | Structured definitions | Sketches | Parameters |
| ----------------- | ------ | ------------- | -------------- | -------- | ---------------------- | -------- | ---------- |
| Fusion F3D/F3Z    | 714    | 16            | 681            | 17       | 617                    | 973      | 2,487      |
| SOLIDWORKS SLDPRT | 58     | 58            | 0              | 0        | 602                    | 748      | 2,482      |

The 1,219 structured definitions comprise 855 extrusion definitions, 50 revolve definitions, 87 fillets, 56 chamfers, 5 shells, 6 scales, and 160 reference/construction planes.
They remain semantically unverified observations, not independently qualified portable features.
The full root timelines contain 5,459 steps: 1,219 structured definitions, 2,481 native-only definitions, 751 recognized sketch references, and 1,008 incompletely interpreted steps without definitions.
Native-only counts include non-modeling tree records, so timeline totals must not be reported as the number of fully decoded modeling features.

For example, the ordinary Fusion rectangle control yielded one sketch, two parameters, and a `DistanceExtrude` definition.
`RUEDA DE TURBINA.SLDPRT` yielded 12 extrusion, 3 revolution, 2 chamfer, and 1 reference-plane definitions, alongside 18 sketches, 69 parameters, and 48 native-only definitions.
Every receipt still reports `portable_complete=false`, `semantic_qualification=unverified`, and `native_acceptance=not_established`.
