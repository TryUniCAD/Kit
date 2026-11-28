from convert.adapters.solidworks.Archive.Construction.Datums.Angles.DatumVector import (
    KDatumVector,
    KHingeAxis,
    KHingeRoot,
)
from convert.adapters.solidworks.Archive.Construction.Nodes.PersistentIds import (
    PersistentIds,
)
from convert.adapters.solidworks.Archive.Construction.Part.MakePartHeaders import (
    MakePartHeaders,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.System.PartSystem import (
    PartSystem,
)
from convert.adapters.solidworks.Archive.Header.WriteHeaderGraph import WriteHeadGraph
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.ReadPlane import ReadVector


# the constrained angle can attach only to both real ordered local plane supports of its hinge
def CheckHingePick(
    ModelValue: ArchiveNode,
    WrapValue: object,
    PlaneValue: ArchiveNode,
    Headers: tuple[ArchiveNode, ...],
) -> ArchiveNode:
    Wrapper = RequireNode(WrapValue, "moPlaneRef_w").FieldsValue
    Reference = RequireNode(Wrapper.get("f58"), "moCompRefPlane_c").FieldsValue
    Component = RequireNode(Reference.get("f58"), "moUnitComponent_c")
    TargetId = FieldInt(PlaneValue.FieldsValue, "f08")
    Identity = RequireRecord(Reference.get("ff0"))
    if (
        Wrapper.get("f60") is not None
        or Wrapper.get("f68") != 1
        or (Wrapper.get("has_f10"), Wrapper.get("has_f18")) != (0, 0)
        or Component is ModelValue.FieldsValue.get("f990")
        or Component.FieldsValue.get("owner") is not ModelValue
        or Component.FieldsValue.get("has_ext") != 0
        or Reference.get("ff8") is not None
        or Identity.get("f00") != TargetId
        or any(
            Identity.get("f08") != DatumTime(Header, TargetId) for Header in Headers[:2]
        )
    ):
        raise ValueError(
            "angular datum requires ordered registered Top and Right hinge supports"
        )
    return Component


# matching the live allocator and two header roles prevents building on detached hinge state
def CheckHingeStamp(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
    HingeValue: ArchiveNode,
    Headers: tuple[ArchiveNode, ...],
) -> None:
    if (
        len(SystemValue.ConfigValues) != 1
        or SystemValue.ManagerValue.FieldsValue.get("f360")
        is not SystemValue.ConfigValues[0]
    ):
        raise ValueError(
            "angular datum requires the actual ordinary generated part and active configuration"
        )
    Fields = RequireNode(HingeValue, "moRefAxis_c").FieldsValue
    NativeId = FieldInt(Fields, "f08")
    if (
        Fields.get("owner") is not SystemValue.RootValue
        or Allocator.Allocations.get((HingeValue, "f08")) != NativeId
    ):
        raise ValueError(
            "angular datum requires its actual registered hinge from the same model"
        )
    if (
        len(Headers) != 3
        or any(
            Value.FieldsValue.get("f08") != Allocator.NextValue for Value in Headers[:2]
        )
        or SystemValue.ConfigValues[0].FieldsValue.get("f85c")
        != Allocator.NextValue - 1
    ):
        raise ValueError(
            "angular datum allocation must extend the hinge's current header and configuration"
        )
    Fresh = MakePartHeaders(SystemValue, Settings, Allocator)
    if tuple(WriteHeadGraph(Value, 19000) for Value in Headers[:2]) != tuple(
        WriteHeadGraph(Value, 19000) for Value in Fresh[:2]
    ):
        raise ValueError(
            "angular datum requires the actual fresh hinge headers and their original provenance"
        )


# the stored finite interval must remain the one currently derived from the first principal display
def CheckAngleHinge(
    SystemValue: PartSystem,
    Settings: PartBuildInput,
    Allocator: PersistentIds,
    HingeValue: ArchiveNode,
    Headers: tuple[ArchiveNode, ...],
) -> tuple[tuple[KDatumVector, KDatumVector], ArchiveNode]:
    CheckHingeStamp(SystemValue, Settings, Allocator, HingeValue, Headers)
    AxisFields = RequireNode(
        HingeValue.FieldsValue.get("f700"), "moPlaneInterAxisData_c"
    ).FieldsValue
    Planes = SystemValue.SystemValues.PlaneValues
    TopValue, RightValue = Planes["y"], Planes["x"]
    FirstPick = CheckHingePick(
        SystemValue.RootValue, AxisFields.get("f80"), TopValue, Headers
    )
    SecondPick = CheckHingePick(
        SystemValue.RootValue, AxisFields.get("f88"), RightValue, Headers
    )
    if (
        FirstPick is SecondPick
        or not all(
            Value in SystemValue.FeatureValues for Value in (TopValue, RightValue)
        )
        or (ReadNodeName(TopValue), ReadNodeName(RightValue))
        != ("Top Plane", "Right Plane")
    ):
        raise ValueError(
            "angular datum requires ordered registered Top and Right hinge supports"
        )
    TopData = RequireNode(
        TopValue.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c"
    ).FieldsValue
    CenterZ = ReadVector(TopData.get("display_root"))[2]
    Start, Finish = ReadVector(AxisFields.get("f18")), ReadVector(AxisFields.get("f30"))
    if (
        ReadVector(AxisFields.get("f50")) != KHingeAxis
        or ReadVector(AxisFields.get("f68")) != KHingeRoot
        or Start != (0.0, 0.0, CenterZ - RequireScalar(TopData.get("b3")))
        or Finish != (0.0, 0.0, CenterZ - RequireScalar(TopData.get("b2")))
        or (AxisFields.get("f08"), AxisFields.get("f10")) != (Start[2], -Finish[2])
    ):
        raise ValueError(
            "angular datum requires the actual directed finite clipping of the hinge"
        )
    return (Start, Finish), RightValue
