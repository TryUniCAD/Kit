from collections.abc import Callable

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import (
    CheckPlainLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.MakeBlindPlan import (
    MakeBlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadLength import (
    ReadLength,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import (
    RequireBossDef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    RequirePlainDoc,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Sketch import Sketch


# rectangle and polygon admission must share neutral parameter support configuration and body ownership checks
def ProjectBlind(
    DocumentValue: CadDocument,
    ReadSketch: Callable[[Sketch, float], tuple[tuple[float, float], ...]],
    DepthName: str = "D1",
    *,
    AxisValue: str = "z",
    IsReversed: bool = False,
) -> BlindPlan:
    RequirePlainDoc(DocumentValue)
    Definition = RequireBossDef(
        DocumentValue.feature_timeline[0], AxisValue, IsReversed
    )
    CheckPlainLinks(DocumentValue, Definition, DepthName, AxisValue)
    ScaleValue = {"mm": 0.001, "m": 1.0, "in": 0.0254}.get(DocumentValue.units)
    if ScaleValue is None:
        raise ValueError(
            "plain boss document units are outside the supported dimensional profile"
        )
    return MakeBlindPlan(
        DocumentValue,
        ReadSketch(DocumentValue.sketches[0], ScaleValue),
        DocumentValue.parameters[0].id,
        ReadLength(Definition.length),
        DepthName,
        AxisValue=AxisValue,
        IsReversed=IsReversed,
    )
