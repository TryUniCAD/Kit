# Offline research timings

The plan on PR #296 calls for measuring deterministic work without enabling an AI advisor.
The controller and supervisor already default to no advisor. An integration test now runs
the same evidence stall with and without explicit opt-in. Only opt-in reaches the fake advisor.

## Corpus decode

Run the corpus driver on a POSIX host from a trusted checkout with complete Git history and the decoder dependencies installed:

```sh
python re/automation/OfflineCorpus/RunCorpus.py --manifest CORPUS.json --output NEW_DIRECTORY --workers 1
```

Use one worker for serial execution. The default is four workers.
In `Report.json`, native assets appear in manifest order. Each asset records elapsed
nanoseconds for its decoder subprocesses and their sum. `timings.decode_ns`
sums the asset durations, while `timings.elapsed_ns` measures batch wall time.
The sum may exceed wall time when subprocesses overlap.
`Results.jsonl` retains completion order for live progress and recovery.
Use a fresh output directory for each run.

## Generation and comparison

The encoder round-trip `manifest.json` reports elapsed nanoseconds for the source
decode and each candidate, plus combined decode and generation stage totals.
Blocked candidates contribute no generation time. Timing values do not enter
the deterministic run fingerprint.

The bulk comparison `summary.json` reports elapsed nanoseconds per pair,
their sum, and batch wall time. It does not add timing values to the hashed
per-pair reports.

## Verification

The process tests check advisor opt-in with a fake provider, consistent asset
order and artifact digests with serial and parallel decoding, and the timing
fields in bulk comparison and encoder reports. They do not establish native
or application acceptance.
