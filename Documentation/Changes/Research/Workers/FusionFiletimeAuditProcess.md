# FILETIME auditing through accepted controller artifacts

The retained Windows process identity checks now exercise the real supervisor, A03 queue and immutable artifact intake before invoking `AuditFusionPhases.py` as an independent command.
They no longer load or call the auditor's `phase_process` helper directly.
The existing `ProtocolFixture.py` has an `audit-supervised` fixture operation that publishes independently authored phase-A measurements, receipt, dispatch and explicitly non-CAD placeholder files through ordinary supervisor intake.
It neither starts an application transport host nor dispatches a native application; Phase B remains waiting.

The eight cases preserve the exact tick identity positive, one-tick shift and missing-tick refusals, the original trimmed legacy fixture exception, a shifted legacy tick refusal, both directions of fixture-marker disagreement and the wrong-reason refusal.
The known `133485408000000001` FILETIME and its one-tick successor share Unix second `1704067200`, so the shifted cases specifically require full-tick comparison.
Each case requires unchanged controller database bytes, queue receipt, accepted receipt and accepted result after auditing.
Successful observations retain `native_qualified: false` and `launched_application: false`; the fixture records and placeholder files establish no licensed application startup, restart or CAD acceptance.

The test remains selected recursively by the existing Linux and macOS application process jobs and by the complete candidate test plan.
Local validation is restricted to static formatting, syntax, typing and policy checks.
The changed test passed normal-configuration Mypy 2.4.1, Pyright 1.1.414 and Black 26.10.1 checks; both changed Python files parsed without importing them, and Prettier 3.6.2 passed this entry.
No test, collection, auditor, controller, supervisor, reader, SDK or native application was executed locally; the assembled candidate requires hosted process verification.
