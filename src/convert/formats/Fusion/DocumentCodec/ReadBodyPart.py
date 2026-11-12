from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.Topology.AsmEdge.AsmTable import ReadAsmTable
from convert.formats.Fusion.Topology.AsmEdge.AsmFields import ReadAsmNum


def ReadBodyPart(Value: ContainerPart) -> DocumentBody:
    if not Value.Name.startswith("Breps.BlobParts/BREP.") or not Value.Name.endswith(
        ".smbh"
    ):
        raise ValueError("Unsupported Fusion document part")
    if (
        type(Value.Payload) is not bytes
        or not 0 < len(Value.Payload) <= 2 * 1024 * 1024
    ):
        raise ValueError("Invalid or oversized Fusion document history")
    Table = ReadAsmTable(Value.Payload)
    if Table.RootCount != 2:
        raise ValueError("Unsupported Fusion document history body count")
    if len(Table.Records) == 35:
        Surfaces = tuple(
            Record for Record in Table.Records if Record.Name == "cone-surface"
        )
        if len(Surfaces) != 1:
            raise ValueError("Unsupported Fusion rotational history surface inventory")
        if ReadAsmNum(Surfaces[0], 9) != 0:
            return DocumentBody(Value.Name, ReadFrustumHist(Value.Payload))
        return DocumentBody(Value.Name, ReadHistory(Value.Payload))
    if len(Table.Records) == 102:
        return DocumentBody(Value.Name, ReadPrismHist(Value.Payload))
    raise ValueError("Unsupported Fusion document history topology profile")


from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
