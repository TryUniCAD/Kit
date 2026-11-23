from collections.abc import Sequence
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.TypedResolved.Geometry.IsCacheAbsent import (
    KPrismStreams,
)
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureExtrude import ExtrudeFeature
from interchange.Features.FeatureKinds import NativeFeature, ShellFeature
from interchange.Features.FeatureStep import FeatureStep


# only the fresh native projection supplies this archive construction input
def CheckShellRead(DocumentValue: CadDocument) -> None:
    Streams = DocumentValue.metadata.get("stream_names")
    if (
        DocumentValue.source.format_id != KPartFormatId
        or DocumentValue.source.container_version != "4"
        or DocumentValue.brep_payloads
        or not isinstance(Streams, (tuple, list))
        or not CastValue(Sequence[object], Streams)
        or not KPrismStreams.issuperset(CastValue(Sequence[object], Streams))
    ):
        raise ValueError("SOLIDWORKS shell compilation requires its cache-free source")


# the stock sketch carrier and shell must retain their actual chronological owners
def ReadShellHist(
    DocumentValue: CadDocument, SketchId: str
) -> tuple[FeatureStep, FeatureStep]:
    History = DocumentValue.feature_timeline
    StockValue, ShellValue = (
        StepValue
        for StepValue in History
        if type(StepValue.definition) is not NativeFeature
    )
    CarrierIds = tuple(
        StepValue.id
        for StepValue in History
        if type(StepValue.definition) is NativeFeature
        and StepValue.sketch_id == SketchId
    )
    if (
        type(StockValue.definition) is not ExtrudeFeature
        or type(ShellValue.definition) is not ShellFeature
        or StockValue.sketch_id != SketchId
        or len(CarrierIds) != 1
        or StockValue.input_feature_ids != CarrierIds
        or ShellValue.input_feature_ids != (StockValue.id,)
    ):
        raise ValueError("SOLIDWORKS shell compilation lacks its linked stock history")
    return StockValue, ShellValue
