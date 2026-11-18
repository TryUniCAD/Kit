from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Part.Neutral.CheckPlainLinks import (
    CheckPlainLinks,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequireBossDef import (
    RequireBossDef,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.RequirePlainDoc import (
    RequirePlainDoc,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Records.RecordParameter import Parameter


# shared boss admission validates the same model after the separately admitted radial driver is accounted for
def CheckCircBase(DocumentValue: CadDocument, DepthParam: Parameter) -> ExtrudeFeature:
    SketchValue = DocumentValue.sketches[0]
    BossView = ReplaceValue(
        DocumentValue,
        parameters=(DepthParam,),
        sketches=(ReplaceValue(SketchValue, constraints=(), parameter_ids=()),),
    )
    RequirePlainDoc(BossView)
    Definition = RequireBossDef(DocumentValue.feature_timeline[0])
    CheckPlainLinks(BossView, Definition)
    return Definition
