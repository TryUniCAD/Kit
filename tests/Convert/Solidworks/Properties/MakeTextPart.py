from pathlib import Path as FilePath
from typing import cast as CastValue

from convert.adapters.solidworks.Archive.Construction.Part.PartCandidate import (
    PartCandidate,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.MakePartProps import (
    MakePartProps,
)
from convert.adapters.solidworks.Archive.Construction.Metadata.Properties.PartTextInput import (
    PartTextInput,
)
from convert.adapters.solidworks.Container.Container import BuildSldprt
from convert.adapters.solidworks.Core.Preparation.PrepareNative import PrepareNative
from interchange.document.Models.DocumentModel import CadDocument
from interchange.serialization.Deserialize import FromData
from tests.Convert.Solidworks.Research.Construction.Part.MakePolygonCase import (
    MakePolygonCase,
)

# default fixture requests omit empty xml scopes until a test adds them explicitly
KNoEmptyScopes: frozenset[str] = frozenset()


# a fixed authored event makes the reader control independent of wall clock publication
KTextPartEpoch = 1794000100


# complete reader controls use model preparation because their local candidate has no native measurement
def MakeTextPart(
    TargetPath: FilePath,
    IsProperties: bool = True,
    *,
    EmptyScopes: frozenset[str] = KNoEmptyScopes,
    HasEmptyFileOwner: bool = False,
) -> FilePath:
    RequestValue = MakePolygonCase(
        TargetPath.stem, ((-13.0, -5.0), (24.0, -2.0), (8.0, 19.0)), False
    )
    Document = CastValue(CadDocument, FromData(RequestValue["document"]))
    Candidate = PrepareNative(Document, TargetPath, KTextPartEpoch)
    assert isinstance(Candidate, PartCandidate)
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
    else:
        InputsValue = PartTextInput({}, {}, {}, EmptyScopes, HasEmptyFileOwner)
    PropertiesValue = MakePartProps(InputsValue)
    OutputValue = (
        BuildSldprt({**Candidate.StreamsValue, **PropertiesValue}, FormatVersion=4)
        if PropertiesValue
        else Candidate.BytesValue
    )
    with TargetPath.open("xb") as FixtureFile:
        _ = FixtureFile.write(OutputValue)
    return TargetPath
