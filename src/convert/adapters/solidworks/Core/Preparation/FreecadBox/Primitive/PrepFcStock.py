from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.MakeOriginBoxPart import (
    MakeOriginBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.BuildPlacedBox import (
    BuildPlacedBox,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Primitive.PlanFcStock import (
    PlanFcStock,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.geometry.Models.Transform import KTransformIdentity


# isolated primitive stock can be constructed before any downstream boolean history is represented
def PrepFcStock(
    Document: CadDocument,
    FeatureId: str,
    PathValue: str,
    CreationTime: int,
    *,
    Placed: bool = False,
) -> PartCandidate:
    PlanValue = PlanFcStock(
        Document, FeatureId, PureWindowsPath(PathValue).stem, Placed=Placed
    )
    if PlanValue.support_planes[0].transform != KTransformIdentity:
        return BuildPlacedBox(PlanValue, PathValue, CreationTime)
    return MakeOriginBox(PlanValue, PathValue, CreationTime, PartTextInput({}, {}, {}))
