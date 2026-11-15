# Model offsets depend on the concrete root

Part and assembly records share the model base. Their later fields do not
share one layout: a part scalar can occupy the offset of an assembly map.
Calling the part constructor and renaming its class would retain invalid
field ownership.

The common `model_fields` factory follows the shared LW/RES serializer
boundary. It receives the actual concrete object and explicit generated
dependencies. `part_root` adds its own fields afterward. Assembly construction
must supply its concrete self component and derived fields from its own rules.

Keep serializer `PartOnly` branches with the part construction even when the
underlying runtime member was initialized in the model constructor. Do not
copy a part field dictionary into an assembly builder.

The [construction record](../../../../re/solidworks/records/ModelConstruction2026.md#part-root-graph)
records the exact shared methods and static field partition. Native fresh
assembly acceptance remains unfinished.
