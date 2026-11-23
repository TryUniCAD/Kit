# Automatic decoder advice

Start the existing supervisor with a signed-in Codex account on macOS or Linux.

```sh
kit research --root /path/to/Kit supervisor --config Supervisor.json run --codex-on-stall
```

The built-in A03 controller settles the deterministic result first. During this run, a paired gap parked for missing evidence, or a field search that ends ambiguous, unresolved, refuted or without distinguishing controls, triggers one GPT-6.2-Sol request at medium effort. Successful field matches, resolved gaps, retries and process timeouts do not trigger advice. Offline runs omit the flag. Each run reserves at most 16 calls by default. Set an explicit budget with `--codex-on-stall MAX_CALLS` (1–256).

The supervisor sends a fixed question and a description selected from known stall reasons. For the known through-all cut it also identifies the body-selection question. The prompt excludes archive bytes, filenames, operator text and holdout measurements. A background worker checks the accepted receipt before and after the call. It writes the outcome and any proposed experiment under `decoder-advice/<receipt>/Advice.json` in the supervisor state directory. Keep that directory private and outside the controller store. Existing receipt claims prevent duplicate calls. The integrated path uses a single 90-second attempt and does not retry at higher effort.

Provider failure leaves the deterministic result available. A suggestion still needs a controlled experiment before it can become a rule. This mode reacts to results settled during the run. For a previously parked pair use the [standalone helper](CodexFallback.md).

## Verification

The installed Codex model catalog lists `gpt-6.2-sol` with medium reasoning. The process cases exercise a parked paired gap, a refuted field search and a successful field match. A disposable provider records each invocation independently. The developer research launcher requires an explicit trusted checkout. The production SDK has no advice entry point. Stephen’s [61 passing process cases](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6985183316) predate this integration. The earlier [live synthetic call](CodexFallback.md) exercised the separate helper. Neither establishes a live account result for this change.

## Share provider work between instances

Opt into shared advice with an explicit provider and one owner-private local directory:

```sh
kit research --root /path/to/Kit supervisor --config /private/var/tmp/Supervisor.json run --advisor codex --auth login --model gpt-6.2-sol --advice-state /private/var/tmp/KitAdvice --advice-global-calls 16 --advice-parallel 1
```

The same advisor flags work on file and catalogue research runs.
`--auth api` uses the existing provider API credential configuration.
Shared state does not enable advice by itself. The legacy `--codex-on-stall` flag alone does not select shared state.
The directory requires POSIX owner-private permissions and must remain on a local filesystem.

The first use fixes the provider's cumulative call allowance and concurrency limit.
Later instances must use the same limits; a new process or resumed run does not reset them.
The allowance counts provider invocations, including unsuccessful and uncertain attempts. It is not a token or currency budget.
The normal per-run call ceiling still applies.

Identical public prompts, explicit provider/model/auth settings, effort, allowed experiments and prior-attempt status share one queued reservation.
Successful validated proposals can be reused after the caller rechecks its own source evidence.
Raw CAD bytes, credentials and holdout measurements do not enter the shared key or database.
Different evidence remains independently verified; a cached model proposal is never a verified format rule.
Queued callers wait for a bounded interval. Expired waiters cannot retain the front of the provider queue.

A timeout or caller interruption can leave the remote request's completion uncertain.
That reservation stays charged and occupies capacity until the owner confirms the provider process has stopped.
It is not resent automatically, and elapsed time alone does not clear it.
Inspect and recover the exact reservation through the local operator tool:

```sh
python3 re/automation/CodexAdvice/SharedAdvice.py --state /private/var/tmp/KitAdvice --provider codex status
python3 re/automation/CodexAdvice/SharedAdvice.py --state /private/var/tmp/KitAdvice --provider codex recover --request-key REQUEST_SHA256 --provider-stopped
```

Replace `REQUEST_SHA256` with the observed reservation key only after confirming that its provider process stopped.
Recovery releases capacity but does not refund the consumed call or resend that request.
Use a separately chosen state directory for a genuinely new allowance; do not delete active coordination state to bypass its limits.

See [shared research scheduling](../Supervisor/Coordination/SharedResearchScheduling.md) for the job queue and its process verification scope.
