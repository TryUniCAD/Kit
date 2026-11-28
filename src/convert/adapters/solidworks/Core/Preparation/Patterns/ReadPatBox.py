from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadBossEnd import (
    ReadBossEnd,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadCircParams import (
    CheckCircDrive,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireExtrusion import (
    RequireExtrude,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    FrontStockBox,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.ReadStockBox import (
    ReadStockBox,
)
from convert.adapters.solidworks.Archive.Construction.ThroughAll.ReadStockRectangle import (
    ReadStockRect,
)
from interchange.Enums.EnumFeatures import BooleanOp
from interchange.Features.FeatureExtrude import ExtrudeEnd
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordParameter import Parameter


# each stock must own its actual sketch and editable forward blind depth
def ReadPatBox(
    StepValue: FeatureStep,
    SketchValue: Sketch,
    SupportId: str,
    DriverValue: Parameter,
    PreviousIds: tuple[str, ...] = (),
) -> FrontStockBox:
    Definition = RequireExtrude(
        StepValue,
        BooleanOp.KJoin if PreviousIds else BooleanOp.KCreate,
        PreviousIds,
        ExpectedSelections=StepValue.selection_ids if PreviousIds else (),
    )
    CheckCircDrive(DriverValue, StepValue.id, "D1")
    if (
        StepValue.parameter_ids != (DriverValue.id,)
        or Definition.length != DriverValue.value
        or Definition.end_condition is not ExtrudeEnd.KBlind
        or Definition.reversed is not False
        or Definition.symmetric is not False
        or SketchValue.support_plane_id != SupportId
        or SketchValue.parameter_ids
    ):
        raise ValueError(
            "stock needs its actual Front rectangle and sole positive forward blind D1"
        )
    Vertices = ReadStockRect(SketchValue, 0.001)
    EndValue = ReadBossEnd(Definition, "z")
    BoundsValue = ReadStockBox(
        ((*Vertices[0], 0.0), (*Vertices[2], EndValue.DepthValue))
    )
    return FrontStockBox(SketchValue.name, StepValue.name, BoundsValue)
