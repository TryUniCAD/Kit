# SOLIDWORKS capture recovery

Fresh-process catalogue captures log a lost COM/RPC session separately from
other launcher errors. The supervisor retries the first attempt in a new
owned process, subject to the job's existing attempt budget. If the next
attempt loses the session again, the supervisor rejects the job instead of
launching a third attempt for that error.

If the launcher reaches its shutdown deadline, it terminates only the owned
application. If a COM call hangs and prevents launcher cleanup, the worker
terminates the owned Windows job at the configured phase deadline and waits
for its processes to exit. After confirmed cleanup, the controller marks the
attempt retryable within the existing job budget. Each attempt stages the
scheduled case again and creates a separate directory in `NativeAttempts`.
A failed attempt does not release dependent decoders, and unrelated jobs can
continue. Forced cleanup does not count as a normal exit.

Use the existing [catalogue authoring command](../../../../Tasks/ResearchCommandLine.md#author-new-catalogue-samples).
Inspect the phase logs and owner receipts under `NativeAttempts`. Recovery
does not terminate an existing interactive application, repair a host that
cannot dispatch, or restart a persistent document-reopen owner. AI assistance
remains opt-in.

The offline supervisor fixture verified exit-status propagation, retry input
preservation, the retry limit on repeated RPC failure, and termination of a
simulated hanging launcher. Live SOLIDWORKS validation is still pending.
