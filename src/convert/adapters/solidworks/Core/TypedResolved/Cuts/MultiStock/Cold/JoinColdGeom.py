from math import isfinite as IsFinite

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdSolid import (
    ColdSolid,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.Formats.Fusion.Revolves.JoinRevModels import JoinRevModels
from interchange.geometry.Models.BoundingBox import BoundingBox
from interchange.geometry.Models.VectorSpace import SpaceVector
from interchange.Records.RecordTopology import TopologyCounts


# combined analytic geometry must retain both distinct body identities and closed regions
def JoinColdGeom(
    UncutValue: ColdSolid, ResultValue: ColdSolid, BodyIds: frozenset[str]
) -> PartGeometry:
    BrepValue = JoinRevModels((UncutValue.BrepValue, ResultValue.BrepValue))
    Issues = BrepValue.validate(BodyIds)
    if Issues:
        raise ValueError(
            "composed stock solids violate body or topology ownership: "
            + "; ".join(Issues)
        )
    Volume = UncutValue.VolumeValue + ResultValue.VolumeValue
    AreaValue = UncutValue.AreaValue + ResultValue.AreaValue
    if not IsFinite(Volume) or not IsFinite(AreaValue):
        raise ValueError("combined stock measures exceed the supported range")
    FirstBox, SecondBox = UncutValue.BoundsValue, ResultValue.BoundsValue
    Lower = SpaceVector(
        min(FirstBox.minimum.x, SecondBox.minimum.x),
        min(FirstBox.minimum.y, SecondBox.minimum.y),
        min(FirstBox.minimum.z, SecondBox.minimum.z),
    )
    Upper = SpaceVector(
        max(FirstBox.maximum.x, SecondBox.maximum.x),
        max(FirstBox.maximum.y, SecondBox.maximum.y),
        max(FirstBox.maximum.z, SecondBox.maximum.z),
    )
    return PartGeometry(
        BrepValue,
        TopologyCounts(
            solid_count=2,
            shell_count=len(BrepValue.shells),
            face_count=len(BrepValue.faces),
            edge_count=len(BrepValue.edges),
            vertex_count=len(BrepValue.vertices),
            volume=Volume,
            surface_area=AreaValue,
            bounding_box=BoundingBox(Lower, Upper),
            valid=True,
        ),
        {
            "method": "typed_parametric_selected_two_stock_cut",
            "physical_cache": "absent",
        },
    )
