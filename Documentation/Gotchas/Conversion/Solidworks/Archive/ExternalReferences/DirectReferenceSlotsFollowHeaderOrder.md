# Direct archive slots follow the model header order

An ordinary child may have file id zero and occupy archive slot four.
The native configuration serializer allocates the self entry first and
then the external file list entries. Both use the archive counter after
the model class and object entries. Advancing a counter by the directory
size alone leaves the reference target unresolved.

Allocate the slots from the ordered header objects so downstream streams
can refer to those same objects by identity. The
[native archive map trace](../../../../../../re/solidworks/records/ArchiveMapConstruction2026.md#direct-header-objects)
identifies the separate registration routines used by the reader and writer.
