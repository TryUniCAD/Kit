from pathlib import Path as FilePath
from typing import cast as CastValue

from convert import write_document as WriteDocument
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import (
    MakePartProps,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt, SldprtArchive
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)


# public geometry construction and shared property generation provide independently authored complete native reader inputs
def MakeTextPart(TargetPath: FilePath, IsProperties: bool = True) -> FilePath:
    RequestValue = MakePolygonCase(
        TargetPath.stem, ((-13.0, -5.0), (24.0, -2.0), (8.0, 19.0)), False
    )
    Document = CastValue(CadDocument, FromData(RequestValue["document"]))
    _ = WriteDocument(
        Document,
        TargetPath,
        allow_carrier=False,
        values={"require_native_transfers": True},
    )
    if IsProperties:
        InputsValue = PartTextInput(
            {
                "title": "Fixture <α>",
                "author": "Reader control",
                "comments": "Authored comment",
            },
            {
                "SharedName": "Document & α",
                "SecondText": "Literal text",
                "SpacedText": "  retained  ",
            },
            {"SharedName": "Configuration <β>"},
        )
        StreamsValue = SldprtArchive.OpenAction(TargetPath).streams
        _ = TargetPath.write_bytes(
            BuildSldprt({**StreamsValue, **MakePartProps(InputsValue)}, FormatVersion=4)
        )
    return TargetPath
