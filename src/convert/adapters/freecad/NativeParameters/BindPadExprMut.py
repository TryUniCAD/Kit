from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from convert.adapters.freecad.NativeParameters.LinkPadLength import LinkPadLength
from convert.adapters.freecad.NativeParameters.ReadPadExpr import ReadPadExpr
from interchange.Features.FeatureStep import FeatureStep
from interchange.Records.RecordParameter import Parameter
from interchange.geometry.Models.Sketch import Sketch

if TYPE_CHECKING:
    from convert.adapters.freecad.Native import NativeObject


# native reads and exact replay must observe the same owned parameter links before digesting the graph
def BindPadExprMut(
    Objects: Sequence[NativeObject],
    Features: Sequence[FeatureStep],
    Sketches: Sequence[Sketch],
    Parameters: list[Parameter],
) -> None:
    if not Sketches or not Features:
        return
    SketchById = {Value.id: Value for Value in Sketches}
    ParamById = {Value.id: Value for Value in Parameters}
    OffsetById = {Value.id: Index for Index, Value in enumerate(Parameters)}
    for Native, Feature in zip(Objects, Features, strict=True):
        Evidence = ReadPadExpr(Native)
        SketchValue = SketchById.get(Feature.sketch_id or "")
        if Evidence is None or SketchValue is None or SketchValue.suppressed:
            continue
        ProfileName, Source = Evidence
        for ParamId in Feature.parameter_ids:
            LengthValue = ParamById[ParamId]
            if (
                LengthValue.owner_id == Feature.id
                and LengthValue.attributes.get("freecad_path") == "Length"
                and LengthValue.attributes.get("freecad_property_type")
                == "App::PropertyLength"
            ):
                Parameters[OffsetById[ParamId]] = LinkPadLength(
                    LengthValue, SketchValue, ProfileName, Source, ParamById
                )
