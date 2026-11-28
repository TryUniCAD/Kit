from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Geometry.ReadRigidXform import (
    ReadRigidXform,
)


# occurrence placements store the forward authored row basis and translation while validating ordinary proper rigid native geometry
def MakePlacement(FrameValue: PlaneFrame) -> dict[str, object]:
    MatrixValue = (*FrameValue.AxisU, *FrameValue.AxisV, *FrameValue.NormalValue)
    HasMatrix = int(MatrixValue != (1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0))
    FieldsValue: dict[str, object] = {
        "has_matrix": HasMatrix,
        "f58": FrameValue.OriginValue[0],
        "f60": FrameValue.OriginValue[1],
        "f68": FrameValue.OriginValue[2],
        "f70": 1.0,
        "f78": 0,
    }
    if HasMatrix:
        FieldsValue["f08"] = {
            f"m{IndexValue}": ItemValue
            for IndexValue, ItemValue in enumerate(MatrixValue)
        }
    _ = ReadRigidXform(FieldsValue)
    return FieldsValue
