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
from convert.adapters.solidworks.Drawing.Construction.Portable.BlankDrawInput import (
    BlankDrawInput,
)
from convert.adapters.solidworks.Drawing.Construction.Portable.DrawDocOptions import (
    DrawDocOptions,
)
from interchange.document.Models.Drawing.DrawingData import DrawingData


# one generated document must preserve consistent authored provenance across its model header and independent history stream
def CheckBlankInput(InputValue: BlankDrawInput) -> None:
    if type(InputValue) is not BlankDrawInput or (
        type(InputValue.DrawingValue) is not DrawingData
        or type(InputValue.OptionsValue) is not DrawDocOptions
        or type(InputValue.UiSettings) is not ModelDefInput
        or type(InputValue.HeaderValue) is not HeaderInput
        or type(InputValue.FileValue) is not SelfFileInput
        or type(InputValue.HistoryValue) is not HistoryInput
    ):
        raise TypeError(
            "blank drawing file construction requires complete typed neutral intent and provenance"
        )
    if (
        InputValue.OptionsValue.CreatedAt != InputValue.HeaderValue.CreatedAt
        or InputValue.HeaderValue.CreatedAt != InputValue.HistoryValue.CreatedAt
        or InputValue.HeaderValue.CommentText != InputValue.HistoryValue.CommentText
        or InputValue.UiSettings.VersionValue
        != InputValue.OptionsValue.TargetValue.FileVersion
    ):
        raise ValueError("blank drawing model header and history provenance disagree")
