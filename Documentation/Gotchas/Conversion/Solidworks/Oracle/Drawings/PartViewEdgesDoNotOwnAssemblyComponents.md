# Part-view edges do not require an assembly component owner

A drawing view may expose one visible projected part component while its actual model edges have no assembly-context component owner. In the disclosed 2026 control, `GetVisibleEntities2` returned four correct visible edges and the unique target rail passed its geometry checks, but `IEntity.GetComponent` returned null. Requiring it to equal the projected component stopped both controls before annotation creation.

The public contract restricts `GetComponent` to assembly entities, including assembly entities displayed in a drawing. Preserve the actual view/component/model/path/configuration checks, then query `IEdge.GetBody` and compare that body with the actual referenced part's live sole body. Require exact selected-edge membership in that body's edge inventory. Coordinates alone do not establish ownership. Keep null component evidence and reject a non-null foreign owner; do not require null as a new default.

The new body predicate is API-bound and host-verified, but must pass native brackets before counting an annotation lifecycle. [Exact failure, interface slots and successor](../../../../../../re/solidworks/records/DrawingPartEdgeBodyOwnership2026.md)
