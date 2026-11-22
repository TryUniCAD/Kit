from collections.abc import Mapping
from typing import cast as CastValue

from convert.adapters.solidworks.Container.Format import KPartFormatId
from convert.adapters.solidworks.Core.NativeSourceKey import KSourceFormatKey
from interchange.document.Models.DocumentModel import CadDocument
from interchange.Features.FeatureAngleRev import AngularRevolve


# only the projected one sided feature can use the complete regenerated source comparison
def IsRevRead(DocumentValue: CadDocument) -> bool:
    Report = DocumentValue.metadata.get("solidworks.typed_revolve_semantics")
    if not isinstance(Report, Mapping):
        return False
    ReportValue = CastValue(Mapping[str, object], Report)
    Definitions = tuple(
        StepValue.definition
        for StepValue in DocumentValue.feature_timeline
        if isinstance(StepValue.definition, AngularRevolve)
    )
    return (
        DocumentValue.assembly is None
        and DocumentValue.DrawingValue is None
        and DocumentValue.source.format_id == KPartFormatId
        and DocumentValue.source.container_version == "4"
        and DocumentValue.metadata.get(KSourceFormatKey) == KPartFormatId
        and ReportValue.get("status") == "projected"
        and ReportValue.get("typed_geometry_projection") is True
        and len(Definitions) == 1
        and Definitions[0].SideMode == "one_sided"
    )
