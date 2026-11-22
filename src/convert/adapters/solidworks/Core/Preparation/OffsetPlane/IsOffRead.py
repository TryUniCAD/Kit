from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.OffsetPlane.OrderOffStreams import (
    KOffStreamOrder,
)
from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureKinds import RefPlaneFeature


# the exact offset stream inventory identifies the same typed source in both read modes
def IsOffRead(DocumentValue: CadDocument) -> bool:
    StreamsValue = DocumentValue.metadata.get("stream_names")
    return (
        DocumentValue.source.format_id == KPartFormatId
        and DocumentValue.source.container_version == "4"
        and DocumentValue.metadata.get(KSourceFormatKey) == KPartFormatId
        and DocumentValue.assembly is None
        and DocumentValue.DrawingValue is None
        and isinstance(StreamsValue, (tuple, list))
        and tuple(CastValue(Sequence[object], StreamsValue)) == KOffStreamOrder
        and sum(
            type(StepValue.definition) is RefPlaneFeature
            for StepValue in DocumentValue.feature_timeline
        )
        == 1
    )
