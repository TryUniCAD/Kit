from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    DatumPoint,
)
from convert.adapters.solidworks.Archive.Construction.Datums.MakeHingePick import (
    MakeHingePick,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.AxisCross import (
    AxisCross,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.AxisStations import (
    AxisStations,
)
from convert.adapters.solidworks.Archive.Construction.Datums.PrincipalAxes.PrincipalAxis import (
    PrincipalAxis,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.AtomSeeds import (
    KAtomLists,
    KAtomWords,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.InitFeatureMut import (
    InitFeatureMut,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Construction.System.PrincipalFrame import (
    PrincipalFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass


# directed endpoint components away from the selected axis use the modeled positive zero
def AxisPoint(Station: float, Direction: KDatumVector) -> dict[str, float]:
    AxisX, AxisY, AxisZ = Direction
    return DatumPoint(
        (
            Station * AxisX if AxisX else 0.0,
            Station * AxisY if AxisY else 0.0,
            Station * AxisZ if AxisZ else 0.0,
        )
    )


# each generated axis is a distinct feature and two independently constructed plane references
def MakePosAxisMut(
    SystemValue: PartSystem,
    InputValue: PartBuildInput,
    Allocator: PersistentIds,
    Headers: tuple[ArchiveNode, ArchiveNode],
    AxisValue: PrincipalAxis,
    Supports: tuple[str, str],
) -> ArchiveNode:
    First, Second = Supports
    FirstFrame = PrincipalFrame(First)
    Direction = AxisCross(FirstFrame.NormalValue, PrincipalFrame(Second).NormalValue)
    if Direction != AxisValue.DirectionValue:
        raise ValueError(
            "principal plane supports disagree with the authored signed axis"
        )
    Planes = SystemValue.SystemValues.PlaneValues
    Start, EndValue = AxisStations(Planes[First], FirstFrame, Direction)
    StartPoint = AxisPoint(Start, Direction)
    Feature = ArchiveNode(RuntimeClass("moRefAxis_c", 1), {})
    InitFeatureMut(
        Feature,
        AxisValue.NameValue,
        SystemValue.RootValue,
        InputValue.TargetValue,
        Allocator,
    )
    Feature.FieldsValue.update(dict.fromkeys(KAtomWords, 0))
    Feature.FieldsValue.update({KeyValue: [] for KeyValue in KAtomLists})
    Feature.FieldsValue.update(
        f35c=0,
        f368={"n": 0, "items": []},
        f388={"n": 0, "items": []},
        f538=None,
        f4a0=1,
        f6c0=StartPoint,
        f6dc=4,
        f6e0=0,
        f6e8=None,
        f6f0=0,
    )
    Feature.FieldsValue["f700"] = ArchiveNode(
        RuntimeClass("moPlaneInterAxisData_c", 1),
        {
            "f18": StartPoint,
            "f30": AxisPoint(EndValue, Direction),
            "f08": -Start,
            "f10": EndValue,
            "f50": DatumPoint(Direction),
            "f68": DatumPoint(AxisValue.OriginValue),
            "f80": MakeHingePick(
                SystemValue, Planes[First], First, Headers, AllowFrontIdentity=True
            ),
            "f88": MakeHingePick(
                SystemValue, Planes[Second], Second, Headers, AllowFrontIdentity=True
            ),
        },
    )
    return Feature
