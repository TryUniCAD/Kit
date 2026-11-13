from dataclasses import dataclass as MakeDataClass

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Model.DwgClassRow import DwgClassRow


@MakeDataClass(frozen=True, slots=True)
class DraftStandard:
    ClassRows: tuple[DwgClassRow, ...]
    HeaderVars: DraftRecord
    FixedHandles: tuple[tuple[str, int], ...]
    SlotItems: tuple[tuple[str, tuple[KDraftValue, ...]], ...]
    DraftRows: tuple[DraftRow, ...]
