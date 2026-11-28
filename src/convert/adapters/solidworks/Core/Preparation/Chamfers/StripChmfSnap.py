from dataclasses import replace as ReplaceValue

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.Adapter import KSourceBytesKey
from convert.adapters.solidworks.Core.Preparation.Chamfers.ChmfSnapMeta import (
    KChmfSnapshot,
)
from interchange.Core.Common import FreezeMapping
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import NativeFeature
from interchange.Features.FeatureStep import FeatureStep


# known replay bytes can be regenerated while each native row retains its identity and archive spans
def StripChmfRow(StepValue: FeatureStep) -> FeatureStep:
    Definition = StepValue.definition
    if type(Definition) is not NativeFeature:
        return StepValue
    FieldsValue = dict(Definition.object_data)
    if type(FieldsValue.get("record_data")) is not bytes:
        raise ValueError(
            "cold chamfer JSON native row lacks its canonical replay bytes"
        )
    del FieldsValue["record_data"]
    return ReplaceValue(
        StepValue,
        definition=ReplaceValue(Definition, object_data=FreezeMapping(FieldsValue)),
    )


# snapshot transport changes only the archive carrier and its redundant native row copies
def StripChmfSnap(Document: CadDocument, Recipe: SelfFileInput) -> CadDocument:
    Metadata = dict(Document.metadata)
    del Metadata[KSourceBytesKey]
    Metadata[KChmfSnapshot] = FreezeMapping(
        {"locator": Recipe.PathName, "written_at": Recipe.SavedAt}
    )
    return ReplaceValue(
        Document,
        metadata=FreezeMapping(Metadata),
        feature_timeline=tuple(
            StripChmfRow(Value) for Value in Document.feature_timeline
        ),
    )
