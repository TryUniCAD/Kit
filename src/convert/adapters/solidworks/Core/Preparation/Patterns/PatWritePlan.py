from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.LinPatternInput import (
    LinPatternInput,
)
from convert.adapters.solidworks.Archive.Construction.Patterns.Input.PatPresentInput import (
    PatPresentInput,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.PlanLinPattern import (
    PlanLinPattern,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.ColdPatInput import (
    ColdPatInput,
)
from convert.adapters.solidworks.Core.Preparation.Patterns.Readback.PatReadData import (
    IsPatRead,
    PatDocName,
)
from interchange.document.Models.DocumentModel import CadDocument


# selection and emission plan through the same typed ordinary pattern owners
def PatWritePlan(
    Document: CadDocument,
    Target: SelfFileInput,
    Presentation: PatPresentInput | None = None,
) -> LinPatternInput:
    if IsPatRead(Document):
        Neutral, Original = ColdPatInput(Document, PatDocName(Document))
        if Presentation is not None and Presentation != Original:
            raise ValueError("cannot replace a cold pattern's authored presentation")
        return PlanLinPattern(Neutral, Target, Original)
    return PlanLinPattern(Document, Target, Presentation)
