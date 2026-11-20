from convert.adapters.solidworks.Archive.Construction.BodyNames.AnchorPartInput import (
    AnchorPartInput,
)
from convert.adapters.solidworks.Archive.Construction.BodyNames.CheckAnchorSpec import (
    CheckAnchorSpec,
)
from convert.adapters.solidworks.Archive.Construction.Part.CheckPartInput import (
    CheckPartInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.Equations.PlanWidthDepth import (
    PlanWidthDepth,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartBuildInput import (
    PartBuildInput,
)
from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.RectangleAnchors.MakeAnchorPart import (
    MakeAnchorPart,
)
from interchange.document.Models.DocumentModel import CadDocument


# the derived depth needs a fully admitted neutral intent before constructing any linked stream
def MakeDerivedBoss(
    DocumentValue: CadDocument, InputValue: PartBuildInput, AnchorValue: AnchorPartInput
) -> PartCandidate:
    CheckAnchorSpec(AnchorValue)
    if AnchorValue.KindValue != "corner" or AnchorValue.TopAttached:
        raise ValueError(
            "local equation requires an explicit Front Plane corner anchor"
        )
    PlanValue = PlanWidthDepth(DocumentValue)
    CheckPartInput(DocumentValue, InputValue, PlanValue)
    return MakeAnchorPart(
        InputValue,
        PlanValue,
        AnchorValue,
        WidthDepth=True,
    )
