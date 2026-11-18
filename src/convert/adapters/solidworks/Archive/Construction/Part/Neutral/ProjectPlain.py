from convert.adapters.solidworks.Archive.Construction.Part.Neutral.BlindPlan import (
    BlindPlan,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ProjectBlind import (
    ProjectBlind,
)
from convert.adapters.solidworks.Archive.Construction.Part.Neutral.ReadRectSketch import (
    ReadRectSketch,
)
from interchange.document.Models.DocumentModel import CadDocument


# existing part and linked document construction must retain its rectangle admission boundary
def ProjectPlain(DocumentValue: CadDocument) -> BlindPlan:
    return ProjectBlind(DocumentValue, ReadRectSketch)
