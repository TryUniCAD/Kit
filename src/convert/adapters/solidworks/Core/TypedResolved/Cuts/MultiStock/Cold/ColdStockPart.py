from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Core.TypedResolved.Cuts.MultiStock.Cold.ColdStockOwners import (
    ColdStockOwners,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.PartGeometry import (
    PartGeometry,
)
from interchange.Features.FeatureBody import DesignBody


# reconstructed solids and topology depend on the same linked cold history retained for projection
@DataClass(frozen=True, slots=True)
class ColdStockPart:
    OwnersValue: ColdStockOwners
    GeometryValue: PartGeometry
    BodiesValue: tuple[DesignBody, DesignBody]
