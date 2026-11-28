# Generate binary display states for one concentric assembly profile

The internal SOLIDWORKS assembly compositor accepts `DisplayValues` through `EmitAsmStreams`. It takes the all-visible default and two distinct, opposite named visibility states. Each state names the two actual direct occurrences of one owned radial child.

The composer resolves the active configuration, component identities, file references and datum owners before constructing `ThirdPtyStore/VisualStates`. It supports the aligned, unlocked concentric mate under the measured generated version-19000 profile. Original source appearance, populated chronology and public writing remain outside this scope.

The two guarded processes reproduced the exact previously native-tested parent and child. The visibility stream is 1,819 bytes, and all twelve inherited parent streams retain their exact bytes. Sixteen builds and thirteen focused refusals pass with zero audited runtime external accesses.
[SDK evidence](../../../../../re/solidworks/records/SdkConcentricVisualStore2026.md) · [Guarded result](../../../../../re/solidworks/measurements/2026/SdkConcentricVisualStore01.json)
