# Generate a native parallel plane mate in research

The SOLIDWORKS 2026 research composer supports one aligned parallel mate using principal-plane selections on two ordinary occurrences of a generated part. It writes the native `moMateParallel` in the inherited mate list and uses the shared feature, wrapper reference, creation log and configuration allocators.

Run `ParallelMateBundleProcess.py` with the authored assembly bundle on stdin. The process verified both generated files, six exact stream round trips, the selected datum identities and zero runtime file reads. Both existing coincident builds reproduced their original bytes. The scoped native observer uses read-only controls and measures initial open and rebuild. Native qualification and held-out coverage remain open.

[Construction and trial protocol](../../../../../../re/solidworks/records/AssemblyParallelMateConstruction2026.md) · [Structural receipt](../../../../../../re/solidworks/measurements/2026/GeneratedParallelMateBundle01.json)
