# SOLIDWORKS 2026 assembly construction research

Fresh assembly construction remains in progress and has no target-application acceptance evidence. The [construction finding](../../../re/solidworks/records/AssemblyConstruction2026.md) records native root, component, path, and configuration ownership before adding a fresh builder.

The finding distinguishes constructor seeds from accepted saved-model values. It identifies concrete runtime classes, rejects abstract base records as fresh object choices, binds serialized members to native accessors, and closes the assembly model-update predicate. The named part and assembly constructors both reach the active common initializer that supplies a unit self component and relation manager with the actual model as owner. External references, placements, configuration domains, solver state, and derived caches remain active work.

The [concrete-component gotcha](../../Gotchas/Conversion/Solidworks/Archive/AssemblyConcreteComponents.md) explains why an existing base serializer or a class name does not prove that a standalone object can be constructed. The source codec's 14 exact stream round trips are recorded separately and do not establish fresh generation.

The research [`Assembly.py`](../../../re/tooling/sw2026/builders/Assembly.py)
module now computes the ten-double bounding-box record from explicit semantic
minimum/maximum coordinates. Center and enclosing sphere radius follow native
constructor arithmetic; high and low corner wire order follows the native
accessors and serializer. It rejects nonfinite or reversed bounds and supplies
no invalid constructor box as a neutral cache. The
[bounds-state gotcha](../../Gotchas/Conversion/Solidworks/Archive/BoundingBoxSphereState.md)
records why six corners or zero fill are insufficient.

The same module constructs embedded ordinary native file definitions from an
explicit authored reference path, document kind and creation time. Windows
filename stems, native part/assembly categories and typed string handles follow
native setters and serializers. Virtual, imported and PDM relationships are
outside this initial profile. A separate helper constructs an explicit generated
configuration-name/id pair or the native unset pair. No saved path, timestamp,
configuration name or identifier is supplied as a default.

These are closed initial record operations, with static parsing only. Their
remote process coverage belongs with the completed assembly graph. Reference insertion,
configuration ownership and placement have additional static dataflow evidence;
unresolved external identity, option domains, solver and cache policy still
prevent claiming a complete fresh assembly writer.

Verification is static inspection of the hashed 2026 modules and read-only decompilation in private projects outside repository checkouts. No local tests or CAD operations ran. Production adapter support, held-out assembly acceptance, and vendor load/rebuild/mate-edit measurements remain unproven.
