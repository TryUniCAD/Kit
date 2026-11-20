from convert.adapters.base.ReadOptions import ReadOptions
from convert.adapters.base.WritePolicy import GetFormatKey
from convert.Formats.CheckPartText import CheckPartText
from interchange.document.Models.DocumentModel import CadDocument
from interchange.document.Models.DocumentWalk import WalkDocuments

# serialized neutral snapshots can retain explicit inspection status from a prior source
KNeutralJson = "interchange.json"


# unavailable text in any owned child must block a new projection of the assembly
def CheckSourceText(
    DocumentValue: CadDocument,
    ReaderFormat: str | None,
    WriterFormat: str,
    ReaderOpts: ReadOptions | None,
) -> None:
    if (
        ReaderFormat is not None
        and GetFormatKey(ReaderFormat) == GetFormatKey(WriterFormat) == KNeutralJson
        and (
            ReaderOpts is None
            or (
                ReaderOpts.include_brep
                and ReaderOpts.include_tessellation
                and ReaderOpts.configuration is None
            )
        )
    ):
        return
    for PartValue in WalkDocuments(DocumentValue):
        CheckPartText(PartValue)
