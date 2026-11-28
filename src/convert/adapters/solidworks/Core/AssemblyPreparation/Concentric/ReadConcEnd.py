from math import isclose as IsClose

from convert.adapters.solidworks.Archive.Construction.Assembly.Bounds.PlacePoint import (
    PlacePoint,
)
from convert.adapters.solidworks.Archive.Construction.Assembly.OccurrenceIn import (
    OccurrenceIn,
)
from convert.adapters.solidworks.Archive.Construction.ConcentricMates.CylFaceBuild import (
    CylFaceBuild,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.RotateVector import (
    RotateVector,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Concentric.CylMateEnd import (
    CylMateEnd,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.Model.AsmRootData import (
    AsmRootData,
)
from interchange.assembly.MateEntity import MateEntity


# a selected cylinder must name the actual neutral side and a direct placed occurrence
def ReadConcEnd(
    Entity: MateEntity,
    Model: AsmRootData,
    Placements: tuple[OccurrenceIn, OccurrenceIn],
    FaceValue: CylFaceBuild,
    FaceId: str,
    RadiusMm: float,
) -> CylMateEnd:
    if (
        Entity.owner_definition_id != Model.RootValue.id
        or str(Entity.kind) != "cylinder"
        or len(Entity.instance_path) != 1
        or Entity.selection_id
        or Entity.frame is not None
        or Entity.provenance is not None
        or Entity.attributes
    ):
        raise ValueError(
            "concentric endpoint requires its actual direct cylinder owner"
        )
    if Entity.source_entity_id != FaceId:
        raise ValueError(
            "concentric endpoint must select the actual neutral lateral face"
        )
    Radius = Entity.radius
    if (
        Radius is None
        or type(Radius) not in (int, float)
        or not IsClose(Radius, RadiusMm, rel_tol=1e-12, abs_tol=1e-12)
    ):
        raise ValueError(
            "concentric endpoint radius differs from its actual child in mm"
        )
    (OwnerId,) = Entity.instance_path
    (IndexValue,) = (
        Index for Index, Value in enumerate(Model.Occurrences) if Value.id == OwnerId
    )
    FrameValue = Placements[IndexValue].FrameValue
    return CylMateEnd(
        Entity,
        Model.Occurrences[IndexValue],
        IndexValue,
        PlacePoint(FrameValue, FaceValue.OriginValue),
        RotateVector(
            (*FrameValue.AxisU, *FrameValue.AxisV, *FrameValue.NormalValue),
            FaceValue.AxisValue,
        ),
    )
