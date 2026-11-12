from typing import cast as CastValue

from convert.formats.Fusion.BrepCodec.EmitHistory import EmitHistory
from convert.formats.Fusion.BrepCodec.Models.BrepHeader import BrepHeader
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Prism.EmitPrismHist import EmitPrismHist
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory
from convert.formats.Fusion.ContainerCodec.Model.ContainerPart import ContainerPart
from convert.formats.Fusion.DocumentCodec.Model.DocumentBody import DocumentBody


def EmitBodyPart(Value: DocumentBody) -> ContainerPart:
    History = Value.History
    if not isinstance(CastValue(object, History), (HistoryModel, PrismHistory)):
        raise ValueError("Unsupported typed Fusion document history")
    if History.Header != BrepHeader(23200, 2, 3, 50.0, 1e-6, 1e-10):
        raise ValueError("Unsupported Fusion document BRep header")
    if isinstance(History, HistoryModel):
        Payload = EmitHistory(
            History.Model,
            History.Identity,
            History.TagSet,
            History.History,
            History.Stamp,
            History.Vertices,
        )
    else:
        Payload = EmitPrismHist(
            History.Model,
            History.Identity,
            History.TagSet,
            History.History,
            History.Stamp,
            History.Frame,
        )
    return ContainerPart(Value.PartName, Payload)
