from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Enums.EnumFeatures import FeatureKind
from interchange.Features.FeatureKinds import NativeFeature


# the measured writer requires the actual producer of the imported solid
def IsImportRead(DocumentValue: CadDocument) -> bool:
    if not IsColdRead(DocumentValue) or len(DocumentValue.bodies) != 1:
        return False
    ProducerId = DocumentValue.bodies[0].final_feature_id
    return any(
        FeatureValue.id == ProducerId
        and FeatureValue.kind is FeatureKind.KImported
        and isinstance(FeatureValue.definition, NativeFeature)
        and FeatureValue.definition.object_data.get("native_class") == "moBaseBody_c"
        for FeatureValue in DocumentValue.feature_timeline
    )
