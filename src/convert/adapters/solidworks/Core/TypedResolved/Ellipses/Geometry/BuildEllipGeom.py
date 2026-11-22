from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.EllipPartRead import (
    EllipPartRead,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.Geometry.BuildEllipShell import (
    BuildEllipShell,
)
from convert.adapters.solidworks.Core.TypedResolved.Ellipses.Geometry.EllipMeasures import (
    EllipMeasures,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeSpan import NativeNodeSpan


# geometry derives only from the exact same supported conic and depth that the semantic reader publishes
def BuildEllipGeom(PartValue: EllipPartRead, BodyId: str) -> PartGeometry:
    DepthOwner = PartValue.BossValue.RequireDepth()
    HeightMm = RequireScalar(DepthOwner.DepthValue.native_value) * 1000.0
    Model = BuildEllipShell(PartValue.GeometryValue, HeightMm, BodyId)
    return PartGeometry(
        Model,
        EllipMeasures(PartValue.GeometryValue, HeightMm, Model),
        {
            "method": "typed_parametric_full_ellipse",
            "feature_owner": NativeNodeSpan(
                PartValue.LinkValue, PartValue.BossValue.NodeValue
            ),
            "sketch_owner": NativeNodeSpan(PartValue.LinkValue, PartValue.SketchValue),
            "depth_owner": NativeNodeSpan(PartValue.LinkValue, DepthOwner.Dimension),
            "native_kernel_identity": False,
        },
    )
