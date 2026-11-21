# Feature dimension ids belong to the dimension

## Expectation

Every persistent id is stored in a node's `f08`, and a feature parameter owns
the persistent id used by its driving dimension.

## Observed behavior

The 2026 feature-dimension parameter-naming routine at `sldmodu` `0x4c821c40`
names the parameter, then calls `moHeader_c::getNewID` for the dimension's `f50`.
The fresh parameter's node id remains the constructor's `-1` on this path.
Parameter names and the separate parameter reference count do not allocate that id.

## Workaround

Bind the shared header allocator to the object's actual persistent-id field.
Use `PersistentIds.allocate(dimension, field="f50")` for this feature-dimension
path and the default `f08` field for ordinary model nodes.
Keep configuration-local ids and sketch-entity ids in their separate namespaces.
Do not introduce a synthetic node-id field to stand in for a dimension id.
