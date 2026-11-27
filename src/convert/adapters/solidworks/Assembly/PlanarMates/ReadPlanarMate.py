from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    ReadNodeName,
    ReadRows,
    RequireNode,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarMate import PlanarMate
from convert.adapters.solidworks.Assembly.PlanarMates.ReadDistance import ReadDistance
from convert.adapters.solidworks.Assembly.PlanarMates.ReadEndpoint import ReadEndpoint

# the resolved wrapper contract is grounded in the current archive version
KPlanarVersion = 19000

# concrete ordinary planar descriptors share endpoint ownership while each semantic mode retains its separate guards
KPlanarKinds = {
    "moMateCoincident": "coincident",
    "moMateParallel": "parallel",
    "moMateDistanceDim_c": "distance",
    "moMatePerpendicular": "perpendicular",
}


# exact endpoint identity can be projected once linked archive parsing has supplied the graph
def ReadPlanarMate(
    Context: PlanarContext,
    MateNode: ArchiveNode,
    Version: int,
    *,
    Deferred: bool = False,
) -> PlanarMate:
    if Version != KPlanarVersion:
        raise ValueError("planar mate projection requires archive version 19000")
    _ = RequireNode(Context.ModelNode, "moAssembly_c")
    ClassValue = MateNode.ClassValue
    if not isinstance(ClassValue, RuntimeClass):
        raise ValueError("planar mate projection requires a concrete mate class")
    ClassName = ClassValue.NameValue
    KindValue = KPlanarKinds.get(ClassName)
    Fields = MateNode.FieldsValue
    CodeValue = FieldInt(Fields, "f3b4")
    Records = ReadRows(Fields.get("f410"))
    if KindValue is None or CodeValue not in (0, 1, 2) or len(Records) != 2:
        raise ValueError(
            "mate class alignment or endpoint count lies outside planar projection"
        )
    MateId = FieldInt(Fields, "f08")
    First = ReadEndpoint(Context, Records[0].get("o"), MateId, 0, Deferred=Deferred)
    Second = ReadEndpoint(Context, Records[1].get("o"), MateId, 1, Deferred=Deferred)
    Distance = ReadDistance(MateNode) if KindValue == "distance" else None
    return PlanarMate(
        MateId,
        ReadNodeName(MateNode),
        KindValue,
        ClassName,
        CodeValue,
        (First, Second),
        Distance,
    )
