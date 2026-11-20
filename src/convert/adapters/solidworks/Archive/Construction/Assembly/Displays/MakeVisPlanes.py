from convert.adapters.solidworks.Archive.Construction.Assembly.AssemblyState import (
    AssemblyState,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadLogItems import (
    ReadLogItems,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
)


# datum visibility keys use actual plane ownership and the native empty creation log rule
def MakeVisPlanes(
    StateValue: AssemblyState, HeadersValue: tuple[ArchiveNode, ArchiveNode]
) -> tuple[ArchiveNode, ...]:
    Planes = tuple(
        NodeValue
        for NodeValue in StateValue.FeatureValues
        if NodeValue.ClassValue == RuntimeClass("moRefPlane_c", 1)
    )
    if (
        set(StateValue.PlaneValues) != {"x", "y", "z"}
        or len(Planes) != 3
        or set(Planes) != set(StateValue.PlaneValues.values())
    ):
        raise ValueError(
            "assembly visibility requires the three actual principal datum planes"
        )
    UnitValue = RequireNode(
        StateValue.RootValue.FieldsValue["f990"], "moUnitComponent_c"
    )
    Result = []
    for Plane in reversed(Planes):
        IdValue = FieldInt(Plane.FieldsValue, "f08")
        if (
            Plane.FieldsValue["owner"] is not StateValue.RootValue
            or IdValue <= 0
            or FieldInt(Plane.FieldsValue, "f2b0") != 19000
        ):
            raise ValueError("assembly visual datum lacks its actual model owner")
        LogArrays = tuple(
            tuple(
                LogValue
                for LogValue in ReadLogItems(Header.FieldsValue["f20"], "moLogs_c")
                if FieldInt(LogValue.FieldsValue, "f48") == IdValue
            )
            for Header in HeadersValue
        )
        if (
            len(LogArrays[0]) != len(LogArrays[1])
            or len(LogArrays[0]) > 1
            or any(
                ReadLogItems(LogValue, "moStamp_c")
                for Items in LogArrays
                for LogValue in Items
            )
            or (
                LogArrays[0]
                and LogArrays[0][0].FieldsValue["f50"]
                != LogArrays[1][0].FieldsValue["f50"]
            )
        ):
            raise ValueError(
                "assembly visual datum chronology is outside the measured empty-log profile"
            )
        Fields = CompRefFields(UnitValue)
        Fields.update(
            {
                "f58": ArchiveNode(
                    RuntimeClass("moUnitComponent_c", 1), {"owner": None, "has_ext": 0}
                ),
                "ff0": {"f00": IdValue, "f08": DatumTime(HeadersValue[0], IdValue)},
            }
        )
        Result.append(ArchiveNode(RuntimeClass("moCompFeature_c", 1), Fields))
    return tuple(Result)
