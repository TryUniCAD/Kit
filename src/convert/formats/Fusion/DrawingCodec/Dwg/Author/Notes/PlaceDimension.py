from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftBook import DraftBook
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftLinks import (
    HardPointer,
    SoftPointer,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftRow import DraftEed
from convert.formats.Fusion.DrawingCodec.Dwg.Author.DraftValue import (
    DraftRecord,
    KDraftValue,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Notes.DimensionPlan import (
    KExtentRatio,
    KTextHeight,
    DimensionPlan,
    PlanDimension,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.PlaceMut import (
    AppendMut,
    PlaceMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.PlaceBlock import (
    OwnMut,
    PlaceBlockMut,
)
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Sheet.SheetKeys import KPaperSpace
from convert.formats.Fusion.DrawingCodec.Dwg.Author.Spec.DimensionDraft import (
    DimensionDraft,
)

KStyleKey = "DIMSTYLE:Dim-ISO-25"
KDimLayer = "LAYER:FD_Dimensions"
KPointLayer = "LAYER:Defpoints"
KByBlock = 8192
KLineWeight = 30
KJagGroups = (("1070", 387), ("1070", 0), ("1070", 389), ("1010", (0.0, 0.0, 0.0)))
KDraftFields = dict[str, KDraftValue]


def FactorItem(NameText: str, Value: float) -> DraftEed:
    return DraftEed(HardPointer("APPID:" + NameText), DraftRecord((("1040", Value),)))


def FactorEed(Factor: float) -> tuple[DraftEed, ...]:
    Style = (
        ("1000", "DSTYLE"),
        ("1002", 0),
        ("1070", 144),
        ("1040", Factor),
        ("1002", 1),
    )
    return (
        DraftEed(HardPointer("APPID:ACAD"), DraftRecord(Style)),
        FactorItem("ACAD_DIMASSOC_CALC_DIMLFAC", Factor),
        FactorItem("ACAD_DIMASSOC_DIMLFAC", Factor),
        FactorItem("ACAD_DIMASSOC_OVERRIDDEN_DIMLFAC", 0.0),
        DraftEed(
            HardPointer("APPID:ACAD_DSTYLE_DIMJAG_POSITION"), DraftRecord(KJagGroups)
        ),
    )


def BlockCommon(BlockKey: str, Layer: str) -> KDraftFields:
    return {
        "EntityMode": 0,
        "Owner": SoftPointer(BlockKey),
        "ColorIndex": KByBlock,
        "LtypeScale": 1.0,
        "LtypeFlags": 0,
        "Layer": HardPointer(Layer),
    }


def PlaceLinesMut(Ledger: DraftBook, BlockKey: str, Planned: DimensionPlan) -> None:
    for Index, (Start, Finish) in enumerate(Planned.Lines):
        KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Line{Index}")
        Common = {**BlockCommon(BlockKey, KDimLayer), "LineWeight": KLineWeight}
        Points = {
            "StartX": Start[0],
            "EndX": Finish[0],
            "StartY": Start[1],
            "EndY": Finish[1],
        }
        Plane = {"ZeroDepth": 1, "UnitExtrusion": 1, "Thickness": 0.0}
        _ = PlaceMut(Ledger, KeyText, "LINE", Common, {**Points, **Plane})
    for Index, (Corner, Second, Apical) in enumerate(Planned.Arrows):
        KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Arrow{Index}")
        Corners = {
            "CornerOne": Corner,
            "CornerTwo": Second,
            "CornerThree": Apical,
            "CornerFour": Apical,
        }
        _ = PlaceMut(
            Ledger, KeyText, "SOLID", BlockCommon(BlockKey, KDimLayer), Corners
        )


def PlaceTextMut(Ledger: DraftBook, BlockKey: str, Planned: DimensionPlan) -> None:
    KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Text")
    Point = (*Planned.TextPoint, 0.0)
    Width = Planned.TextWidth
    _ = PlaceMut(
        Ledger,
        KeyText,
        "MTEXT",
        BlockCommon(BlockKey, KDimLayer),
        {
            "Insertion": Point,
            "XAxis": (1.0, 0.0, 0.0),
            "ExtentHeight": KTextHeight * KExtentRatio,
            "ExtentWidth": Width,
            "TextValue": Planned.TextValue,
            "ContextXAxis": (1.0, 0.0, 0.0),
            "ContextInsertion": Point,
            "ContextExtWidth": Width,
            "ContextExtHeight": KTextHeight * KExtentRatio,
        },
    )


def PlacePointsMut(Ledger: DraftBook, BlockKey: str, Planned: DimensionPlan) -> None:
    for Index, Point in enumerate(
        (Planned.FirstPoint, Planned.SecondPoint, Planned.LinePoint)
    ):
        KeyText = OwnMut(Ledger, BlockKey, f"{BlockKey}/Point{Index}")
        Place = {"PointX": Point[0], "PointY": Point[1], "PointZ": 0.0}
        _ = PlaceMut(
            Ledger, KeyText, "POINT", BlockCommon(BlockKey, KPointLayer), Place
        )


def PlaceDimMut(Ledger: DraftBook, Index: int, Draft: DimensionDraft) -> str:
    Planned = PlanDimension(Draft)
    BlockKey = PlaceBlockMut(Ledger, f"BLOCK_HEADER:Dimension{Index}", "*D")
    PlaceLinesMut(Ledger, BlockKey, Planned)
    PlaceTextMut(Ledger, BlockKey, Planned)
    PlacePointsMut(Ledger, BlockKey, Planned)
    KeyText = OwnMut(Ledger, KPaperSpace, f"{KPaperSpace}/Dimension{Index}")
    _ = PlaceMut(
        Ledger,
        KeyText,
        "DIMENSION_LINEAR",
        {"ReactorCount": 0, "Reactors": ()},
        {
            "TextMidpoint": Planned.TextPoint,
            "Measurement": Planned.Measurement,
            "PointThirteen": (*Planned.FirstPoint, 0.0),
            "PointFourteen": (*Planned.SecondPoint, 0.0),
            "PointTen": (*Planned.LinePoint, 0.0),
            "DimRotation": 0.0,
            "DimBlock": HardPointer(BlockKey),
        },
        FactorEed(Planned.LinearFactor),
    )
    AppendMut(Ledger, KStyleKey + ".Reactors", SoftPointer(KeyText))
    return KeyText
