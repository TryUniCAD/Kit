# A self reference stores the model name and the file path independently

The ordinary file-definition constructor initially derives its name from the
path stem. The native model factory then calls `setName` with the filed model's
node name and retains the original path. A document's display name and the
basename at the output path can therefore differ in the same reference record.

When constructing the self record, take the name from the generated assembly
model and the path from the authored save destination. The configuration's
direct map must share the resulting model-header object's identity.

The [constructor and save trace](../../../../../../re/solidworks/records/AssemblyConstruction2026.md#ordinary-self-reference-construction)
identifies both native call sites, the model name accessor and the map handoff.
