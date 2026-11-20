# Automatic decoder advice

Start the existing supervisor with a signed-in Codex account on macOS or Linux.

```sh
kit research --root /path/to/Kit supervisor --config Supervisor.json run --codex-on-stall
```

The built-in A03 controller settles the deterministic result first. During this run, a paired gap parked for missing evidence, or a field search that ends ambiguous, unresolved, refuted or without distinguishing controls, triggers one GPT-6.2-Sol request at medium effort. Successful field matches, resolved gaps, retries and process timeouts do not trigger advice. Offline runs omit the flag. Each run reserves at most 16 calls by default. Set an explicit budget with `--codex-on-stall MAX_CALLS` (1–256).

The supervisor sends a fixed question and a description selected from known stall reasons. For the known through-all cut it also identifies the body-selection question. The prompt excludes archive bytes, filenames, operator text and holdout measurements. A background worker checks the accepted receipt before and after the call. It writes the outcome and any proposed experiment under `decoder-advice/<receipt>/Advice.json` in the supervisor state directory. Keep that directory private and outside the controller store. Existing receipt claims prevent duplicate calls. The integrated path uses a single 90-second attempt and does not retry at higher effort.

Provider failure leaves the deterministic result available. A suggestion still needs a controlled experiment before it can become a rule. This mode reacts to results settled during the run. For a previously parked pair use the [standalone helper](CodexFallback.md).

## Verification

The installed Codex model catalog lists `gpt-6.2-sol` with medium reasoning. The supervisor process case exercises the provider command boundary with a disposable CLI. Stephen’s [61 passing process cases](https://github.com/TryUniCAD/Kit/pull/158#issuecomment-6985183316) predate this integration. The earlier [live synthetic call](CodexFallback.md) exercised the separate helper. Neither establishes a live account result for this change.
