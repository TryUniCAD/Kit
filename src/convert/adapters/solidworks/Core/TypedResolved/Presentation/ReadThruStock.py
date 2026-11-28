from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.CheckDimGraph import (
    CheckDimGraph,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.ReadLineDims import (
    ReadLineDims,
)
from convert.adapters.solidworks.Core.TypedResolved.Lines.LineLoop import LineLoop
from convert.adapters.solidworks.Core.TypedResolved.Lines.ReadLineLoop import (
    ReadLineLoop,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative


# presentation admission must retain the complete rectangular contour and its actual unary relation owners
def ReadThruStock(ProfileValue: ArchiveNode, LinkValue: NativeLink) -> LineLoop:
    if (
        ProfileValue.FieldsValue.get("f3dc") != 0
        or ProfileValue.FieldsValue.get("pd_f110") is not None
    ):
        raise ValueError(
            "through-all presentation stock has shared or spatial geometry"
        )
    SketchValue = RequireNative(ProfileValue.FieldsValue.get("pd_f80"), "sgSketch")
    DimsValue = ReadLineDims(SketchValue, LinkValue)
    if DimsValue.DriverValues or DimsValue.OriginValue is not None:
        raise ValueError("through-all presentation stock has unmeasured sketch drivers")
    LoopValue = ReadLineLoop(SketchValue, LinkValue, DimsValue)
    CheckDimGraph(LoopValue, DimsValue)
    CheckTreeAlias(
        LinkValue,
        (SketchValue, *(Value.HandleValue for Value in DimsValue.AxisValues)),
    )
    return LoopValue
