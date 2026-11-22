from convert.adapters.solidworks.Container.Parasolid import DecodeBrep
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckSavedRound import (
    CheckSavedRound,
)


# design only projection proves the live dimensions before discarding the geometry
def CheckAttachGeom(DataValue: bytes, ModelValue: NativeModel) -> None:
    BodyValue = DecodeBrep(DataValue)
    if BodyValue is None:
        raise ValueError("SOLIDWORKS attached circle has no usable active body")
    _ = CheckSavedRound(BodyValue, ModelValue)
