from collections.abc import Mapping

from convert.Geometry.Parasolid import DecodeBrepModel, DecodePartData
from convert.adapters.solidworks.Archive.Partition.CheckXmtGraph import CheckXmtGraph
from convert.adapters.solidworks.Archive.Partition.ReadActiveNodes import (
    ReadActiveNodes,
)
from convert.adapters.solidworks.Archive.Partition.XmtNode import XmtNode
from convert.adapters.solidworks.Container.Container import SldprtArchive
from interchange.brep.Topology.BrepModel import BrepModel


# active topology and attribute ownership must come from the same selected partition payload
def ReadStockData(
    Archive: SldprtArchive, StreamName: str
) -> tuple[Mapping[int, XmtNode], BrepModel]:
    StreamValue = Archive.require(StreamName)
    Payloads = DecodePartData(StreamValue, StreamName)
    if tuple(Payload.kind for Payload in Payloads) != ("partition", "deltas") or any(
        Payload.schema != "SCH_3701250_37102_13006" for Payload in Payloads
    ):
        raise ValueError("saved stock cache has alternate partition framing")
    ActiveValue, DeltaValue = Payloads
    if (
        ActiveValue.wrapper_offset
        or DeltaValue.wrapper_offset != ActiveValue.stored_size
        or DeltaValue.wrapper_offset + DeltaValue.stored_size != len(StreamValue)
    ):
        raise ValueError("saved stock cache has unowned partition envelope bytes")
    Active = ActiveValue.data
    NodesValue = ReadActiveNodes(Active)
    CheckXmtGraph(NodesValue)
    ModelValue = DecodeBrepModel(Active)
    if ModelValue is None:
        raise ValueError("saved stock cache has no decoded active geometry")
    return NodesValue, ModelValue
