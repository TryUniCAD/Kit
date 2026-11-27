# Agent guidance

## CAD success criteria and reverse engineering

Agents MUST read the [CAD success criteria](Documentation/Reference/Operations/CadSuccessCriteria.md)
before any CAD parsing, writing, conversion, verification, or reverse-engineering task, and before
claiming that any CAD output works. Abide by every criterion at once: no donor data, no CAD runtime,
lossless, fully parametric, vendor loadable, application usable, measured acceptance against
controls, honest attestation, complete implementation, generalization to held-out inputs, and
traceable knowledge. A result that misses one criterion is unfinished work, not an outcome. The
criteria page collects the authoritative standards and never relaxes them.

Any agent tasked with reverse engineering a file format, decoding or writing a native CAD stream, or
analyzing a CAD application's binaries MUST read the
[reverse-engineering instruction book](re/Playbook/README.md) in full before starting, then the
chapter for its phase, and follow it. The book requires mapping the file's structure and its
parametric and derived data, reverse engineering the vendor loader modules for their data model and
key boundaries with the REA MCP server or the `npx rea-agents` CLI, generating a ground-truth corpus
of extreme models through the vendor API, correlating that corpus to locate every field, and only
then building the writer. Put both documents in every sub-agent brief for CAD work.

For decoding challenges, agents MUST use the research automation pipeline for supported capture, deterministic comparison, inference and evidence tracking. Investigate unresolved findings and implement decoder rules from the recorded evidence. Validate changes through deterministic checks; a detected pattern alone is not a proven rule. Report missing automation capabilities explicitly

## Planning and scope claims

Before selecting, claiming, dispatching or handing off work, read
[the planning procedure](Documentation/Planning/README.md), its generated task,
feature and delivery indexes, the owning register and the live organization project
recorded in `Documentation/Planning/Project.json` when available.
Check current ownership, prerequisites, scheduled window, delivery PR and exclusive
native resource. An unverified or unmapped catalogue scope is not automatically free.
Do not duplicate an existing owner or infer readiness from a scheduled forecast.

Keep the owning register and project scope synchronized in the same task whenever
scope, owner, branch, blocker, schedule, dependency, PR or acceptance evidence changes.
Use stable scope/task IDs and record exact tested revisions and evidence separately
for capture, decode, semantic qualification, writing and native acceptance.
Preserve unfinished requirements, cancelled work and superseded delivery history.
Update explicit catalogue/task links and engineering windows in
`Documentation/Planning/Links.json`, refresh the forge snapshot when selecting work,
and regenerate the views with `uv run --locked python re/automation/Planning/Build.py`.
Verify freshness with the same command plus `--check`; never edit generated views.
Every new feature or decoding scope must be represented in the owning register or
catalogue and linked into planning before implementation. Include product, CLI,
UI/UX, documentation, infrastructure and release work; label proposals explicitly.
Project assignment records ownership; it does not launch an agent. Dispatch only
through a configured supported runtime after live claim and dependency checks.
If project access is unavailable, update the repo records and report the pending sync.

## Documentation and gotchas

Read the [completion roadmap](Roadmap.md) and [conversion backlog](Documentation/Maintenance/ConversionBacklog.md)
before claiming conversion, format, documentation, CLI or release work.
Refresh the linked PRs and owning registers before treating a task as available.
Distinguish active implementation, planned programme scope, blocked work and unassigned tasks.
Preserve PR #94's explicit programme delivery rule and coordinate existing separate PRs.
Do not infer that a broad future plan implements every individual gap.

Record the task ID, owner, scope, dependencies, delivery PR and exit condition when claiming work.
Update its owning register when the scope, blocker, PR state or completion evidence changes.
Update the backlog links and production snapshot when those changes affect this roadmap.
Update Roadmap.md when a milestone or supported production boundary changes.
Completion requires revision-bound acceptance evidence, not an open PR, decoded-byte count or green PR checks.
Retain unfinished requirements and link the evidence for completed work.

Every new feature, API, adapter, command, configuration option, workflow, tool,
or other repository addition MUST include a new PascalCase Markdown entry in
`Documentation/Changes/` in the same PR. Describe behavior, usage or configuration,
limitations, and actual verification evidence. Update the relevant guide and
link the entry directly in the PR. The [change directory](Documentation/Changes/Index.md)
explains how to find entries without a manual index update. An existing reference-page update
does not replace the required new entry. Pure documentation corrections may
update their existing entry.

Find and read the relevant pages in the [gotchas directory](Documentation/Gotchas/README.md)
before working in an affected area. If you discover a new gotcha, unexpected API
behavior, wrong assumption, or undocumented quirk, you MUST record it before
finishing. Add a separate, specific PascalCase Markdown file in the appropriate
topic under `Documentation/Gotchas/` and link it in the PR. Describe the expectation,
actual behavior, and workaround. Link evidence when available. Do not append
entries to the directory's README.

Maintained documentation lives in `Documentation/`. Follow
[the publishing guide](Documentation/Publishing.md) for generated imports and GitHub wiki
updates; generated docs must be reviewed and must not overwrite manual entries.

## Repository workflow

Agents MUST activate [standard-pr-practice](.agents/skills/standard-pr-practice/SKILL.md)
every time they work on this repository, before any task, including investigation,
documentation, skill edits, implementation, and PR follow-up. It is the only repository skill and the
canonical source for Codex and Claude Code. Edit it directly. Do not restore
the removed Kiro skill registrations, steering directories, or skill generator.
All prior rules and resources are preserved in full inside standard-pr-practice;
read its complete standards index and every applicable rule before coding.

- Use an isolated worktree and a separate normal PR for each task. Preserve
  user-owned changes and never write directly to `main`.
- Push with `--no-verify`. Follow the skill's local execution rules. Large PRs
  have standing authorization for relevant local tests permitted by repository policy.
- For [large PRs](.agents/skills/standard-pr-practice/SKILL.md#large-pull-requests),
  use parallel agents for independent work, with one owner per shared vendor
  oracle. Retain needed evidence and close completed task-owned Hopper sessions.
  Begin configured review once the requested work and its pre-review verification
  are complete.
- Unit tests are prohibited, including policy, security, and tooling unit
  tests. Validate through integration, end-to-end, smoke, compatibility, and
  repository policy checks at real component or process boundaries.
- Run heavy acceptance and security checks on the merge-group candidate through
  [the native merge queue](MergeQueue.md). Keep every applicable CI gate enabled.
  Distinguish green PR checks from successful queue acceptance.
- Add specialised end-to-end and compatibility tests to the complete test suite.
  Run them through the existing merge-queue planner, shards, and report.
  Share its runners and workflow, including Fusion and CLI compatibility coverage.
  New specialised tests must use this same execution path.
- Use `Pull Request / CI Agg` for overall CI health. Register every applicable
  PR and merge-queue CI job in the [CI allowlist](.github/scripts/CiAllowlist.cjs).
  Keep automated review out of the allowlist and its workflows. Run Pyright,
  Mypy and Python steering in both phases. Assign other validations to one phase using its complete observed job duration. Jobs below
  45 seconds, including light change-range checks, run on PRs. Jobs at or above
  45 seconds run on merge-group candidates. Security scans and test planning
  run on the candidate. Preserve the former job set during trusted-base rollout
  until the phase-version marker reaches the base revision. A test module reuses
  a passing result only from an accepted ancestor candidate when every file and
  folder that it recorded is unchanged. Every other test executes on the candidate.
- Read every entry in `Reviewers` from
  [ReviewBot.json](.agents/skills/standard-pr-practice/ReviewBot.json), the sole
  source of reviewer identities, report names, and exact request comments.
  When review is due under the skill's timing rules, submit each entry's
  `Comment` verbatim once per accepted head unless that reviewer already has
  a request or review for that head. Verify every responding
  account/app and reviewed SHA, and address all findings. Every configured
  reviewer must pass all its native reports and submit an actual `APPROVED`
  review on the current head before the PR is ready. Missing, pending, failed,
  stale, or dismissed evidence blocks readiness. Comments and green checks do
  not substitute for approval. Keep reviewer names and identifiers only in that
  JSON. No human or code-owner approval is required by this workflow. Report
  unavailable review evidence and independently enforced requirements separately.
- `jdharcourt` and `odinglynn` are repository-policy administrators with merge
  privileges. Either may explicitly authorize agent queue enrollment, auto-merge,
  or merging under the existing readiness gates. Verify the requester’s GitHub
  identity. This designation does not grant GitHub platform permissions or bypass
  enforced protections. Other administrators require verified current GitHub
  `admin` permission.
- Only an explicit merge request from a verified repository administrator
  authorizes an agent to enroll a PR in the queue, enable auto-merge, or merge.
  Verify the requester's identity and authority under the administrator rule above.
  Implementation requests and PR creation alone do not authorize merging.
- Use Python for backend work, React for frontend work, and `uv` for Python
  dependencies outside `modules/`.
- Add the mandatory rationale comment above every Python declaration, lambda,
  and module binding. Follow the skill's rationale standard. Other explanatory
  comments and comment-oriented docstrings remain prohibited. Preserve required
  standalone licenses and third-party attribution. Use `license: MIT` in skill
  frontmatter and pin Actions and runner versions.
- Keep chat lowercase, extremely concise, without emojis or terminal full
  stops. These response rules do not constrain artifacts.

The repository-root `re/` tree remains an unrestricted research workspace,
exempt from code standards and unit-test requirements, including naming,
formatting, typing, imports, rationale comments, declaration
splitting, architecture, and directory density. This applies only to `re/` and
its descendants; code promoted into other directories follows their normal
rules. Git isolation and preservation of user-owned work still apply.

Do not stage, commit, or distribute proprietary vendor software, including
SOLIDWORKS DLLs, interop assemblies, executables, installers, SDK code, symbols,
license files, or decompiled vendor listings. This includes renamed and compressed
copies. Keep licensed software outside repository checkouts. The `re/` exemption
does not waive this restriction. CAD files, documents, independently authored
research tools, and recorded format knowledge remain permitted. Follow the
[research artifact policy](Documentation/Reference/Research/ResearchArtifacts.md).
Never force-add an ignored vendor artifact.

The research exemption does not waive product acceptance. Code or artifacts
shipped in production, and outputs claimed to be production-ready, must satisfy
no-CAD-runtime, no-donor-block, lossless-conversion, parametric feature/history,
vendor-loadability, and target-application acceptance requirements listed in the
[CAD success criteria](Documentation/Reference/Operations/CadSuccessCriteria.md). Research
experiments may remain unrestricted in `re/`; their location does not qualify
them for shipping or establish acceptance evidence.

Donor data is banned. Writers MUST make every emitted byte from
reverse-engineered format knowledge. Do not ship donor files, donor blocks,
templates, captured rows, or values captured from or fitted to one document,
in `src/`, in package data, or in writer output. A "generic" template and a
fallback to donor data are also banned. `re/` may keep vendor-saved controls
and captured tables for research, but production code MUST NOT load them.
Read the [no donor blocks standard](.agents/skills/standard-pr-practice/references/Standards/Portable/NoDonorBlocks.md)
and the [Fusion donor data ban](Documentation/Reference/Research/FusionDonorBan.md)
before writer work.

A typed field program is donor data when its values or offsets come from a vendor
save. Zero opaque bytes proves that each byte has a typed owner. It does not prove
that Kit generated the value. Kit removed the SOLIDWORKS writer that used recorded
programs. The current [bounded part writer](Documentation/Changes/Solidworks/Construction/SolidworksMeasuredPartPublication.md)
generates a part from the supported model and requires exact offline measurement evidence.
SOLIDWORKS assembly support is read-only. CI runs
`tools/Donors/CheckReplays.py` on `src` and fails on any recorded field operation or
recorded payload re-emission call. Do not restore the removed programs or add a
SOLIDWORKS writer family as a recorded program. Build the generative serializer
instead. The no donor blocks standard states the current SOLIDWORKS state and the
required direction, and this paragraph takes precedence over its preserved state
section.

An administrator's explicit merge request remains valid through repairs and
authorizes a supported admin override when independently enforced protections
otherwise block a fully green, conflict-free PR. It never authorizes bypassing
pending or failed queue acceptance, changing protection settings, or bypassing
enforced tool approvals. Follow the skill's administrator-requested merge rules.

## Deterministic decoding through the CLI

Install this CLI checkout with `uv tool install --python 3.14 .`.
Use a separate, trusted checkout containing PR #94's research tools and pinned Git objects.
Use `kit research` or `python -m KitCli research` for this developer workflow.
`python -m convert` supports SDK formats, decoding, and conversion; research execution stays outside its runtime.
The CLI is delivered in its own PR; do not add CLI implementation work to PR #94.
Use that research checkout's absolute path as `--root` and choose unused output directories.

```sh
kit research --root /path/to/KitPr94 solidworks --asset re/solidworks/examples/.SLDPRT/example.SLDPRT --output /tmp/KitPinnedPart
kit research --root /path/to/KitPr94 fusion --asset re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d --output /tmp/KitPinnedFusion
kit research --root /path/to/KitPr94 corpus check --manifest /path/to/KitPr94/re/automation/Corpus.json
```

These commands use PR #94's pinned readers and corpus verifier in a fresh process with that checkout's SDK.
They verify committed bytes and preserve the readers' document JSON, separate receipts, fingerprints, and Fusion summary.
Keep receipts with documents and inspect unresolved evidence; a completed decode does not establish portable semantics or native conversion acceptance.
Repeat `--asset` for a Fusion batch; `--allow-partial` records strict rejection before fallback.
Fusion exit `3` means published rejected/error outcomes and must not be treated as complete decoding.
Do not remove `kit.research_read_status: unqualified` metadata to force conversion.

For durable research jobs, use the existing controller and configured supervisor:

```sh
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState init --max-running 4
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState status
kit research --root /path/to/KitPr94 supervisor --config /path/to/Supervisor.json run --idle-seconds 30
```

Configure actual trusted worker programs before using the supervisor; the CLI does not supply a production decode runner or model provider.
Controller leases, retries, pool controls, and worker dispatch remain owned by PR #94's tools.
Models remain disabled by default. Model execution retains the plan's explicit authorization requirements.
The supervisor supports Linux, macOS, and compatible Windows checkouts.
Windows supervision requires Windows 10 or later, Python 3.14 or later, the locked `pywin32` development extra, and Windows shutdown protocol 1.
Fusion research requires Python 3.14.
Use `kit research --root /path/to/KitPr94 TOOL --help` for tool-specific commands.
Use `kit decode SOURCE` for working-file inspection and `kit convert SOURCE DESTINATION` for supported conversion.
Read [the deterministic CLI procedure](Documentation/Tasks/ResearchCommandLine.md) before changing these workflows.
Follow the skill's local execution rules for developer verification. Verify
applicable PR and queue checks on their respective remote revisions.
