from convert.Geometry.Parasolid import BuildPartModel, ParaHeaderData, SolidFaceData
from convert.adapters.solidworks.Archive.Partition.Current.ReadVertexTable import (
    ReadVertexTable,
)
from interchange.brep.Topology.BrepModel import BrepModel


# proven fin shadow recovery retains its original model and failure boundaries
def ReadShadowModel(DataValue: bytes) -> BrepModel | None:
    try:
        Tables = ReadVertexTable(DataValue)
        HeaderValue = ParaHeaderData(DataValue)
        if Tables is None or HeaderValue is None:
            return None
        BodyData = DataValue[HeaderValue.body_offset :]
        ModelValue = BuildPartModel(Tables, *SolidFaceData(BodyData))
    except (KeyError, ValueError, OverflowError):
        return None
    return ModelValue if not ModelValue.validate() else None
