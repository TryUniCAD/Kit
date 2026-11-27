from hashlib import sha256 as Sha256

from convert.adapters.solidworks.Container.Parasolid import DecodeBrep
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.AttachedCylinder import (
    AttachedCylinder,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckSavedRound import (
    CheckSavedRound,
)


# design only projection proves the live dimensions before discarding the geometry
def CheckAttachGeom(DataValue: bytes, ModelValue: NativeModel) -> AttachedCylinder:
    BodyValue = DecodeBrep(DataValue)
    if BodyValue is None:
        raise ValueError("SOLIDWORKS attached circle has no usable active body")
    return AttachedCylinder(
        BodyValue, CheckSavedRound(BodyValue, ModelValue), Sha256(DataValue).hexdigest()
    )
