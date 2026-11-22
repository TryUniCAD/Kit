from interchange.Core.Common import FreezeMapping
from interchange.Enums.EnumGeometry import GeometryKind
from interchange.geometry.Models.GeometryCurves import PointGeometry
from interchange.geometry.Models.Sketch import SketchEntity
from interchange.geometry.Models.VectorPlane import PlaneVector

from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.LineOrigin import (
    LineOrigin,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.OriginMetadata import (
    OriginMetadata,
)
from convert.adapters.solidworks.Core.TypedResolved.LineDimensions.Origin.OriginPointId import (
    OriginPointId,
)
from convert.adapters.solidworks.Core.TypedResolved.TypedProvenance import (
    TypedProvenance,
)


# an external model origin is a fixed construction datum rather than another contour vertex or a duplicate endpoint
def OriginEntity(ProfileId: int, OriginValue: LineOrigin) -> SketchEntity:
    NativeId = f"{ProfileId}:points:{OriginValue.ExternalIndex}"
    PointOwner = {
        **OriginValue.OwnerValue,
        "embedded_array": "points",
        "row_index": OriginValue.ExternalIndex,
        "embedded_class": "sgPoint",
    }
    return SketchEntity(
        id=OriginPointId(ProfileId, OriginValue),
        kind=GeometryKind.KPoint,
        geometry=PointGeometry(
            PlaneVector(*(1000.0 * Value for Value in OriginValue.PositionValue))
        ),
        construction=True,
        fixed=True,
        provenance=TypedProvenance(PointOwner, NativeId),
        attributes=FreezeMapping(
            {**OriginMetadata(OriginValue), "typed_archive_owner": PointOwner}
        ),
    )
