<!--
SPDX-License-Identifier: MIT
SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin, Stephen Harcourt
-->

# Known gotchas

Read this log before working in an affected area.
Each entry records an expectation, observed behavior, and corrective action.
Add a new entry when repository work reveals an undocumented condition.
Keep source links and historical evidence.

- **Fusion discovery:** A packaged reader might appear production-ready. Public discovery excludes the partial Fusion reader. Use the explicit research interface. Do not infer lossless output from a partial read. See [the import record](../Changes/FusionResearchImport.md).
- **Header remediation and CI:** An automated SPDX commit might appear to complete validation. Its new workflows can await approval while the aggregate covers an older head. Approve the exact current-head runs. If aggregation did not start, restart validation through the authorized maintainer workflow. See [the blocked run](https://github.com/TryUniCAD/Kit/actions/runs/42783888706).
- **Pyright integer inference:** An `isinstance` check might appear necessary after unpacking. Pyright 1.1.414 already infers integer values for literal `H` and `I` formats. Keep bounds checks and return an explicit integer. See [the compatibility record](../Changes/PyrightCompatibility.md).
- **Distribution and import names:** The `kit` distribution name suggests a `kit` import. The wheel packages `convert` and `interchange`. Use `from convert import convert`. See [package metadata](../../pyproject.toml).
- **README images in distributions:** A relative image can work in the repository but fail in a source distribution. The package manifest excludes `files/`. Use an absolute image URL pinned to a repository revision. See [the distribution manifest](../../pyproject.toml).
- **Strict reading and carrier policy:** `strict=True` might appear to require usable target output. It controls reader validation. Set output policy separately with `allow_carrier=False`. Inspect the attestation and vendor evidence. See [result evaluation](../Tasks/InspectResult.md).
- **Target-limit carriers:** `allow_carrier=False` might appear to reject every carrier transfer. The registry treats `target_unsupported` differently from implementation and decoding gaps. Inspect each transfer reason when applying acceptance requirements. See [the write policy](../../src/convert/adapters/base/WritePolicy.py).
- **Partial stream writes:** Staging might appear to provide rollback for every destination. The final caller-stream write can fail after writing some bytes. Use a fresh stream after a failed write. See [stream staging](../../src/convert/adapters/staging/StreamStaging.py).
- **Partial B-rep extraction:** Extraction might appear to use the conversion output transaction. It writes payloads in sequence. A later error can leave earlier files. Use a separate directory for each attempt. See [extraction](../Tasks/ExtractGeometry.md).
- **Hash meaning:** A matching digest might appear to authenticate a source. An untrusted sender can replace both the bytes and digest. Use hashes for the documented integrity comparison. Do not claim authorship from an unsigned hash. See [serialization](../Reference/Data/Serialization.md).
- **Generated page paths:** A generated export might appear ready for repository import. Numbered or lowercase project-owned stems can fail `PTH001`. Normalize the export into maintained PascalCase paths. Preserve provenance and repair links. See [publishing](../Publishing.md).
- **Wiki initialization:** Enabling the wiki might appear to create its Git remote. The remote remains unavailable until the first web page is saved. Initialize that page before cloning the wiki. See [GitHub's procedure](https://docs.github.com/en/communities/documenting-your-project-with-wikis/adding-or-editing-wiki-pages).
- **Case-only directories:** `Docs/` and `docs/` might appear distinct. A case-insensitive filesystem treats them as the same directory. Use `Documentation/` for maintained pages. Preserve the separate generated `docs/` path.
- **Queue configuration and enforcement:** A checked-in manifest might appear to establish live protection. The historical ruleset allowed PR #42 to merge despite failed heavy jobs. Verify live enforcement before enrollment. Settings changes require explicit authorization. See [the incident record](../Changes/QueueScorecard.md).
- **Skipped job names:** A conditional job name might appear resolved before reporting. GitHub reported the expression text for a skipped bootstrap. The aggregate rejected that unexpected check. Retire obsolete bootstrap triggers and use stable gate names. See [the repair](../Changes/AggregateBootstrap.md).
- **Artifact publication:** A successful upload might appear immediately readable. Later reads succeeded after immediate metadata and ZIP requests returned 404. The verification client now permits four retries while retaining digest and provenance checks. See [the recorded failures](../Changes/ArtifactPublication.md).
- **Trusted-base aggregation:** A reporter change on a PR might appear to affect that PR's aggregate. `pull_request_target` loads trusted base code. Merge the reviewed reporter change before relying on its behavior elsewhere. See [provider exclusions](../Changes/ReviewProviderExclusions.md).
- **Scorecard and queue commits:** Disabling publication might appear sufficient for the Scorecard action on `merge_group`. The action rejects that event before analysis. Use the pinned CLI and both required scan modes. Native reviewer evidence belongs to PR heads, not synthetic queue commits. See [the repair](../Changes/QueueScorecard.md).
- **Public standards summaries:** Short sentences might appear sufficient for standards conformance. Full ASD language assessment also needs dictionary usage checks. ISO conformance needs complete applicable requirements and evidence. Keep full conformance unverified when those inputs are unavailable. See [the evidence matrix](../Standards/Conformance.md).

- **Review trigger syntax:** An account mention might appear sufficient for every integration. Some require a slash command and a linked account with write access. Read each exact `Comment` and official source in [ReviewBot.json](../../.agents/skills/standard-pr-practice/ReviewBot.json). Submit it verbatim and verify the responding identity and reviewed SHA.

- **Provenance references:** An array position might appear to identify a generator permanently. Reordering exclusion entries changes that target. Use the stable `DocumentationSources.InitialWiki.Generator` key in [the configuration](../../.agents/skills/standard-pr-practice/ReviewBot.json).
