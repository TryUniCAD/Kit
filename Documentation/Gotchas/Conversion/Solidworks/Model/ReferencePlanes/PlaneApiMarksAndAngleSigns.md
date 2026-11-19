# Plane API selection marks and angle signs have separate owners

Appending a plane and line in a particular order does not establish their `InsertRefPlane` geometry slots. The pinned 2026 coupler queries each actual selection mark, requires one to three selected wrappers and rejects duplicate/out-of-range marks. Preserve plane mark `0` and hinge mark `1` for the ordinary angle-plane plus coincident-line operation, even when append order changes.

A negative raw double also does not select the reverse angular direction. The consumer starts its angle at zero and copies only a greater-than-zero value. The ordinary angular reverse flag comes separately from mask bit `256`; the angle constraint itself is bit `16`. Verify the actual selected plane and hinge frames and native rotation sign before lowering a signed source angle.

The current command's `IsBeingCreatedByAPI` flag is separate from the old-API predicate used by native plane factory compatibility. That predicate reads actual existing feature/data ownership and creation version. Do not substitute the current command flag for it or infer an archive class from the public plane type.

Bind the actual angular parameter from the plane feature's own display list before editing. The existing offset/radial observer's non-radius branch expects a linear dimension and must not be invoked with an arbitrary angle mode. Fresh save/reopen must retain actual angular ownership, selected references, tree and geometry. [Exact source and replay](../../../../../../re/solidworks/records/FreecadCylinderAngleApi2026.md)

Verification is source-only against exact original hashes and a prior registered metadata receipt. Two authored mathematical examples do not establish native sign convention, source locks or generated acceptance.
