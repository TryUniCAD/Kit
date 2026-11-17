# Generate a native parallel plane mate in research

The SOLIDWORKS 2026 research composer supports one aligned parallel mate using principal-plane selections on two ordinary occurrences of a generated part. It writes the native `moMateParallel` in the inherited mate list and uses the shared feature, wrapper reference, creation log and configuration allocators.

Run `ParallelMateBundleProcess.py` with the authored assembly bundle on stdin. The process verified both generated files, six exact stream round trips, the selected datum identities and zero runtime file reads. Both existing coincident builds reproduced their original bytes. The first generated parallel pair opens and rebuilds cleanly between two A19 controls. It preserves both plane references and the authored separation. Editing, save and held-out qualification remain open.

[Construction and trial protocol](../../../../../../re/solidworks/records/AssemblyParallelMateConstruction2026.md) · [Structural receipt](../../../../../../re/solidworks/measurements/2026/GeneratedParallelMateBundle01.json) · [Native trial](SolidworksGeneratedParallelMateNativeProof.md)
