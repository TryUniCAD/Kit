from convert.adapters.Fusion.Native.Circular.Snapshots.SnapFaces import BodyFaces
from convert.Formats.Fusion.BrepCodec.Journal.Geometry.BodyNode import BodyNode
from convert.Formats.Fusion.BrepCodec.Journal.Snapshot.GeometryState import (
    GeometryState,
)


# body roles must follow independent shell topology rather than assumed root positions
def ReadSnapRoles(State: GeometryState) -> tuple[tuple[int, str], ...]:
    Result: list[tuple[int, str]] = []
    for Identity, Entity in enumerate(State.Entities):
        if not isinstance(Entity, BodyNode):
            continue
        if Entity.Prefix.Attribute != -1 or Entity.Prefix.EntityTag != -1:
            raise ValueError("Dual snapshot body has unsupported saved metadata")
        Faces = BodyFaces(State, Entity)
        if len(Faces) in (3, 4) and not any(
            FaceValue.DoubleSided for FaceValue in Faces
        ):
            RoleName = "solid"
        elif len(Faces) == 1:
            RoleName = "profile" if Faces[0].DoubleSided else "sketch"
        else:
            raise ValueError("Dual snapshot has an unsupported body topology")
        Result.append((Identity, RoleName))
    if len(Result) != 3 or {RoleName for _, RoleName in Result} != {
        "solid",
        "profile",
        "sketch",
    }:
        raise ValueError(
            "Dual snapshot requires distinct solid profile and sketch bodies"
        )
    return tuple(Result)
