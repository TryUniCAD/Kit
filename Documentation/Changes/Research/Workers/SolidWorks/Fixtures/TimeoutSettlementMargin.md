# Preserve controller time for Windows timeout fixtures

The Windows readback worker reserves five seconds between the application
request deadline and the supervisor's worker cutoff. This gives the worker
time to record cancellation, quarantine the queue and publish its result.
The timeout and restart fixtures add four seconds to their total deadlines
to keep the original application request window.

The hosted cancellation fixture reported that the worker finished while the controller held no result.
The scenario now requires an accepted finish before reading the stored result and checking the application hold.
The restart fixture also requires the original supervisor to park the job
before its injected exit. A worker stopped at its deadline failed that
check in the hosted Windows shard.
