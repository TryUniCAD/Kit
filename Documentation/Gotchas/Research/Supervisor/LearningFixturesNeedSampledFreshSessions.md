# Learning fixtures need sampled, fresh sessions

## Expectation

A memory-learning scenario can expect one `memory_estimate` event per completed fixture job.

## Actual behavior

The supervisor learns only from completions it accepted on a current lease that also have a positive sampled process-group peak.
Both skips are intentional and documented in [versioned memory estimates](../../../Changes/Research/Supervisor/VersionedMemoryEstimates.md).

On a loaded host, one supervision pass can last several seconds because each controller call is a separate Python process.
A fixture that sleeps for one second can start and exit between two `ps` refreshes.
Its receipt then records `sampled_group_peak_memory_bytes: 0`, and the supervisor emits no estimate.
The default fixture lease of three seconds can also expire between renewals.
The finish is then stale, and the supervisor discards its sample.

On a loaded two-CPU host with three CPU burners, every run of the 55-job window scenario missed at least two estimates.
With the default lease, nearly all misses were stale finishes.
With a 30-second lease alone, 3 of 6 runs still missed one or two non-stale, never-sampled sessions.
This matches the macOS queue failure for `521bb5f7`, where 54 of 55 estimates were emitted.

## Workaround

The learning runner writes a marker to stdout and waits until the supervisor drains the marker into its session `stdout.log`.
The supervisor drains logs in the same `tend` call that reads that pass's process-group sample.
That sample comes from a `ps` refresh taken after launch and while the runner is still alive.
The window scenario gives its jobs a 30-second lease, so a slow pass cannot make the completion stale.
With both changes, the targeted test passed 8 of 8 times under the same load.
