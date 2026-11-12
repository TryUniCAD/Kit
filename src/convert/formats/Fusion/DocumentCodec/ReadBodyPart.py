from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody
from convert.formats.Fusion.DocumentCodec.Reading.PickBodyView import PickBodyView


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
    Journal = ReadJournal(Value.Payload)
    Profile = PickBodyView(Journal)
    if Profile == "frustum":
        return DocumentBody(Value.Name, ReadFrustumHist(Value.Payload))
    if Profile == "cylinder":
        return DocumentBody(Value.Name, ReadHistory(Value.Payload))
    if Profile == "prism":
        return DocumentBody(Value.Name, ReadPrismHist(Value.Payload))
    return DocumentBody(Value.Name, Journal)
