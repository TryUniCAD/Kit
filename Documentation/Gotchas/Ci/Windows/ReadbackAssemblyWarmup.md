# A discarded in-memory compile does not cache a fixture assembly

Expected: a successful readback warm-up prevents compilation during later fixture processes.

Observed: `Add-Type -TypeDefinition` creates an in-memory assembly unless `-OutputAssembly` is specified.
The old `-CompileOnly` process discarded that assembly when it exited.
Every later fixture process compiled the same source again.
The warm-up only helped runner-level startup caches.

[Queue run 46020197598, Windows shard 4](https://github.com/TryUniCAD/Kit/actions/runs/46020197598/job/140580380067) timed out in warm-up after 120 seconds.
That observation is right-censored: the compiler's eventual completion time is unknown.
The log does not separate PowerShell bootstrap, compiler work, CPU scheduling or antivirus scanning.
It cannot establish that compilation itself consumed all 120 seconds.

The fixture now publishes a source/runtime-keyed assembly under the shard's temporary directory.
A named mutex serializes first writers, and a temporary DLL is renamed only after successful compilation.
Later PowerShell processes load that DLL without recompiling.
The owner-parent check removes its separate PowerShell/WMI startup dependency by using a fresh native process snapshot.

Successful warm-up output records complete process time, script phase timestamps, compilation time and cache-hit state.
Pytest report logs retain captured output for later timing analysis.
A timeout also prints partial diagnostic output before it propagates.
These measurements must establish the host-level cause in a future Windows queue run.
See [the change and measurement record](../../../Changes/Ci/Testing/ReadbackAssemblyCache.md).
