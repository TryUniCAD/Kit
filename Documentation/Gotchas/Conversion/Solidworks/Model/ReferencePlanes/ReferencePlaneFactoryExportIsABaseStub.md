# The generic reference-plane factory export returns null

The exported factory name suggests that `moConstraintRefplaneFactory::createRefPlane` is the active authored-plane construction route. On the pinned 2026 model DLL, its export resolves to a folded function at `0x4b27cbe0` whose body returns zero. Other unrelated exports share the same body.

Use the concrete factory or public API path and verify its selected geometry and publication steps. The API module imports distinct distance and angle geometry constructors; the constrained-plane data then owns a separate three-reference interface and the computed plane. An exported name alone does not establish that the application executes that factory. [Exact binary identity and scope](../../../../../../re/solidworks/records/ReferencePlaneConstruction2026.md)
