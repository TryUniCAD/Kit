from pathlib import PureWindowsPath

from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Archive.Construction.Styles.ReadStyleText import (
    ReadStyleText,
)
from interchange.document.Models.DocumentModel import CadDocument


# the archive path and creation event must come from the actual modeled target identity
def ReadPatTarget(DocumentValue: CadDocument, TargetValue: SelfFileInput) -> str:
    if type(TargetValue) is not SelfFileInput:
        raise ValueError("expected a typed neutral part with explicit target identity")
    NameValue = ReadStyleText(DocumentValue.metadata["name"], "neutral part name")
    PathValue = PureWindowsPath(TargetValue.PathName)
    if (
        not PathValue.is_absolute()
        or str(PathValue) != TargetValue.PathName
        or PathValue.drive != "C:"
        or PathValue.name != NameValue + ".SLDPRT"
        or ".." in PathValue.parts
        or not 0 < TargetValue.SavedAt < 0x7FFFFFFF
    ):
        raise ValueError("target needs the exact authored native basename and event")
    return NameValue
