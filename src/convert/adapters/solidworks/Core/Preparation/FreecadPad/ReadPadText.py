from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.MakeFcDocText import (
    MakeFcDocText,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxRelease import (
    ReadBoxRelease,
)
from convert.adapters.solidworks.Core.Preparation.FreecadBox.Source.ReadBoxText import (
    ReadDocProps,
)
from convert.adapters.solidworks.Core.Preparation.FreecadPad.CheckPadOwners import (
    CheckPadOwners,
)
from convert.adapters.solidworks.Core.Preparation.FreecadPad.ReadPadDoc import (
    ReadPadDoc,
)
from interchange.document.Models.DocumentModel import CadDocument


# the shared literal property recipe keeps authored title comment and source identity by their document scope
def ReadPadText(Document: CadDocument) -> PartTextInput:
    Release = ReadBoxRelease(Document.source.application_version)
    Metadata = ReadPadDoc(Document)
    CheckPadOwners(Document, Metadata)
    Properties = ReadDocProps(Document.source, Metadata, Release)
    Summary, Fields, _ = MakeFcDocText(Document.source, Properties, {})
    return PartTextInput(Summary, Fields, {})
