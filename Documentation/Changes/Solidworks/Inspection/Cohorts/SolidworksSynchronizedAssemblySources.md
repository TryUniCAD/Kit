# Author ordinary assembly sources with a saved child stamp

The [paired child save diagnostic](../../../../../re/solidworks/measurements/2026/AssemblyChildSaveProbe01.json)
found that a parent-only save reopens with warning 32 while an otherwise
equivalent parent with an explicitly saved child reopens cleanly. The native
child update stamp at authoring was 134 in both cases. After reopen it was
120 without the child save and 134 with the child save. Geometric properties
matched and both controls passed.

The [new source specification](../../../../../re/tooling/sw2026/AssemblySourceSpecs03.json)
reserves empty, single and repeated discovery cases and two held-out
placement sets. Each populated author phase saves only its exact owned child
copy after rebuild and before saving the parent. Reopening requires zero
errors and warnings, the same saved child stamp, unchanged parent and child
hashes and the requested occurrence geometry. The public lock records child
identity without exposing its held-out stamp or other private observations.

The new batch is pending. These are native test sources with no generated
writer output. The original control and the failed previous attempts remain
unchanged.
