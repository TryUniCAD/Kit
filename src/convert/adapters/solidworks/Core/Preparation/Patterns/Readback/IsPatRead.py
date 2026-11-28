from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from convert.adapters.solidworks.Core.TypedResolved.Patterns.PatEvidence import (
    KPatColdState,
    KPatReadKey,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import LinearPattern


# candidate selection identifies only the typed cache free history before complete verification
def IsPatRead(DocumentValue: CadDocument) -> bool:
    StateValue = DocumentValue.metadata.get(KPatReadKey)
    return (
        DocumentValue.source.format_id == KPartFormatId
        and DocumentValue.source.container_version == "4"
        and DocumentValue.metadata.get(KSourceFormatKey) == KPartFormatId
        and DocumentValue.assembly is None
        and DocumentValue.DrawingValue is None
        and isinstance(StateValue, Mapping)
        and CastValue(Mapping[str, object], StateValue).get("status") == KPatColdState
        and sum(
            type(StepValue.definition) is LinearPattern
            for StepValue in DocumentValue.feature_timeline
        )
        == 1
    )
