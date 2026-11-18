from dataclasses import dataclass as DataClass

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Header.HeaderInput import (
    HeaderInput,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.HistoryInput import (
    HistoryInput,
)
from convert.adapters.solidworks.Archive.Definition.Construction.ModelDefSettings import (
    ModelDefSettings,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import (
    DrawDocOptions,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData


# complete blank output needs genuine drawing intent and explicit presentation file identity and truthful provenance together
@DataClass(frozen=True, slots=True)
class BlankDrawInput:
    DrawingValue: DrawingData
    OptionsValue: DrawDocOptions
    UiSettings: ModelDefSettings
    HeaderValue: HeaderInput
    FileValue: SelfFileInput
    HistoryValue: HistoryInput
