# Trace assembly rebuild warnings before the next source lock

The second ordinary source batch authored all five native files with healthy
controls. On fresh open, its empty discovery assembly had zero warnings; the one-
and two-occurrence assemblies both returned `NeedsRegen` (`32`). Its owned
window observer also found additional assembly progress labels and performance
details. No window was clicked. The whole
[attempt](../../../../../re/solidworks/measurements/2026/AssemblySourceAttempt02.json)
remains failed and frozen.

The [diagnostic](../../../../../re/tooling/sw2026/ProbeAssemblyRebuild.py)
compares a read-only open with a normal open of the same immutable discovery
assembly. It reads
[NeedsRebuild2](https://help.solidworks.com/2026/English/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IModelDocExtension~NeedsRebuild2.html)
before and after active and full-configuration rebuilds. It saves a new copy
and measures that copy in another fresh process. Known load-progress text
is observed without dismissal, and warnings stay in each phase's record.
This does not qualify any assembly writer output. Diagnostic measurements
are pending for the separate saved-copy reopen.

The [first diagnostic](../../../../../re/solidworks/measurements/2026/AssemblyRebuildAttempt01.json)
observed warning `32` and `NeedsRebuild2 = 1` in both open modes, with one
component and no feature problems. `ForceRebuild3` cleared the state to `0`;
`ForceRebuildAll` and the new save retained that state in memory. An unclassified
progress detail blocked the fresh reopen. The observer now accepts the recorded
long form of elapsed seconds as progress, and the first attempt stays incomplete.
