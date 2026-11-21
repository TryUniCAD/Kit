# Lock fresh ordinary assembly sources

The existing one- and two-component fixtures teach archive structure but do not
prove fresh assembly construction. The
[new specifications](../../../../../re/tooling/sw2026/AssemblySourceSpecs.json)
define discovery cases with zero, one and two occurrences of one immutable
native part. They reserve three- and four-occurrence cases, with separate
placements and rotations, before the next assembly writer work.

The [source author](../../../../../re/tooling/sw2026/AuthorAssemblySources.py)
uses the registered 2026 COM library in the dedicated Windows VM. It sends one
sixteen-value transform per occurrence through
[AddComponents3](https://help.solidworks.com/2019/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~AddComponents3.html).
It checks both levels of the
[native component count](https://help.solidworks.com/2026/english/api/sldworksapi/SolidWorks.Interop.sldworks~SolidWorks.Interop.sldworks.IAssemblyDoc~GetComponentCount.html),
requires resolved, unsuppressed children with visible solid bodies, and records
placements, configurations, fixed state, feature problems and mass properties.
Independent expected mass properties follow from the unchanged part and its
requested placements. The empty discovery case has no geometry claim.

Each source is authored and reopened in separate processes between healthy
controls. Only native and observation hashes leave the held-out source lock
before independent prediction. Native output paths and the licensed template
stay outside the checkout. Measurements are pending; this authoring tool
does not generate Kit writer output or qualify any assembly or mate family.

The accompanying [native solve-state trace](../../../../../re/solidworks/records/AssemblySolveStatus2026.md)
shows where update paths replace the assembly's constructor status with an
active mate or reference-walk result. The source batch measures the separate
no-mate case before any value from that branch is used by a writer.
