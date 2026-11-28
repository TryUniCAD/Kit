# Cache the Windows readback fixture assembly

## Scope

Task: Windows fixture startup after queue run 46020197598.
Owner: the delegated CI stability worker.
Dependencies: PRs #356 and #357, Windows PowerShell 5.1, and the existing complete-suite platform shards.
Exit: current-head PR checks and configured review, followed separately by Windows queue acceptance.
This change does not authorize queue enrollment or merging.
It changes no workflows, CI scripts, resource configuration, test assertions or existing platform selection.

## Behavior

The readback fixture compiles its C# source and fixture program into a temporary DLL.
The cache key includes both source texts, the CLR version, PowerShell version and process architecture.
The default directory is `KitReadbackFixture` below `RUNNER_TEMP`, or the current user's temporary directory outside CI.
`-CacheRoot` selects an isolated directory for the process-boundary regression.
No cross-run GitHub cache or committed binary is used.

A named mutex serializes writers for one key and directory.
Compilation writes a unique temporary file before atomic publication to the keyed DLL path.
Every later process loads that assembly with `Add-Type -Path` instead of recompiling.
Compilation and loading errors still fail the case.
No retry, xfail or new skip path hides a failure.

The cold warm-up and its lock wait have a 360-second failure bound.
This is a conservative containment bound, not a proven compile-time p99.
The existing 60-second per-case readback limit remains unchanged.
Warm-up output now records total process time, script-entry and compile-entry timestamps, compilation duration, and cache-hit state.
The existing pytest report log captures that output without workflow changes.

The owner-parent helper no longer launches PowerShell or starts CIM/WMI.
Windows reads a fresh Toolhelp process snapshot for every observation.
It distinguishes normal enumeration completion from native errors and closes the snapshot handle.
Linux retains its independent `ps` observation.
No observed parent identifier is cached.

## Cause and evidence limits

The old warm-up compiled only into its own process memory, then exited.
Every later fixture process compiled the same C# source again.
Microsoft documents [in-memory compilation and on-disk output](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/add-type?view=powershell-5.1).

[Queue run 46020197598, Windows shard 4](https://github.com/TryUniCAD/Kit/actions/runs/46020197598/job/140580380067) exceeded the warm-up's 120-second process deadline.
That deadline includes PowerShell startup, source loading, compiler startup, compilation, and any scheduling or scanning delay.
The archived implementation did not time those phases separately.
It cannot establish whether CPU starvation, Defender scanning or compiler startup caused the extreme tail.
The timeout is right-censored, so its eventual duration and a genuine warm-up p99 cannot be recovered.
The structural repeated-compilation defect is confirmed independently of that missing host attribution.

## Measured distribution

The sample contains 57 first `CircleQueueTests` or `DiscoveryQueueTests` calls across 15 settled candidates with usable Windows reports.
It includes successful shards from candidates that were later cancelled.
Only those two modules call `WarmProgress`, and each shard's first call includes its warm-up.
These are enclosing test-call durations, not isolated warm-up measurements.
They include installation and dispatch work, so successful call durations are upper bounds on successful warm-up durations.

The 56 successful first calls had minimum 1.809 seconds, median 4.284 seconds, p95 8.153 seconds, p99 16.261 seconds, and maximum 22.901 seconds.
Percentiles use linear interpolation.
None of those successful calls exceeded 60 or 120 seconds.
The remaining call failed after 128.975 seconds, including a warm-up process killed at its 120-second deadline.
Exactly one of 57 first calls exceeded each threshold: 1.75%.
The warm-up crossed both thresholds once and no successful warm-up could have crossed either threshold in this sample.
Its true completion time remains unknown, so an uncensored warm-up p99 cannot be calculated.

The 360-second containment bound provides three times the previous censored limit and over fifteen times the successful first-call maximum.
It is also over twenty-two times the successful-call p99, but that percentile excludes the censored failure.
It does not guarantee completion under arbitrary hosted-runner starvation.
The structural cache change prevents repeated compiler exposure after the first successful publication.

Raw first-call durations in seconds, by Actions run ID:

```text
46020590652: 4.878, 4.060, 5.782, 3.938
46020197598: 4.286, 3.698, 4.637, 128.975 failed
46020194117: 4.603, 8.292, 5.186, 4.744
46020191819: 8.107, 3.365, 3.716, 6.051
46020189295: 3.903, 6.228, 3.773, 4.204
46017129154: 4.660, 3.576, 6.201, 6.208
46011437773: 3.729, 4.940, 4.282, 3.663
46011283916: 3.940, 7.899, 6.256, 8.004
46019794004: 10.829
46009489342: 2.426, 5.188, 5.833, 2.835
46005827308: 22.901, 7.034, 5.370, 5.865
46005774891: 2.288, 8.098, 3.491, 4.189
46005349452: 2.303, 4.126, 3.360, 4.468
45902261255: 1.996, 4.333, 3.721, 3.616
45902259589: 1.809, 4.241, 3.099, 3.859
```

The same reports contain 29 owner-restart calls: minimum 6.347 seconds, median 8.424 seconds, p95 9.629 seconds, p99 11.480 seconds, maximum 12.141 seconds.
None exceeded 60 or 120 seconds.
Those are also complete test-call timings, not isolated parent-query warm-ups.
The native snapshot change removes the analogous unbounded cold-provider risk rather than widening or caching observations.

## Verification

The new Windows process regression starts concurrent cold users, requires exactly one compile, and verifies DLL reuse without rewriting.
It changes source bytes and requires a different compiled assembly.
The existing readback cases continue to exercise the real assembly's journal and filesystem behavior.
The owner regression checks a real child process, its parent, and process disappearance.

Linux checks include changed-source formatting, Ruff, strict typing, steering compliance, and repository policy command coverage.
Windows PowerShell compilation, assembly loading, mutex behavior and native process enumeration need the existing Windows queue shards.
Green PR checks do not prove those Windows behaviors or queue acceptance.

See the [assembly warm-up gotcha](../../../Gotchas/Ci/Windows/ReadbackAssemblyWarmup.md) and [owner query guidance](../../../Gotchas/Ci/Windows/OwnerParentQueryColdStart.md).

## Prepared assembly compatibility

The [PR #121 integration](SolidworksReadinessFixtureMerge.md) retains cache warm-up and prepared capture as separate process modes.
Preparation copies the complete cached DLL before listener startup.
The timed capture process loads that prepared DLL without compiling.
