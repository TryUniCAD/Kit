# Build the initial assembly configuration and mate-list handoff

The assembly research builder composes the initial 16 resolved features
from the same folder, plane and origin constructors as the part builder.
It adds the assembly's live-section folder and an explicit empty mate group.
The configuration manager constructs a concrete assembly configuration
rather than a part configuration with a changed class name.

The [archive layout receipt](../../../../../re/solidworks/measurements/2026/AssemblyArchiveLayoutProcesses458.json)
verifies the same 16 resolved roots in three ordinary native assemblies.
The [mate-list rule](../../../../../re/solidworks/records/AssemblyMatesList2026.md)
uses the generated end-of-resolved map count and the shared empty object
list grammar. It rejects nonempty mate graphs at this boundary.

The extended remote process gate exercises five generated logical streams:
the configuration, its header, the configuration manager, resolved
features, and the empty mate list. It requires whole-stream and map equality
after independent decoding. The
[remote process job](https://github.com/TryUniCAD/Kit/actions/runs/44006095790/job/133781715823)
passed on `fc6fd09fb`. The reduced container is not a complete native assembly file.
