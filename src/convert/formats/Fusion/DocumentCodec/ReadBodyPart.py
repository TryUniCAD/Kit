from collections.abc import Callable

from convert.formats.Fusion.BrepCodec.Prism.ReadPrismHist import ReadPrismHist
from convert.formats.Fusion.BrepCodec.Frustum.ReadFrustumHist import ReadFrustumHist
from convert.formats.Fusion.BrepCodec.Journal.JournalModel import JournalModel
from convert.formats.Fusion.BrepCodec.Journal.ReadJournal import ReadJournal
from convert.formats.Fusion.BrepCodec.ReadHistory import ReadHistory
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import (
    DocumentBody,
    KBodyHistory,
)
from convert.formats.Fusion.DocumentCodec.Reading.PickBodyView import PickBodyView


def ReadBodyView(Payload: bytes, Journal: JournalModel) -> KBodyHistory:
    Readers: dict[str, Callable[[bytes], KBodyHistory]] = {
        "frustum": ReadFrustumHist,
        "cylinder": ReadHistory,
        "prism": ReadPrismHist,
    }
    Reader = Readers.get(PickBodyView(Journal))
    if Reader is None:
        return Journal
    try:
        return Reader(Payload)
    except ValueError:
        return Journal


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
    return DocumentBody(Value.Name, ReadBodyView(Value.Payload, Journal))
