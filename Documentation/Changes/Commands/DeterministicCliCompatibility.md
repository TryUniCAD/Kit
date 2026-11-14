# Deterministic CLI compatibility with an external research checkout

## Behavior and scope

The CLI compatibility suite lives in `tests/CliResearch/`. It exercises the
installed CLI against a separate PR94 checkout rather than including PR94's
research implementation or SDK changes in the CLI branch.

Set the test-only `KIT_RESEARCH_CHECKOUT` environment variable to the absolute
path of the immutable research checkout provisioned by CI. Missing or relative
paths fail the suite; no fallback checkout or skipped compatibility result is
accepted. The installed CLI executes as `python -I -m convert` from a temporary
working directory. Direct reference readers execute by absolute path from the
selected checkout. Neither the suite nor its parent process imports that
checkout's SDK or changes `PYTHONPATH` to select it. The research scripts select
their own SDK in their fresh process, as required by their existing contract.

Remote invocation after installation and the pinned checkout step:

```sh
KIT_RESEARCH_CHECKOUT=/absolute/pinned/research/checkout uv run --no-sync --python 3.14 python -m pytest tests/CliResearch -q
```

The same checkout environment must be available to complete-suite CI jobs that
execute these cases. The pin and CI configuration belong to the CLI PR; the
tests verify receipt identity against that checkout's actual Git revision and
SDK source digest.

## Process coverage and limits

SOLIDWORKS and Fusion cases compare all generated artifact bytes with direct
reader runs, including receipts, summaries, unqualified research metadata, SDK
identity, and neutral-document hashes. They exercise existing-output refusal,
all four corpus pin fields, batch preflight refusal, strict Fusion status 3,
root-option forwarding guards, parser status 2, and controller help.

A durable controller case binds an input, submits and claims a job, changes the
bound input, and verifies stale-lease status 3 and requeueing. The supervisor
case configures an absolute fixture worker from the research checkout, observes
actual dispatch, rejects a second supervisor with status 4, pauses and stops the
active session, resumes its pool, and verifies successful result publication.
The fixture is a test process; this suite neither invokes external models or CAD
applications nor claims a production decoding agent or native acceptance result.

## Verification

No local tests, reader runs, or test collection were executed. Pinned formatting,
type analysis, repository steering, path policy, and diff checks cover these
files. Actual subprocess execution must pass in remote CI on the accepted CLI
head with the explicitly pinned research checkout. Target-application acceptance
remains a separate requirement.
