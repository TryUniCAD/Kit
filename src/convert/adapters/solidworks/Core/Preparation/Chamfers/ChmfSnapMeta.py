from convert.adapters.solidworks.Archive.Construction.Files.SelfFileInput import (
    SelfFileInput,
)
from convert.adapters.solidworks.Core.Preparation.RequirePartPath import RequirePartPath
from convert.adapters.solidworks.Core.TypedResolved.NativeRecord import NativeRecord
from interchange.document.Models.DocumentModel import CadDocument

# the snapshot names the modeled archive path and save event needed to recompile its full semantics
KChmfSnapshot = "solidworks_cold_chamfer_source"


# snapshot fields nominate a recipe that still requires complete regeneration and ownership checks
def ReadChmfSnap(Document: CadDocument) -> SelfFileInput:
    Fields = NativeRecord(Document.metadata.get(KChmfSnapshot))
    PathValue, Epoch = Fields.get("locator"), Fields.get("written_at")
    if (
        set(Fields) != {"locator", "written_at"}
        or type(PathValue) is not str
        or type(Epoch) is not int
    ):
        raise ValueError("cold chamfer JSON recipe lacks its actual locator or epoch")
    return RequirePartPath(PathValue, Epoch)
