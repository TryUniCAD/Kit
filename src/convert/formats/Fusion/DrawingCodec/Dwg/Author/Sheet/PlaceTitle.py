from collections.abc import Mapping

from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardOwner,
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftRow
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import KDraftValue
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import OwnMut
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import (
    KBorderBlock,
    KPaperSpace,
    KTitleBlock,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetSizes import (
    PaperSize,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.TitleText import TitleText

KWidthDefault = 0x10
KDefinitionOnly = ("DefVersion", "Prompt")
KTitleInsert = KPaperSpace + "/Title"
KBorderInsert = KPaperSpace + "/Border"
KPoint = tuple[float, float]


def PlaceInsertMut(
    Ledger: DraftBook,
    KeyText: str,
    BlockKey: str,
    Corner: KPoint,
    ClassData: Mapping[str, KDraftValue],
) -> None:
    Layer = "LAYER:BORDER" if BlockKey == KBorderBlock else "LAYER:TITLEBLOCK"
    _ = PlaceMut(
        Ledger,
        KeyText,
        "INSERT",
        {
            "ReactorCount": 0,
            "LtypeScale": 1.0,
            "Reactors": (),
            "Layer": HardPointer(Layer),
        },
        {
            "Insertion": (*Corner, 0.0),
            "BlockHeader": HardPointer(BlockKey),
            **ClassData,
        },
    )
    AppendMut(Ledger, BlockKey + ".Inserts", SoftPointer(KeyText))
    _ = OwnMut(Ledger, KPaperSpace, KeyText)


def PlanarPoint(Value: KDraftValue) -> KPoint:
    if not isinstance(Value, tuple) or len(Value) != 2:
        raise ValueError("Authored DWG title attribute has no planar position")
    Across, Upward = Value
    if not isinstance(Across, float) or not isinstance(Upward, float):
        raise ValueError("Authored DWG title attribute position is not numeric")
    return (Across, Upward)


def Shifted(Value: KDraftValue, Corner: KPoint) -> KPoint:
    Across, Upward = PlanarPoint(Value)
    return (Across + Corner[0], Upward + Corner[1])


def AttribData(
    Definition: DraftRow, Chosen: TitleText, Corner: KPoint
) -> dict[str, KDraftValue]:
    Fields = dict(Definition.ClassData.DraftFields)
    for NameText in KDefinitionOnly:
        _ = Fields.pop(NameText)
    Alignment = Shifted(Fields["Alignment"], Corner)
    IsAligned = "HorizAlign" in Fields
    Fields["Alignment"] = Alignment
    Fields["Insertion"] = (
        Alignment if IsAligned else Shifted(Fields["Insertion"], Corner)
    )
    Fields["TextValue"] = Chosen.TextValue
    Flags = Fields["DataFlags"]
    if Chosen.WidthFactor != 1.0 and isinstance(Flags, int):
        Fields["DataFlags"] = Flags & ~KWidthDefault
        Fields["WidthFactor"] = Chosen.WidthFactor
    return Fields


def TagOf(Definition: DraftRow) -> str:
    return str(dict(Definition.ClassData.DraftFields)["Tag"])


def PlaceTitleMut(
    Ledger: DraftBook, Paper: PaperSize, Texts: tuple[TitleText, ...]
) -> None:
    PlaceInsertMut(Ledger, KBorderInsert, KBorderBlock, (0.0, 0.0), {"HasAttribs": 0})
    Definitions = [
        Entry
        for Entry in Ledger.DraftRows
        if Entry.ClassName == "ATTDEF" and Entry.KeyText.startswith(KTitleBlock + "/")
    ]
    Chosen = {Title.Tag: Title for Title in Texts}
    Unknown = set(Chosen) - {TagOf(Entry) for Entry in Definitions}
    if Unknown:
        raise ValueError(
            f"Authored DWG title block has no attributes {sorted(Unknown)}"
        )
    Attribs = tuple(
        f"{KTitleInsert}/Attrib{Index}" for Index in range(len(Definitions))
    )
    TitleData: dict[str, KDraftValue] = {
        "HasAttribs": 1,
        "OwnedCount": len(Attribs),
        "Attribs": tuple(HardOwner(KeyText) for KeyText in Attribs),
        "SeqEnd": HardOwner(KTitleInsert + "/SeqEnd"),
    }
    PlaceInsertMut(Ledger, KTitleInsert, KTitleBlock, Paper.TitleCorner, TitleData)
    Owner = {"Owner": SoftPointer(KTitleInsert)}
    for KeyText, Entry in zip(Attribs, Definitions):
        Title = Chosen.get(TagOf(Entry), TitleText(TagOf(Entry), ""))
        _ = PlaceMut(
            Ledger,
            KeyText,
            "ATTRIB",
            Owner,
            AttribData(Entry, Title, Paper.TitleCorner),
        )
    _ = PlaceMut(
        Ledger, KTitleInsert + "/SeqEnd", "SEQEND", {**Owner, "ShadowFlags": 3}, {}
    )
