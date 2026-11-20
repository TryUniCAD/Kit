# SOLIDWORKS part empty exploded-view manager

The internal planar import constructor accepts an explicit empty
exploded-view manager. It allocates the concrete part manager, puts it
in the actual configuration model, and writes a nameless keyword row
using the allocated persistent ID. The strict local reader validates the
keyword's shared configuration and resolved map identity.

Three disclosed source projections preserve their linked planar solid,
note pair, lights and property owners with zero construction file reads.
Adding the manager changes only the configuration, manager, resolved
graph, two model headers and keyword index at the same destination. The
common empty-manager initialization preserves complete prior generated
assembly and child bytes. Populated exploded-view steps remain outside
this constructor.

[Construction evidence](../../../../../re/solidworks/records/PartExplodedViewConstruction2026.md)
· [Native probe](../../../../../re/tooling/sw2026/imported_body_source/ProbeImportedPartScene.py)
