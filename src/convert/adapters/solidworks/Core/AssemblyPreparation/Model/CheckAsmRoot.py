from typing import cast as CastValue

from convert.adapters.solidworks.Core.AssemblyPreparation.AsmWriteCaps import (
    KAsmWriteCaps,
)
from convert.adapters.solidworks.Core.AssemblyPreparation.RequireAsm import RequireAsm
from interchange.document.Models.DocumentModel import CadDocument


# unsupported root domains must reject instead of becoming an apparently complete partial assembly output
def CheckAsmRoot(Document: CadDocument) -> None:
    RequireAsm(
        type(CastValue(object, Document)) is CadDocument
        and str(Document.units) == "mm",
        "assembly requires an actual millimetre neutral document",
    )
    Document.assert_valid()
    RequireAsm(
        not any(
            (
                Document.sketches,
                Document.selections,
                Document.feature_timeline,
                Document.bodies,
                Document.meshes,
                Document.brep_payloads,
                Document.diagnostics,
                Document.materials,
            )
        ),
        "assembly root contains unprojected model content",
    )
    RequireAsm(
        Document.brep is None
        and Document.DrawingValue is None
        and Document.schema_version == "1.0",
        "assembly root contains an unsupported document domain",
    )
    RequireAsm(
        not Document.source.attributes and Document.capabilities <= KAsmWriteCaps,
        "assembly has unsupported source extensions or capabilities",
    )
    RequireAsm(
        set(Document.metadata) == {"name"}
        and isinstance(Document.metadata["name"], str),
        "assembly metadata has an unprojected field",
    )
