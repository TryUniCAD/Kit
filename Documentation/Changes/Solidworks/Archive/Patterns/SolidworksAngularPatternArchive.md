# Share the finite hinge and angular datum archive codec

The SOLIDWORKS 2026 part archive codec now decodes and emits the finite intersection axis and constrained angular plane used by the measured local linear-pattern family. The graph retains both ordered axis supports, the actual selected hinge, the separate angular constraint and the retained driving display. The existing ordinary sketch and plane reference contexts keep their original component types.

The internal part archive emitter writes the complete pattern graph through its normal ResolvedFeatures path. Ten guarded processes reproduce six generated archives without runtime input reads. The normal linked codec replays 28 complete streams across the generated originals, ten disclosed native saves and two controls. Public neutral pattern writing and strict cache-free geometry remain open. [Exact evidence and reproduction](../../../../../re/solidworks/records/SharedAngularPatternArchive2026.md)
