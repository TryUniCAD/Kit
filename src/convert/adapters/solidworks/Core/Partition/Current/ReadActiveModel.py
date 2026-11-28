from convert.Geometry.Parasolid import BuildPartModel, ParaHeaderData, SolidFaceData
from convert.adapters.solidworks.Archive.Partition.Current.ReadVertexTable import ReadVertexTable
from convert.adapters.solidworks.Container.Parasolid import DecodeBrep
from interchange.brep.Topology.BrepModel import BrepModel


# successful general decoding stays authoritative while proven current fin shadows can recover a missing model
def ReadActiveModel(DataValue: bytes) -> BrepModel | None:
    ModelValue = DecodeBrep(DataValue)
    if ModelValue is not None:
        return ModelValue
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
