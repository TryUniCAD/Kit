# Windows adaptive CPU measurement

The research supervisor uses Windows system CPU counters to evaluate upward pool adjustments.
The default adaptive policy can add one physical session after a healthy minute with sufficient CPU and memory headroom.
Configured CPU and memory reserves, the controller capacity, and worker memory estimates still apply.

## Observations

With `adaptive_limits` enabled, Windows admission events include `host.cpu_busy_fraction_1m`.
The supervisor derives this fraction from the idle, kernel, and user counter changes across 60 to 70 seconds.
The threshold for an increase is below 0.85.
The field remains null while the interval warms up or when a usable sample is unavailable.
In both cases the existing missing-load guard prevents an increase.

The counter scope requires unrestricted CPU affinity and one Windows processor group.
Use the [supervisor guide](../../../../Reference/Research/ResearchSupervisor.md#resource-admission-and-memory-stops) to inspect admission and memory reserves.
[CPU counter scope](../../../../Gotchas/Research/Supervisor/WindowsCpuCounterScope.md)

## Verification

On a 20-CPU Windows host, the existing policy calculated 18 slots with two reserved CPUs and started with an active limit of nine.
A grouped 64-file probe completed in 23.34 seconds and peaked at six overlapping readers.
It averaged 35.2 percent host CPU activity and retained at least 11.99 GiB of available memory.
That short probe ended before the adaptive interval could elapse.
The Windows process case exercises the interval with a queued successor and the real supervisor.
