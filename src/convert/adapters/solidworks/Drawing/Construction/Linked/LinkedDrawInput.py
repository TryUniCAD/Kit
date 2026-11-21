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
    ModelDefInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import (
    DrawDocOptions,
)
from convert.adapters.solidworks.Drawing.Construction.Supports.ViewNames import (
    ViewNames,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData


# linked file construction must receive complete portable intent and explicit support presentation beside the independently generated child
@DataClass(frozen=True, slots=True)
class LinkedDrawInput:
    DrawingValue: DrawingData
    OptionsValue: DrawDocOptions
    UiSettings: ModelDefInput
    HeaderValue: HeaderInput
    FileValue: SelfFileInput
    HistoryValue: HistoryInput
    SupportNames: ViewNames
