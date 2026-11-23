# An empty assembly property manager has its own file owner

The six disclosed SOLIDWORKS 2026 SP05.2 concentric assembly saves
use `moAssyFilePropContainer_c` in the keyed property container. The
corresponding parts use `moFilePropContainer_c` and their separate
cut-list owner. Validate the concrete file class, null list fields and
configuration join before attempting to transfer that scope.

Core XML also owns a separate package creation instant. In two of the
three disclosed pairs it is one second later than the model header's
creation instant. In the third it agrees. Preserve the actual package
creation event and derive the modified event from the paired self-file
save records. [Exact typed evidence](../../../../../../re/solidworks/records/ConcentricD01PropertyOwners2026.md)
