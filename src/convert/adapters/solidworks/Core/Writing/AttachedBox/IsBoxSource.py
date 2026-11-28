from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import NativeFeature


# only a legacy freecad primitive can ask for this independently verified source projection
def IsBoxSource(DocumentValue: CadDocument) -> bool:
    if (
        DocumentValue.source.format_id != "freecad.fcstd"
        or not DocumentValue.source.application_version.startswith("0.21R")
        or DocumentValue.assembly is not None
        or len(DocumentValue.feature_timeline) != 1
    ):
        return False
    Definition = DocumentValue.feature_timeline[0].definition
    return (
        isinstance(Definition, NativeFeature)
        and Definition.format_id == "freecad.fcstd"
        and Definition.type_id == "PartDesign::AdditiveBox"
    )
