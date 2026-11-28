# Native lifecycle of a portable registry assembly

This disclosed experiment in PR #121 used a portable neutral assembly, a
dimensioned rectangular child, and a private Kit writer registry. The input
declared three occurrences of the same child, one fixed anchor, and ordered
aligned distance, coincident and parallel mates. The registry produced one
`.SLDASM` and one shared `.SLDPRT` through the normal write entry point with
an explicit registry instance. The guarded producer opened no model or
template files during writing.

The source manifest binds 4,237 frozen files. The guest verified every
manifest entry and independently regenerated the geometry and mate
predictions without using writer readback. The first transport attempt failed
before launching SOLIDWORKS because the pinned guest interpreter could not
import `interchange`. The retry loaded the same verified snapshot and
observer sources with explicit import roots. The frozen generated files kept
their original hashes throughout the native run. SOLIDWORKS saved separate
working copies at their linked destinations.

SOLIDWORKS 2026 SP05.2 `34.5.2.0604` passed four distinct native processes
with two healthy controls and 440 numerical comparisons. Clean open,
rebuild, and fresh reopen preserved 28 assembly and 25 child feature rows,
three resolved bodies, six mate endpoints, configurations, child dimensions,
and calculated volume, area and center of mass. The driving distance
advanced from 42 to 57.73 mm, with the expected dependent occurrence
transforms. A child-first save propagated the revised child stamp to the
parent and the fresh process resolved the same child with stamp 144.

Two strict Kit parent reads and four typed parent and child audits
cover the generated and native-saved files. All 26 modeled stream cycles
are byte-identical. Both parent reads retain the legacy informational
`sldasm.native_record_unresolved` diagnostic while the six typed endpoints
and three child drivers are recovered.

The result is scoped to the disclosed private-registry input. Normal
default-registry registration, wider assembly semantics and original FCStd
qualification have separate acceptance gates.

[Exact measurement and source hashes](../measurements/2026/SdkPortableAssemblyRegistryNative01.json)
[Native observer](../../tooling/sw2026/InspectPortableAsmTrial.py)
[Independent portable prediction](../../tooling/sw2026/PortableAsmPrediction.py)
[Original planar mate qualification](SdkOriginalPlanarMateNative2026.md)
