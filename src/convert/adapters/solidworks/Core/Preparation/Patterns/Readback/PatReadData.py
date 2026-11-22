from convert.adapters.solidworks.Core.Preparation.Readback.IsColdRead import IsColdRead
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import LinearPattern


# only the typed linear pattern writes through the dedicated preparation and evidence lane
def IsPatWrite(Document: CadDocument) -> bool:
    return any(
        type(Value.definition) is LinearPattern for Value in Document.feature_timeline
    )


# round trips use a verified cold projection while fresh authored models keep their own name
def PatDocName(Document: CadDocument) -> str:
    if IsColdRead(Document):
        Details = NativeRecord(Document.metadata.get("solidworks.typed_linear_pattern"))
        if Details.get("status") != "projected_cold_single_direction":
            raise ValueError("unsupported saved linear pattern source")
        NameValue = Details.get("part_name")
    else:
        NameValue = Document.metadata.get("name")
    if type(NameValue) is not str or not NameValue:
        raise ValueError("linear pattern requires its actual part name")
    return NameValue
