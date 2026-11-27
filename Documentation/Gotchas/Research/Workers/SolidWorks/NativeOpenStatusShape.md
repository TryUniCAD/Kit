# Native open status has a strict receipt shape

The saved-file verifier compares native open status to the exact object `{"errors": 0, "warnings": 0}`.
Adding diagnostic properties to that object rejects an otherwise clean open.

The first retry probe at `765e6b71c9` recovered startup and completed native measurements, then failed this receipt check.
The corrected implementation preserves the original status object.
It records every attempt and the total operation time in `open-attempts.jsonl` instead.
The subsequent probe at `d36d7d4806` passed the existing verification and independent-process comparison.
No acceptance predicate was relaxed.

See [the recovery observation](../../../../../re/automation/BatchEvidence/OpenRetryTimingObservation.json).
