# Run deterministic research with Kit

## Purpose

Run PR #94's pinned readers, corpus, durable controller, and configured supervisor through the installed `kit` command.
The CLI delegates to existing implementations and preserves their evidence contracts.
Users do not write Python imports or scripts.

## Before you start

Install a CLI revision from its source checkout with `uv tool install .`.
Use `uv tool install --python 3.14 .` when Fusion research is required.
The launcher uses the interpreter running `kit` and does not silently select another environment.
The equivalent module command is `python -m KitCli research`.
`python -m convert research` reports an error directing callers to these developer entry points.

Select a trusted checkout containing PR #94 and the corpus's pinned Git objects.
`--root` authorizes execution of that checkout's research code and SDK.
The wheel contains the SDK and CLI, not research fixtures or the `re/` workspace.
The supervisor requires Linux or macOS.
On Windows, reader, corpus, and controller commands wait for completion and return the tool's exit status.

The examples use `/path/to/KitPr94` for the trusted research checkout.
Replace it with its absolute path; the installed CLI checkout can be different.
Replace example output paths with unused directories that you own.
Preserve the original CAD files.

## Decode committed inputs

Decode a pinned SOLIDWORKS part:

```sh
kit research --root /path/to/KitPr94 solidworks --asset re/solidworks/examples/.SLDPRT/example.SLDPRT --output /tmp/KitPinnedPart
```

Inspect `receipt.json` before using `document.json`.
Retain both files for subsequent research.
The reader selects committed Git bytes and verifies path, blob, size, SHA-256, and prefix.
The document remains unchanged SDK `CadDocument` serialization.
Research documents carry `kit.research_read_status: unqualified` in their existing metadata field.
The CLI refuses conversion of those marked documents, including marked nested components, before staging output.
Keep the marker and receipt; the CLI does not promote research results into qualified conversion inputs.
The separate receipt binds source, SDK, tools, options, hashes, and unresolved evidence.

For Fusion, use Python 3.14 and select one or more committed assets:

```sh
kit research --root /path/to/KitPr94 fusion --asset re/Fusion/Study/thinextrudes-c1632bcb5efe/ordinary_rectangle_control.f3d --output /tmp/KitPinnedFusion
```

Repeat `--asset` for up to 1000 distinct inputs.
Fusion publishes `summary.json` and separate document/receipt directories for decoded assets.
Exit status `3` means a published run contains rejected or reader-error outcomes.
Inspect every outcome before interpreting the batch.

Use `--manifest PATH` for another supported manifest.
SOLIDWORKS also accepts `--configuration NAME`.
Fusion `--allow-partial` means strict-first decoding with explicit fallback, unlike inspection's forced `--partial` reader mode.
Set `--root` once before the tool name; forwarded root overrides and their abbreviations are rejected.
Use `kit research --root /path/to/KitPr94 fusion --help` for the authoritative reader help.

Expected result: the existing reader publishes its normal artifacts or reports its existing failure.
Successful receipts do not establish portable completeness or native conversion acceptance.

## Manage durable research jobs

The corpus and controller retain their existing commands:

```sh
kit research --root /path/to/KitPr94 corpus check --manifest /path/to/KitPr94/re/automation/Corpus.json
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState init --max-running 4
kit research --root /path/to/KitPr94 controller --store /tmp/KitResearchState status
```

Use `controller --help` for evidence binding, batch submission, claims, lease renewal, and result submission.
The CLI preserves stale-lease status `3` and the controller's integrity checks.

## Run configured sessions

Prepare an actual runner registry and `Supervisor.json` with the [supervisor guide](../Reference/Research/ResearchSupervisor.md).
Use only trusted configuration and runner programs.

```sh
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json submit Batch.json
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json run --idle-seconds 30
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json status
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json pause decode --reason "operator hold"
kit research --root /path/to/KitPr94 supervisor --config Supervisor.json resume decode
```

The supervisor owns pools, claims, leases, retries, restart fencing, and configured worker dispatch.
On Linux and macOS the CLI starts a separate research session and owns signal handling before spawning it.
Interrupt, termination, hangup, quit, and user signals are forwarded; terminal suspension stops both launcher and child, and continuation resumes the child.
Startup signals wait for the child reference, and continuation cancels a queued suspension.
It waits for cleanup, preserves output and exit statuses, and terminates with the child's signal when that child is killed.
An uncatchable launcher kill cannot be forwarded; use the existing research lease and recovery controls after forced termination.
Supervisor contention retains status `4`.

No production decode runner or model-provider registry is supplied by this bridge.
Models remain disabled by default.
To request GPT-6.2-Sol advice automatically on inference stalls, add `--codex-on-stall` to the supervisor's `run` command. See [automatic decoder advice](../Changes/Research/Advice/AutomaticDecoderAdvice.md).

The separate [Codex advice command](../Changes/Research/Advice/CodexFallback.md) can watch an approved parked inference job.
It uses the local Codex login and writes proposals for independent verification.
Application workers remain separate isolated research oracles.
See [session output lifetime](../Gotchas/Research/SupervisorSessionOutputLifetime.md) before implementing a persistent decode runner.

## Run a CAD catalogue with optional advice

Use a clean checkout with the catalogue runner and install Kit from that revision with
`uv tool install --python 3.14 .`. Obtain [Fusion Catalog.sqlite](https://github.com/TryUniCAD/Kit/pull/163)
or [SOLIDWORKS FeaturePlan.json](https://github.com/TryUniCAD/Kit/pull/164).
Choose an unused output directory outside the checkout.

```sh
kit run --root . fusion --catalogue /path/to/Catalog.sqlite --directory /tmp/KitFusionRun --advisor codex
kit run --root . solidworks --catalogue /path/to/FeaturePlan.json --directory /tmp/KitSolidworksRun --advisor codex
```

| Options                                       | What runs                                                                        |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| `--advisor codex --auth login`                | Installed Codex CLI with saved sign-in. Run `codex login` first if needed.       |
| `--advisor claude --auth login`               | Installed Claude Code CLI with saved sign-in. Sign in through Claude Code first. |
| `--advisor codex --auth api`                  | Installed Codex CLI with `CODEX_API_KEY` or `OPENAI_API_KEY`.                    |
| `--advisor claude --auth api`                 | Installed Claude Code CLI with `ANTHROPIC_API_KEY`.                              |
| `--advisor ollama --auth local --model MODEL` | Ollama at `127.0.0.1:11434` with an installed local model.                       |

Cloud providers default to login mode. The installed CLI selects the model unless you supply `--model`.
For Ollama, start the server with `OLLAMA_NO_CLOUD=1` and supply an installed model tag.
Omit `--advisor` to run deterministic research alone. Advice requires macOS or Linux.
Use `--advice-calls N` to set the limit for the batch. The default is four calls.

Kit reserves 4096 MiB of available memory for the system during the offline stage by default.
Use `--reserved-memory-mib 1024` to reserve 1 GiB, or `--reserved-memory-mib 0` for zero reserve.
An explicit value applies to every supervisor stage started by this batch.
Kit still requires enough available memory for each worker's estimated demand.

Kit automatically runs independent offline jobs in parallel when memory and CPU are available.
Small compatible rescans can share one worker process in groups of up to four files.
Each file retains its own result and receipt.
Use `--workers N` to cap the number of offline workers.
Set `--workers 1` for a serial offline run. Native CAD workers follow their own supervisor configuration.

With a configured native worker, a reviewed capture can start while independent offline jobs run.
The capture still needs its prerequisite assessment and a licensed application session.
Once the application owner has prepared its worker, use `--native-ready` to allow dispatch.
See the [catalogue native handoff](../Changes/Research/Controller/DeterministicInference.md#run-both-complete-catalogue-inventories).

Kit shows active workers, queued jobs, and waits in the terminal while it runs.
Progress uses standard error. The final JSON remains on standard output.
Read `CatalogueResult.json` for completed and blocked entries. Exit status 2 means coverage remains incomplete.
Read `State/decoder-advice/<receipt>/Advice.json` for suggestions produced during the offline batch stage.
A suggestion requires an independently checked experiment before it can become a decoder rule.
Use `kit run --root . fusion --help` for all options.

To pause a run, open another terminal and use its existing output directory.
Let the active workers finish before you resume.

```sh
kit run --root . fusion --directory /tmp/KitFusion --pause
kit run --root . fusion --directory /tmp/KitFusion --resume
```

Resume from the same source revision. Kit reuses the original catalogue and worker settings.
To retry a parked native job after its owner restores the application, add `--native-ready` to `--resume`.

## Keep the interfaces distinct

| Command                                       | Contract                                                   |
| --------------------------------------------- | ---------------------------------------------------------- |
| `kit convert SOURCE DESTINATION`              | User conversion through the SDK and its output policy      |
| `kit decode SOURCE`                           | Working-file inspection with a `kit.decode` report         |
| `kit research --root CHECKOUT solidworks ...` | Pinned input, unchanged neutral document, separate receipt |
| `kit research --root CHECKOUT fusion ...`     | Pinned batch, per-asset receipts, run summary              |
| `kit research --root CHECKOUT supervisor ...` | Existing configured runner sessions and controller state   |

The research checkout can differ from the installed CLI checkout.
The selected script starts in a fresh interpreter and explicitly loads its own SDK source.
The CLI forwards reader output and exit codes without reconstructing fingerprints or receipts.
It executes no shell and imports no research modules into production conversion.
The packaged `KitCli` developer composition lives in `Cli/`, separately from the two SDK packages in `src/`.
Conversion and inspection do not import its process launcher dependencies.

## If the command fails

| Symptom                           | Action and stop condition                                          |
| --------------------------------- | ------------------------------------------------------------------ |
| Missing research script           | Select the intended trusted PR #94 checkout                        |
| Missing pinned Git object         | Fetch the manifest's committed revision before retrying            |
| Hash or prefix mismatch           | Restore or review the intended pin; do not relax checks            |
| Existing output directory         | Choose an unused path; no overwrite bypass is exposed              |
| Fusion requires Python 3.14       | Install or run the CLI with that interpreter                       |
| Supervisor unavailable on Windows | Use Linux or macOS for orchestration                               |
| Runner unavailable                | Configure an implemented runner or retain the blocked prerequisite |

Tests execute only in remote CI.
The Linux and Windows [compatibility jobs](../Changes/Commands/ResearchCandidateCompatibility.md) install the CLI from the workflow candidate and select a separate research checkout at the same revision.
See [the change record](../Changes/Research/DeterministicResearchCli.md) for compatibility coverage and limits.

## Related information

- [General CLI](CommandLine.md)
- [Research plan](../Reference/Research/AutomationPlan.md)
- [Step register](../Reference/Research/AutomationSteps.md)
- [SOLIDWORKS reader](../Reference/Research/SolidworksResearchReader.md)
- [Fusion reader](../Reference/Research/FusionResearchReader.md)

## Export a qualified codec change

Supply a reviewed format rule, a completed scope and at least two tracked files with independently measured semantic values. Pin the checkout to the request's full Git revision. Use a trusted local Docker image with Python 3.14 and any dependencies the selected adapter requires. Pass its immutable image ID (from `docker image inspect --format '{{.Id}}' IMAGE`).

```sh
kit run --root . fusion --catalogue Catalog.sqlite --directory Run \
  --codec-request request.json --codec-image "$IMAGE_ID" --codec-output reader.patch
```

To use a settled run, take the assessment job ID and receipt digest from the scope's jobs in `Run/CatalogueResult.json`.

```sh
kit research --root . codec-patch --store Run/Store --job "$JOB" --receipt "$RECEIPT" \
  --request request.json --image "$IMAGE_ID" --output reader.patch
git apply --check --index reader.patch
git apply --index reader.patch
```

A request contains these fields.

| Field | Required value |
| --- | --- |
| `name`, `base`, `scope` | PascalCase patch name of 4–19 letters, full Git commit and exact scheduled scope |
| `reference`, `rule` | Tracked research Markdown path under `re/` and a written interpretation of the corroborated finding |
| `modules` | Explicit Python source paths under `src/convert/adapters/` or `src/convert/Formats/` |
| `contract.mode`, `contract.target_suffix` | `reader` with an empty suffix, or `writer` with the output extension |
| `contract.cases` | Two to sixteen objects with tracked `file`, its `sha256`, and an `expect` mapping from decoded document JSON pointers to independently measured scalar values |

For example, an expected value for the first circle sketch entity can be expressed as `{"/document/sketches/$tuple/0/entities/$tuple/0/geometry/$type":"CircleGeometry"}`. Each case must also check a feature-history value and a parameter value. Select measurements specific to the proposed change. The exporter runs the repository recorded-payload scanner before qualifying a candidate.

When the baseline fails a measurement, Codex receives the selected modules, the reviewed rule and the finding. The default is GPT-6.2-Sol at medium reasoning effort. Keep proprietary contents out of the written rule. Supply `--candidate replacements.json` (or `--codec-candidate` during a catalogue run) to qualify a mapping from each selected path to its complete proposed source without a model call.

Qualification runs each case through the public CLI in a network-isolated container. Writer cases reopen the generated file with the reader from the pinned base. The resulting Git patch includes codec changes, a replayable regression, the pinned cases and a change entry. Review the patch for generalization and donor data. Native application reopen, editing and losslessness still require the format's acceptance controls.
