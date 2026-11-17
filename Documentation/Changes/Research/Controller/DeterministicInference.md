<!--
SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin

This SPDX license identifier and copyright notice must not be
removed, altered, or obscured. Doing so is a material breach of
the PolyForm Strict License 1.0.0 and voids all licenses granted
to you under it immediately and permanently.
-->

# Deterministic inference and affected archive rescans

The automation-only A07 implementation searches supplied aligned streams and schedules affected-file observations. It does not include a native record extractor, writer or raw native qualification verifier. The [main-SDK boundary record](MainSdkAutomationBoundaries.md) describes the current split.

## Run an assessment

Use the locked development dependency group for numeric field search. Register `inference.fields`, `inference.paired-gap` and `inference.rescan` with the supervisor, using `re/automation/InferenceRunner.py` and the whole-argument `{session}` substitution. Generate its records schema in your private state directory:

```sh
uv run --frozen --group dev --python 3.14 python re/automation/InferenceRunner.py --schema
```

Bind the actual plan and streams through the [controller](../../../Reference/Research/ResearchController.md). A field plan contains `inference_version: 1`, `scope`, `quantity`, `provenance`, `encodings`, a nonnegative `tolerance`, `confounds` and `observations`. Each observation names its ID, lineage, source SHA-256, stream, aligned span, recorded value, controls, input role and split. `provenance.inputs` binds every observation ID to its archive and stream digests. The runner checks the input roster, seals and bounded work before searching.

Discovery freezes candidate locations before challenge and holdout evaluation. Declared holdout lineages must be disjoint from discovery and challenge. Integer comparisons remain exact. Floating searches use declared encodings and tolerances. A matching candidate has partial confidence; declared lineage names and numeric agreement do not independently prove capture ancestry or native meaning. P05 stays reserved and is not a source of new discovery inputs.

## Schedule generic work

Run `InferenceSchedule.py REQUEST.json` with a request containing `inference_version`, `scope`, `family`, immutable `rule_version` and `tool_version`, `plan_input`, `stream_inputs`, `archives`, `distinguishing_evidence` and `depends_on`. The archive map identifies each source SHA-256, its binding and explicit format. Current rescans use the existing main readers for `fusion.f3d` and `solidworks.sldprt`.

Submit the generated jobs through the existing controller `schedule` command. Batch requests use a `requests` array. Supplied generic grid jobs retain their explicit class and installation resources; scheduling a job does not supply a missing native worker or verifier. Requested distinguishing work and ordinary queued work retain the controller's existing priority and resource rules.

A rescan depends on its accepted assessment result, verifies its pinned source and format, and records public reader output identity plus unresolved observations. It does not install inferred fields in a production reader. Changed inputs, rules or tool versions invalidate declared dependent jobs; unchanged fingerprints retain their original receipts.

Generic paired-gap reports contain a scope, affected source-format map and an assessment of `refuted`, `corroborated` or `needs-distinguishing-evidence`. Unresolved gaps require a distinguishing request and remain `waiting_evidence`. A completed generic observation is not native proof. Every new runner result retains `semantic_qualification: unverified`, `native_acceptance: not_established` and `portable_complete: false`.

## Excluded native proof profiles

The runner and scheduler refuse these reserved profiles:

- `p03-blind-boss.fusion`
- `p03-blind-boss.solidworks`
- `p04-cut-termination`
- `p04-through-all-body-selection`

Generic gap input cannot carry `native_grid`, `continued_from_receipt` or `grid_from_receipt` as a substitute for the original proof. Fixed `InferenceArchives`, `InferenceArchiveGate` and `InferenceGrid` commands remain in the preserved decoder/proof follow-up. There is no current provision/resume command for those native studies in this PR.

## Historical evidence and verification

The original [A07 entry at `fb723e0a920b4d03ad2d5635882860b800a9b61c`](https://github.com/Stephen316/Kit/blob/fb723e0a920b4d03ad2d5635882860b800a9b61c/Documentation/Changes/Research/Controller/DeterministicInference.md) retains all fixed native archive commands, measurements and source-bound results. The hosted archive/scheduler observation at `ebe6130c` and private replay at `8425b5fbc9bbda0b19c9efbd8dc566d2ea6cc0c4` do not become verification of the automation-only candidate.

Preserve the original private replay report `66a1e22b04c02f004ef662b86d0506959c17efbd85ccca57bafaa1e77e5d1744` and parked receipt `06414a895e34601d8866dd0cccff87d82da1cbffd90b4829b0a2cdbd9d293fd2`. The missing licensed Fusion output and independently established saved target policy remain open dependencies. Those receipts must not be relabeled or released by generic JSON input.

Current process coverage includes authored binary streams and independent refutation, generic gap states, main-SDK rescan pins and reserved-profile refusal. Local verification is static only. Actual hosted execution, source admission and native acceptance remain distinct. See the [step register](../../../Reference/Research/AutomationSteps.md).
