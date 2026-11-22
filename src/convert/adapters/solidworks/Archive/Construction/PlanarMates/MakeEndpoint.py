from convert.adapters.solidworks.Archive.Construction.PlanarMates.CheckMateChild import (
    CheckMateChild,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.CompRefFields import (
    CompRefFields,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.DatumTime import (
    DatumTime,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.EndpointData import (
    EndpointData,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MakeMateChain import (
    MakeMateChain,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.MateSelection import (
    MateSelection,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.PlaceDatum import (
    PlaceDatum,
)
from convert.adapters.solidworks.Archive.Construction.PlanarMates.ReadDatumFrame import (
    ReadDatumFrame,
)
from convert.adapters.solidworks.Archive.Objects.ArchiveNode import ArchiveNode
from convert.adapters.solidworks.Archive.Objects.RuntimeClass import RuntimeClass
from convert.adapters.solidworks.Archive.Views.RequireScalar import RequireScalar
from convert.adapters.solidworks.Assembly.PlanarMates.GraphValue import (
    FieldInt,
    RequireNode,
    RequireRecord,
)


# each selected principal datum produces its own chain and plane reference while inherited occurrence identity stays shared
def MakeEndpoint(Assembly: ArchiveNode, Selection: MateSelection) -> EndpointData:
    ConfigId = CheckMateChild(Selection)
    Chain = MakeMateChain(Assembly, Selection.OccurrenceValue)
    Datum = Selection.DatumValue
    Frame, KindValue = ReadDatumFrame(Datum)
    Geometry = RequireNode(Datum.FieldsValue.get("f6f8"), "moDefaultRefPlnData_c")
    Borders = tuple(
        RequireScalar(Geometry.FieldsValue.get(f"b{Index}")) for Index in range(4)
    )
    if Borders[0] < Borders[1] or Borders[2] < Borders[3]:
        raise ValueError(
            "principal datum display bounds must retain their native order"
        )
    Fields = CompRefFields(Chain)
    DatumId = FieldInt(Datum.FieldsValue, "f08")
    Fields.update(
        {
            "ff0": {
                "f00": DatumId,
                "f08": DatumTime(Selection.ChildValue.HeaderValue, DatumId),
            },
            "ff8": None,
            "f100": KindValue,
        }
    )
    Reference = ArchiveNode(RuntimeClass("moCompRefPlane_c", 1), Fields)
    Placement = RequireRecord(Selection.OccurrenceValue.FieldsValue.get("f360"))
    UpdateValue = FieldInt(Selection.OccurrenceValue.FieldsValue, "f3e0")
    if not 0 <= UpdateValue <= 0xFFFFFFFF:
        raise ValueError("child update must fit native unsigned stamp")
    return EndpointData(
        Reference,
        PlaceDatum(Frame, Placement),
        Placement,
        (Borders[0], Borders[1], Borders[2], Borders[3]),
        ConfigId,
        UpdateValue,
        DatumId,
    )
