from convert.adapters.solidworks.Archive.Construction.Geometry.PlaneFrame import (
    PlaneFrame,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Direction.ReadPatFrame import (
    ReadPatPoint,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode


# principal lines use the sized display origin within the actual canonical datum
def ReadPrincDir(
    PlaneValue: ArchiveNode, DataValue: ArchiveNode
) -> tuple[PlaneFrame, int]:
    FrameValue, RoleValue = ReadDatumFrame(PlaneValue)
    Fields = DataValue.FieldsValue
    Display = ReadPatPoint(Fields.get("display_root"))
    if (
        RoleValue not in (1, 2)
        or FrameValue != PrincipalFrame("x" if RoleValue == 1 else "y")
        or Display[RoleValue - 1] != 0.0
        or tuple(Fields.get(KeyValue) for KeyValue in ("f54", "f58", "f5c"))
        != (-4, -4, 1)
        or any(
            Fields.get(KeyValue) is not None
            for KeyValue in ("f48", "f68", "f70", "f78")
        )
    ):
        raise ValueError("pattern direction requires an ordinary Top or Right datum")
    return (
        PlaneFrame(Display, FrameValue.AxisU, FrameValue.AxisV, FrameValue.NormalValue),
        RoleValue,
    )
