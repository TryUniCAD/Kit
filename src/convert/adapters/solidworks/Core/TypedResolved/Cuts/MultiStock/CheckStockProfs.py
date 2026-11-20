from collections.abc import Mapping

from convert.adapters.solidworks.Core.Native import (
    NativeFeature,
    NativeModel,
    NativeSketch,
)
from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.StockCutLineage import (
    StockCutLineage,
)
from convert.adapters.solidworks.Core.TypedResolved.NativeLink import NativeLink
from convert.adapters.solidworks.Core.TypedResolved.NativeNodeId import NativeNodeId
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from convert.adapters.solidworks.Core.TypedResolved.Presentation.CheckTreeAlias import (
    CheckTreeAlias,
)
from convert.adapters.solidworks.Core.TypedResolved.Presentation.ReadThruStock import (
    ReadThruStock,
)
from convert.adapters.solidworks.Core.TypedResolved.RequireNative import RequireNative
from interchange.geometry.Models.Transform import Transform
from interchange.geometry.Models.VectorSpace import SpaceVector


# supported saved profiles must use their actual datums and retain every scoped driver
def CheckStockProfs(
    Model: NativeModel,
    LinkValue: NativeLink,
    Lineage: StockCutLineage,
    Features: Mapping[int, NativeFeature],
    LinesValue: Mapping[int, NativeSketch],
    CirclesValue: Mapping[int, NativeSketch],
) -> None:
    StockIds = tuple(NativeNodeId(Owner.ProfileValue) for Owner in Lineage.StockValues)
    CutId = NativeNodeId(Lineage.CutValue.ProfileValue)
    if set(LinesValue) != set(StockIds) or set(CirclesValue) != {CutId}:
        raise ValueError(
            "selected two stock timeline lacks its complete typed profiles"
        )
    Planes = {Value.object_id: Value for Value in Model.planes}
    for OwnerValue, FrameValue in zip(
        (*Lineage.StockValues, Lineage.CutValue), Lineage.ProfileFrames, strict=True
    ):
        Profile = OwnerValue.ProfileValue
        NativeId = NativeNodeId(Profile)
        Reference = RequireNative(Profile.FieldsValue.get("pd_f78"), "moCompRefPlane_c")
        SketchNode = RequireNative(Profile.FieldsValue.get("pd_f80"), "sgSketch")
        Component = RequireNative(Reference.FieldsValue.get("f58"), "moUnitComponent_c")
        CheckTreeAlias(LinkValue, (Reference, SketchNode, Component))
        SupportId = NativeRecord(Reference.FieldsValue.get("ff0")).get("f00")
        Depths = Features[NativeNodeId(OwnerValue.NodeValue)].dimensions
        if NativeId == CutId:
            Sketch = CirclesValue[NativeId]
            if Sketch.TypedCircle is None or Depths:
                raise ValueError(
                    "selected through cut requires a free circle and no depth"
                )
        else:
            Sketch = LinesValue[NativeId]
            if (
                Sketch.TypedLines != ReadThruStock(Profile, LinkValue)
                or Depths != (OwnerValue.RequireDepth().DepthValue,)
                or Depths[0].name != "D1"
            ):
                raise ValueError(
                    "independent stock lacks its rectangular loop or D1 owner"
                )
        PlaneValue = Planes.get(Sketch.support_plane_id)
        if (
            Sketch.support_plane_id != SupportId
            or Sketch.dimensions
            or PlaneValue is None
            or not PlaneValue.principal
            or Transform(
                SpaceVector(*PlaneValue.origin_mm),
                SpaceVector(*PlaneValue.u_axis),
                SpaceVector(*PlaneValue.v_axis),
                SpaceVector(*PlaneValue.normal),
            )
            != FrameValue
        ):
            raise ValueError(
                "selected two stock profile has alternate support or dimensions"
            )
