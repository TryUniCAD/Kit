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
The Windows process case requires the queued successor to start before the first worker finishes.
It also requires an upward adjustment under the measured headroom guards.

### Sustained Windows replay

The matched replay used 256 jobs over the same 64 pinned Fusion inputs on Windows 11 with Python 3.14.6.
It used four-member groups, 64 controller leases, and the same two-CPU and 4 GiB reserves in both arms.
The private calibration launcher recorded the supervisor identity before dispatch.
The baseline source was `14570404846c8aa1f90b02e68d6f70a419719ca7` and the candidate was `5ab74c2e3ebdb3b24541681389a0075915db6929`.

| Observation | Baseline | Candidate |
| --- | ---: | ---: |
| Highest adaptive limit | 9 | 11 |
| Peak simultaneous reader calls | 6 | 6 |
| Wall time | 152.08 s | 129.37 s |
| Host CPU busy time | 34.02% | 39.48% |
| Minimum available RAM | 12.33 GiB | 12.08 GiB |

The candidate increased the target at 62.93 and 123.20 seconds with CPU fractions of 0.392 and 0.409.
The baseline remained at nine and reported `load measurement unavailable` after the healthy minute.
Both arms completed all jobs with equal neutral digests and complete CPU and resident-memory telemetry.
The pair verifies the adaptive decisions. It does not isolate a throughput gain or establish sustained overlap across 18 readers.

Manifest SHA-256 `3def76b3f5f1383810e429d090de073472d9aa9fef51cec88ef3bb37f413e0d3`.
Decoded output SHA-256 `1ee4850976533005df51a5146af68583b2c1bbfa2d6ec861e4b7f0fb1c3ca96d`.
Baseline report SHA-256 `8d644df5ffb8963dc93126d46603d2e86b017098ac5f6071c9b15de98f7abc20`.
Candidate report SHA-256 `c501f133a116db81e15fab59bd610c223ac522fb04e10b9606383a3a6961185d`.
