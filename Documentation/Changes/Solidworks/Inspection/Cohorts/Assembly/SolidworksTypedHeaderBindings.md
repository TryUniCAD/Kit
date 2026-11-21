# Bind assembly references to their model header objects

The SOLIDWORKS 2026 research codec allocates configuration archive slots
from the typed model header. It registers the self object first, then
the external file entries in list order. Both part and assembly builders
pass the header they generated to the configuration writer.

The synchronized assembly readback now requires references to resolve to
the actual header object. It checks that repeated occurrences share that
object and that the configuration and resolved graphs have no unresolved
references. The [remote native-file job](https://github.com/TryUniCAD/Kit/actions/runs/44016972506/job/133817222480)
verified three typed occurrence bindings and all 35 exact comparisons.
The two generated empty candidates reproduced their measured hashes.

The field inventory retains model-header positions and original indices on
the object records. The configuration map uses its own slot indices for
the same identities. The process suite checked 26 configuration and 26
linked resolved inventories, including the direct slot range and the
linked identity handoff.

The [native map rule](../../../../../../re/solidworks/records/ArchiveMapConstruction2026.md#direct-header-objects)
gives the register order and counter behavior. The next stage will
construct the external directory and occurrence graph for a populated
assembly.
