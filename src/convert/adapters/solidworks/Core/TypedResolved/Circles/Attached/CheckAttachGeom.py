from hashlib import sha256 as HashDigest

from convert.adapters.solidworks.Container.Parasolid import DecodeBrep
from convert.adapters.solidworks.Core.Native import NativeModel
from convert.adapters.solidworks.Core.TypedResolved.Circles.Attached.AttachedRound import (
    AttachedRound,
)
from convert.adapters.solidworks.Core.TypedResolved.Geometry.Circles.CheckSavedRound import (
    CheckSavedRound,
)


# design only projection proves the live dimensions before discarding the geometry
def CheckAttachGeom(DataValue: bytes, ModelValue: NativeModel) -> AttachedRound:
    BodyValue = DecodeBrep(DataValue)
    if BodyValue is None:
        raise ValueError("SOLIDWORKS attached circle has no usable active body")
    return AttachedRound(
        BodyValue,
        CheckSavedRound(BodyValue, ModelValue),
        HashDigest(DataValue).hexdigest(),
    )
