# Configuration owners need model context

A builder's in-memory configuration has an actual model owner. This does not
mean that a standalone configuration archive stores an object reference for
that runtime field.

The 2026 configuration uses the shared feature serializer, whose current
native field grammar has no standalone owner field. Native feature getter
`sldmodu.dll!0x4bb45da0` reads the runtime owner at `+0x290`; constructing
that relationship and decoding the standalone record are separate operations.
The [first process check](https://github.com/TryUniCAD/Kit/actions/runs/43709486908/job/132797724161)
completed configuration encoding, decoding and exact reencoding, then failed
because its report incorrectly expected a decoded `owner` dictionary key.

Do not add a wire field to satisfy a constructor-shaped assertion. The process
check now encodes a real generated unit self component alongside the initial
configuration and file-definition records. Its native component-owner reference
resolves through a fresh generated owner-map seed. That checks an actual wire
edge while preserving the standalone configuration grammar. Full model-context
restoration and generated assembly acceptance remain separate work.

The [construction record](../../../../../re/solidworks/records/AssemblyConstruction2026.md#initial-assembly-configuration-graph)
records the exact native constructor ownership and the process boundary.
