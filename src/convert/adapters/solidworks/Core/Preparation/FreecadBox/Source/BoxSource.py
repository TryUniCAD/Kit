from collections.abc import Mapping
from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Archive.Construction.Units.UnitInput import UnitInput
from interchange.document.Models.DocumentModel import CadDocument


# a qualified source projection carries the actual authored values into the shared builder
@DataClass(frozen=True, slots=True)
class BoxSource:
    ModelValue: CadDocument
    PropertiesValue: PartTextInput
    DimensionsValue: tuple[float, float, float]
    CreationEpoch: int
    ParameterBindings: Mapping[str, str]
    SourceBodyName: str
    SourceFeatureName: str
    GeometryValue: Mapping[str, object]
    UnitsValue: UnitInput | None
