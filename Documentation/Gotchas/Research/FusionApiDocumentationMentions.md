# API documentation can describe another declaration's availability

## Observation

The installed Fusion API documentation can mention a retired item while describing its current replacement.
`Occurrence.transform2` documents replacing the retired `transform` property.
`CustomGraphicsBillBoard.create` describes a retired argument.
`cam.Operations.compatibleStrategies` mentions preview strategies.

A whole-document substring search therefore cannot classify the owning declaration as retired, deprecated or preview.

## Workaround

Store those matches as explicit documentation-mention markers.
Keep actual availability unverified until evidence identifies the owning item's status.
The [catalogue guide](../../Reference/Research/FusionPlannerCatalog.md) describes this distinction.
The process integration case verifies that `Occurrence.transform2` retains unverified availability.
