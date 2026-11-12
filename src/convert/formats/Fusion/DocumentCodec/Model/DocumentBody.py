from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Frustum.Models.FrustumHistory import (
    FrustumHistory,
)
from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel
from convert.formats.Fusion.BrepCodec.Prism.Models.PrismHistory import PrismHistory


@MakeDataClass(frozen=True, slots=True)
class DocumentBody:
    PartName: str
    History: HistoryModel | PrismHistory | FrustumHistory
