# Write a measured SOLIDWORKS planar mate pair

Kit writes the measured SOLIDWORKS 2026 SP05.2 assembly with an aligned
coincident mate and an aligned distance mate. The writer generates the root
and its shared dimensioned part from the neutral model.

The bundle receipt covers both outputs. Strict reopen recovers the mate
group, four datum endpoints, the fixed occurrence, the distance driver
and the three child drivers. A complete strict reread republishes the
same measured files, including through a relative file handle followed
by a neutral JSON round trip. The measured writer requires exactly two
component occurrences.
[Assembly writer reference](../../../../Reference/Adapters/SolidworksAssemblyWriting.md#coincident-and-distance-mates)

A strict read with component resolution disabled retains the assembly-owned mates,
their occurrence and datum references, the mate group, and the distance driver.
Neutral JSON preserves those records. The reader does not verify the referenced
child datums without the component files, so the mate report remains deferred
and the read does not qualify for native republication.
