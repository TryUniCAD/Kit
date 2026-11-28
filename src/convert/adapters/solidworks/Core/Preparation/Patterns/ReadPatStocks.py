from collections.abc import Mapping

from convert.adapters.solidworks.Archive.Construction.Patterns.Stock.FrontStockBox import (
    FrontStockBox,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.CheckPatPick import (
    CheckPatPick,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.ReadPatBox import ReadPatBox
from interchange.Features.FeatureStep import FeatureStep
from interchange.geometry.Models.Selection import Selection
from interchange.geometry.Models.Sketch import Sketch
from interchange.Records.RecordParameter import Parameter


# the second box must consume only the first box and keep its separate sketch
def ReadPatStocks(
    PlateValue: FeatureStep,
    SeedValue: FeatureStep,
    SupportId: str,
    SketchValues: Mapping[str, Sketch],
    ParamValues: Mapping[str, Parameter],
    PickValues: Mapping[str, Selection],
) -> tuple[FrontStockBox, FrontStockBox]:
    PlateSketch, SeedSketch = PlateValue.sketch_id, SeedValue.sketch_id
    if (
        PlateSketch is None
        or SeedSketch is None
        or {PlateSketch, SeedSketch} != set(SketchValues)
        or len(PlateValue.parameter_ids) != 1
        or len(SeedValue.parameter_ids) != 1
        or len(SeedValue.selection_ids) != 1
    ):
        raise ValueError(
            "plate and seed must own exactly their own rectangle and depth driver"
        )
    CheckPatPick(
        PickValues[SeedValue.selection_ids[0]], "feature", PlateValue.id, "body"
    )
    return (
        ReadPatBox(
            PlateValue,
            SketchValues[PlateSketch],
            SupportId,
            ParamValues[PlateValue.parameter_ids[0]],
        ),
        ReadPatBox(
            SeedValue,
            SketchValues[SeedSketch],
            SupportId,
            ParamValues[SeedValue.parameter_ids[0]],
            (PlateValue.id,),
        ),
    )
