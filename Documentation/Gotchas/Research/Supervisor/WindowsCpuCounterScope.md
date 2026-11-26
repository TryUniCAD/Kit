# Windows CPU counter scope

## Expectation

A Windows CPU measurement can appear to describe only the processors allowed by the supervisor's affinity mask.

## Actual behavior

`GetSystemTimes` sums activity across all CPUs on hosts with up to 64 logical processors.
On larger hosts it reports the calling thread's primary processor group.
Its kernel total includes idle time.
[Microsoft CPU counter reference](https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getsystemtimes) · [processor group count](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getactiveprocessorgroupcount)

## Workaround

Use the adaptive CPU signal only when the supervisor affinity covers the full set of counters.
Use idle, kernel, and user counter changes from the same interval.
When a usable sample is unavailable, the supervisor retains measured capacity and blocks upward target changes.
[Windows adaptive CPU measurement](../../../Changes/Research/Supervisor/Adaptive/WindowsAdaptiveCpu.md)
