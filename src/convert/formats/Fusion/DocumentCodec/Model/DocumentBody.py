from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.BrepCodec.Models.HistoryModel import HistoryModel


@MakeDataClass(frozen=True, slots=True)
class DocumentBody:
    PartName: str
    History: HistoryModel
