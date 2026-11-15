# Browser insertion advances the reference counter twice

Assembly member `f1560` is not a visible component count. A single browser-node
insertion request can advance it twice.

In 2026, the browser-node insertion overload increments the member before
calling the common insertion helper. The common helper increments the same
member again on its successful path. Ordinary insertion also reaches that
common helper. Constructor state alone does not describe these transitions.

Compute counter transitions from the actual supported construction operations.
Keep this counter separate from header component activity counts and visible
feature counts. Deletion and other insertion routes still need their own rules.

The [construction finding](../../../../../re/solidworks/records/AssemblyConstruction2026.md#components-paths-and-configuration-ownership)
records the native caller addresses and evidence scope. This is static dataflow
evidence, not an execution trace or generated-assembly acceptance result.
