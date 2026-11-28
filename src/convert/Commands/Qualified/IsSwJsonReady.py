from convert.adapters.json.Metadata import KInfoValue as KJsonInfo
from convert.adapters.solidworks.Core.Preparation.Sweeps.PrepSweepPart import (
    PrepSweepPart,
)
from convert.adapters.solidworks.Core.Preparation.Sweeps.SwReadInput import (
    IsSwReadback,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.SweepFeature import SweepFeature


# neutral json can preserve the complete canonical sweep after checking its derived shape and original archive identity
def IsSwJsonReady(Document: CadDocument, Target: str) -> bool:
    if (
        Target != KJsonInfo.FormatId
        or not IsSwReadback(Document)
        or len(Document.feature_timeline) != 1
        or type(Document.feature_timeline[0].definition) is not SweepFeature
    ):
        return False
    Locator = Document.source.attributes.get("native_locator")
    EpochValue = Document.source.attributes.get("written_at")
    if type(Locator) is not str or type(EpochValue) is not int:
        raise ValueError(
            "neutral sweep transfer requires its canonical source identity"
        )
    _ = PrepSweepPart(Document, Locator, EpochValue)
    return True
