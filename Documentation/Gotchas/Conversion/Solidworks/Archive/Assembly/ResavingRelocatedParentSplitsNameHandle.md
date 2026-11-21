# Saving a relocated native assembly can split its name handle

The two original planar assemblies each stored a shared `Assem1`
string handle. After closed-copy rebind, child edit and parent save,
one reference owns a separate string with the actual saved parent
name. Retaining both names adds one map slot. The detached occurrence
flags and live appearance allocation otherwise follow the same
measured transitions as the generated saves.

Compare the persistent occurrence, linked owner and actual file
identity when relating original and generated saves. Record the
separate native filename handle for the relocated comparison.
[Paired typed evidence](../../../../../../re/solidworks/measurements/2026/PlanarOriginalAllocationParity01.json)
