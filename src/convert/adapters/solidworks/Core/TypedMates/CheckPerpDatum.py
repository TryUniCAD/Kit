from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarContext import PlanarContext
from convert.adapters.solidworks.Assembly.PlanarMates.PlanarEndpoint import (
    PlanarEndpoint,
)


# actual datum creation and canonical kind must agree before a saved perpendicular reference can identify its child plane
def CheckPerpDatum(
    Endpoint: PlanarEndpoint, Wrapper: ArchiveNode, Context: PlanarContext
) -> None:
    Definition = Context.DefinitionMap[Endpoint.ChildDefinitionId]
    ChildValue = Context.ChildMap[
        (
            PureWindowsPath(Definition.source_path).name.casefold(),
            Endpoint.ChildConfigId,
        )
    ]
    Datum = ChildValue.DatumNodes[Endpoint.DatumFeatureId]
    _, KindValue = ReadDatumFrame(Datum)
    Plane = RequireNode(Wrapper.FieldsValue.get("f58"), "moCompRefPlane_c")
    if FieldInt(Plane.FieldsValue, "f100") != KindValue or FieldInt(
        RequireRecord(Plane.FieldsValue.get("ff0")), "f08"
    ) != DatumTime(ChildValue.HeaderNode, Endpoint.DatumFeatureId):
        raise ValueError(
            "perpendicular child datum creation epoch or principal kind differs"
        )
