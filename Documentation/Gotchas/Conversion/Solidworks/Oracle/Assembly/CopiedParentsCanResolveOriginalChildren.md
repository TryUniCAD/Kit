# Assembly copies can resolve the original child

A20 and A21 each retained their saved dependency on the original
child after both files were copied into a fresh directory. The native
application opened each copied parent successfully, then resolved the
child to its old absolute path. Both controls passed and the observer
refused the edit before any original was changed.

Check the child's actual loaded path before changing dimensions or
saving. For this paired experiment, query the closed parent's stored
dependency and rebind the copied parent to the hash-identical child
copy before opening it. Confirm the dependency change and the original
hashes independently.
[Copy run](../../../../../../re/solidworks/measurements/2026/PlanarOriginalCopyRejected01.json)
