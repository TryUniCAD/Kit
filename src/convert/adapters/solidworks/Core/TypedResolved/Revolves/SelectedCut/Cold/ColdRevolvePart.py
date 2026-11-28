from dataclasses import dataclass as Dataclass

from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from convert.adapters.solidworks.Core.TypedResolved.Revolves.SelectedCut.Cold.ColdRevolveOwners import (
    ColdRevOwners,
)
from interchange.Features.FeatureBody import DesignBody


# reconstructed geometry and both body owners must carry the same validated selection into the public result
@Dataclass(frozen=True, slots=True)
class ColdRevolvePart:
    OwnersValue: ColdRevOwners
    GeometryValue: PartGeometry
    BodiesValue: tuple[DesignBody, DesignBody]
