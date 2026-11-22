from convert.adapters.solidworks.Archive.Construction.Geometry.CrossVector import (
    CrossVector,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)


# the selected plane constructor reforms its second tangent before storing the ordered transform
def OffBaseFrame(AxisValue: str) -> PlaneFrame:
    BaseValue = PrincipalFrame(AxisValue)
    AxisU = BaseValue.AxisU
    AxisV = CrossVector(BaseValue.NormalValue, AxisU)
    return PlaneFrame(BaseValue.OriginValue, AxisU, AxisV, CrossVector(AxisU, AxisV))
