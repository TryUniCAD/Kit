# Bind assembly references to their model header objects

The SOLIDWORKS 2026 research codec allocates configuration archive slots
from the typed model header. It registers the self object first, then
the external file entries in list order. Both part and assembly builders
pass the header they generated to the configuration writer.

The synchronized assembly readback now requires references to resolve to
the actual header object. It checks that repeated occurrences share that
object and that the configuration and resolved graphs have no unresolved
references. Remote process evidence is pending.

The field inventory retains model-header positions and original indices on
the object records. The configuration map uses its own slot indices for
the same identities. The process suite checks the direct slot range and
verifies that linked resolved features inherit the same identities.

The [native map rule](../../../../../../re/solidworks/records/ArchiveMapConstruction2026.md#direct-header-objects)
gives the register order and counter behavior. The next stage will
construct the external directory and occurrence graph for a populated
assembly.
